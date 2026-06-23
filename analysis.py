"""
analysis.py
-----------
Meteorologinių duomenų analizės ir vizualizacijos funkcijos.

Apima:
- Metinės temperatūros ir drėgmės statistiką
- Dienos / nakties temperatūras
- Savaitgalių lietaus prognozę
- Istorinių ir prognozuotų duomenų sujungimą ir grafiką
- Temperatūros Series persmeplavimą į 5 minučių dažnį
"""

from __future__ import annotations

import logging

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 2a) Metiniai vidurkiai
# ---------------------------------------------------------------------------


def compute_annual_averages(df: pd.DataFrame) -> dict[str, float]:
    """Apskaičiuoja vidutinę metų temperatūrą ir oro drėgmę.

    Parameters
    ----------
    df : pd.DataFrame
        Istorinių stebėjimų DataFrame (indeksas – laikas LT laiko zonoje).

    Returns
    -------
    dict
        Žodynas su raktais "avg_temperature" ir "avg_relative_humidity".
    """
    temp_col = _find_column(df, ["airTemperature", "temperature", "temp"])
    hum_col = _find_column(df, ["relativeHumidity", "humidity"])

    result: dict[str, float] = {}
    if temp_col:
        result["avg_temperature"] = round(df[temp_col].mean(), 2)
    if hum_col:
        result["avg_relative_humidity"] = round(df[hum_col].mean(), 2)

    logger.info("Metiniai vidurkiai: %s", result)
    return result


# ---------------------------------------------------------------------------
# 2b) Dienos ir nakties temperatūros
# ---------------------------------------------------------------------------

_DAY_START = 8   # 08:00
_DAY_END = 20    # 20:00 (neimtinai)


def compute_day_night_temperatures(df: pd.DataFrame) -> dict[str, float]:
    """Apskaičiuoja vidutinę dienos (08–20) ir nakties temperatūrą LT laiko zonoje.

    Parameters
    ----------
    df : pd.DataFrame
        Istorinių stebėjimų DataFrame.

    Returns
    -------
    dict
        Žodynas su raktais "avg_day_temperature" ir "avg_night_temperature".
    """
    temp_col = _find_column(df, ["airTemperature", "temperature", "temp"])
    if temp_col is None:
        logger.warning("Temperatūros stulpelis nerastas.")
        return {}

    hours = df.index.hour
    day_mask = (hours >= _DAY_START) & (hours < _DAY_END)

    result = {
        "avg_day_temperature": round(df.loc[day_mask, temp_col].mean(), 2),
        "avg_night_temperature": round(df.loc[~day_mask, temp_col].mean(), 2),
    }
    logger.info("Dienos/nakties temperatūros: %s", result)
    return result


# ---------------------------------------------------------------------------
# 2c) Savaitgaliai su lietaus prognoze
# ---------------------------------------------------------------------------


def count_rainy_weekends(df: pd.DataFrame) -> int:
    """Suskaičiuoja savaitgalius, kai buvo prognozuojamas lietus.

    Savaitgalis laikomas „lietingu", jei bent vienas valandinis prognozės įrašas
    šeštadienį arba sekmadienį nurodo lietų (conditionCode arba totalPrecipitation > 0).

    Parameters
    ----------
    df : pd.DataFrame
        Istorinių arba prognozės DataFrame.

    Returns
    -------
    int
        Lietingų savaitgalių skaičius.
    """
    # Šeštadienis = 5, sekmadienis = 6
    weekend_mask = df.index.dayofweek >= 5

    rain_mask = _detect_rain(df)
    rainy_weekend = df.index[weekend_mask & rain_mask]

    # Kiekvieną savaitgalį skaičiuojame kaip vieną vienetą pagal ISO savaitės numerį
    rainy_weekends = set(
        (d.isocalendar().year, d.isocalendar().week)
        for d in rainy_weekend
    )
    count = len(rainy_weekends)
    logger.info("Lietingų savaitgalių skaičius: %d", count)
    return count


# ---------------------------------------------------------------------------
# 3) Grafikas: praėjusi savaitė + prognozė
# ---------------------------------------------------------------------------


