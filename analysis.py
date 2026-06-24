from __future__ import annotations

import pandas as pd


TEMP_COL = "airTemperature"
HUMIDITY_COL = "relativeHumidity"


def annual_averages(df: pd.DataFrame) -> dict[str, float]:
    """Vidutine metu temperatura ir oro dregme."""
    return {
        "temperature": round(float(df[TEMP_COL].mean()), 2),
        "humidity": round(float(df[HUMIDITY_COL].mean()), 2),
    }


def day_night_temperature(df: pd.DataFrame) -> dict[str, float]:
    """Vidutine dienos ir nakties temperatura LT laiko zonoje."""
    day = (df.index.hour >= 8) & (df.index.hour < 20)
    return {
        "day": round(float(df.loc[day, TEMP_COL].mean()), 2),
        "night": round(float(df.loc[~day, TEMP_COL].mean()), 2),
    }


def rainy_weekends(df: pd.DataFrame) -> int:
    """Savaitgaliu skaicius, kai sestadieni arba sekmadieni fiksuotas lietus."""
    weekend_rows = df[df.index.dayofweek >= 5]
    rain = weekend_rows["conditionCode"].str.contains("rain|shower|thunder", case=False, na=False)

    if "precipitation" in weekend_rows.columns:
        rain = rain | (weekend_rows["precipitation"].fillna(0) > 0)
    if "totalPrecipitation" in weekend_rows.columns:
        rain = rain | (weekend_rows["totalPrecipitation"].fillna(0) > 0)

    rainy_dates = weekend_rows.loc[rain].index
    return len({(d.isocalendar().year, d.isocalendar().week) for d in rainy_dates})


def plot_temperature(df_hist: pd.DataFrame, df_forecast: pd.DataFrame, output: str) -> None:
    """Issaugo paskutines savaites istorines ir prognozuojamos temperaturos grafika."""
    import matplotlib.pyplot as plt

    start = df_hist.index.max() - pd.Timedelta(days=7)
    hist = df_hist.loc[df_hist.index >= start, TEMP_COL]
    forecast = df_forecast[TEMP_COL]

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(hist.index, hist, label="Ismatuota temperatura")
    ax.plot(forecast.index, forecast, label="Prognozuojama temperatura", linestyle="--")
    ax.set_title("Temperatura: paskutine savaite ir prognoze")
    ax.set_xlabel("Laikas")
    ax.set_ylabel("Temperatura, C")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def interpolate_temperature_5min(temperature: pd.Series) -> pd.Series:
    """Valandine temperatura pakeicia i 5 min. dazni ir interpoliuoja reiksmes."""
    if not isinstance(temperature.index, pd.DatetimeIndex):
        raise TypeError("Series indeksas turi buti pd.DatetimeIndex.")

    return temperature.resample("5min").interpolate("time")