def plot_temperature_combined(
    df_hist: pd.DataFrame,
    df_fore: pd.DataFrame,
    output_path: str | None = None,
) -> plt.Figure:
    """Atvaizduoja paskutinės savaitės išmatuotą ir prognozuojamą temperatūrą.

    Parameters
    ----------
    df_hist : pd.DataFrame
        Istoriniai stebėjimai.
    df_fore : pd.DataFrame
        Prognozės duomenys.
    output_path : str | None
        Jei nurodytas, grafikas išsaugomas į failą.

    Returns
    -------
    matplotlib.figure.Figure
    """
    temp_hist = _find_column(df_hist, ["airTemperature", "temperature", "temp"])
    temp_fore = _find_column(df_fore, ["airTemperature", "temperature", "temp"])

    if temp_hist is None or temp_fore is None:
        raise ValueError("Nerastas temperatūros stulpelis viename iš DataFrame.")

    # Paskutinė savaitė istoriniuose duomenyse
    last_week_start = df_hist.index[-1] - pd.Timedelta(days=7)
    hist_week = df_hist.loc[df_hist.index >= last_week_start, temp_hist]

    fore_series = df_fore[temp_fore]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(hist_week.index, hist_week.values, color="#1f77b4", linewidth=1.8, label="Išmatuota temperatūra")
    ax.plot(fore_series.index, fore_series.values, color="#ff7f0e", linewidth=1.8, linestyle="--", label="Prognozuojama temperatūra")

    # Vertikali linija ties perėjimu
    if not hist_week.empty and not fore_series.empty:
        ax.axvline(hist_week.index[-1], color="gray", linestyle=":", linewidth=1, label="Dabar")

    ax.set_title("Temperatūra: paskutinė savaitė ir ateinančio laikotarpio prognozė", fontsize=13)
    ax.set_xlabel("Laikas")
    ax.set_ylabel("Temperatūra (°C)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate()
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150)
        logger.info("Grafikas išsaugotas: %s", output_path)

    return fig


# ---------------------------------------------------------------------------
# 4) Interpoliavimas iki 5 minučių
# ---------------------------------------------------------------------------


def resample_to_5min(series: pd.Series) -> pd.Series:
    """Perarba valandinę temperatūros Series į 5 minučių dažnį interpoliuojant.

    Parameters
    ----------
    series : pd.Series
        Valandinė temperatūros Series su DatetimeIndex.

    Returns
    -------
    pd.Series
        Series su 5 minučių dažniu; tarpinės reikšmės interpoliuotos tiesiškai.
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("Series indeksas turi būti pd.DatetimeIndex.")

    resampled = series.resample("5min").interpolate(method="time")
    logger.info(
        "Persemplavota: %d → %d įrašų (5 min dažnis)", len(series), len(resampled)
    )
    return resampled


# ---------------------------------------------------------------------------
# Vidiniai pagalbiniai metodai
# ---------------------------------------------------------------------------


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Grąžina pirmą rastą stulpelį iš kandidatų sąrašo."""
    for col in candidates:
        if col in df.columns:
            return col
    # Atvejis kai pavadinimas šiek tiek skiriasi
    lower_map = {c.lower(): c for c in df.columns}
    for col in candidates:
        if col.lower() in lower_map:
            return lower_map[col.lower()]
    return None


def _detect_rain(df: pd.DataFrame) -> pd.Series:
    """Nustato lietaus požymį pagal turimus stulpelius."""
    cond_col = _find_column(df, ["conditionCode", "condition"])
    precip_col = _find_column(df, ["totalPrecipitation", "precipitation", "precip"])

    rain_mask = pd.Series(False, index=df.index)

    if cond_col is not None:
        rain_keywords = ("rain", "drizzle", "shower", "thunder", "lietus", "lyja")
        rain_mask |= df[cond_col].astype(str).str.lower().str.contains(
            "|".join(rain_keywords), na=False
        )

    if precip_col is not None:
        rain_mask |= df[precip_col].fillna(0) > 0

    return rain_mask
