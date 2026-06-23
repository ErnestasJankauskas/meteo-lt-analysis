"""
main.py
-------
Pagrindinis vykdymo scenarijus. Paleidžiamas tiesiogiai:

    python main.py

Atlieka visus užduoties punktus (1–4) ir išveda rezultatus į konsolę bei
išsaugo temperatūros grafiką kaip PNG failą.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd

from analysis import (
    compute_annual_averages,
    compute_day_night_temperatures,
    count_rainy_weekends,
    plot_temperature_combined,
    resample_to_5min,
)
from meteo_client import MeteoClient

# ---------------------------------------------------------------------------
# Žurnalo konfigūracija
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Nustatymai
# ---------------------------------------------------------------------------
STATION_CODE = "vilnius"      # Stoties / vietovės kodas
BASE_URL = "https://api.meteo.lt/v1"
PLOT_OUTPUT = "temperature_combined.png"

TODAY = date.today()
ONE_YEAR_AGO = TODAY - timedelta(days=365)


def main() -> None:
    # -----------------------------------------------------------------------
    # 1) Duomenų nuskaitymas
    # -----------------------------------------------------------------------
    client = MeteoClient(station_code=STATION_CODE, base_url=BASE_URL)

    logger.info("Nuskaitomi istoriniai duomenys: %s – %s", ONE_YEAR_AGO, TODAY)
    df_hist = client.fetch_historical(start=str(ONE_YEAR_AGO), end=str(TODAY))

    logger.info("Nuskaitomi prognozės duomenys...")
    df_fore = client.fetch_forecast()

    if df_hist.empty:
        logger.error("Istoriniai duomenys tušti – patikrinkite stoties kodą ir API.")
        return

    print("\n" + "=" * 60)
    print("ISTORINIAI DUOMENYS (pirmosios eilutės):")
    print(df_hist.head())
    print(f"\nStulpeliai: {df_hist.columns.tolist()}")
    print(f"Laikotarpis: {df_hist.index[0]}  →  {df_hist.index[-1]}")

    # -----------------------------------------------------------------------
    # 2a) Vidutinė metų temperatūra ir drėgmė
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("2a) METINIAI VIDURKIAI:")
    averages = compute_annual_averages(df_hist)
    for key, val in averages.items():
        label = "Vidutinė temperatūra" if "temperature" in key else "Vidutinė oro drėgmė"
        unit = "°C" if "temperature" in key else "%"
        print(f"   {label}: {val} {unit}")

    # -----------------------------------------------------------------------
    # 2b) Dienos ir nakties temperatūros
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("2b) DIENOS (08–20) IR NAKTIES TEMPERATŪROS:")
    day_night = compute_day_night_temperatures(df_hist)
    for key, val in day_night.items():
        label = "Vidutinė dienos temp." if "day" in key else "Vidutinė nakties temp."
        print(f"   {label}: {val} °C")

    # -----------------------------------------------------------------------
    # 2c) Savaitgaliai su lietaus prognoze
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("2c) LIETINGI SAVAITGALIAI (per pastaruosius metus):")
    rainy_count = count_rainy_weekends(df_hist)
    print(f"   Savaitgalių su lietumi: {rainy_count}")

    # -----------------------------------------------------------------------
    # 3) Grafikas: paskutinė savaitė + prognozė
    # -----------------------------------------------------------------------
    if not df_fore.empty:
        print("\n" + "=" * 60)
        print("3) TEMPERATŪROS GRAFIKAS (išsaugomas į failą):")
        fig = plot_temperature_combined(df_hist, df_fore, output_path=PLOT_OUTPUT)
        print(f"   Grafikas išsaugotas: {PLOT_OUTPUT}")
        # Jei paleidžiama interaktyviai, galima parodyti grafiką:
        # fig.show()
    else:
        logger.warning("Prognozės duomenys tušti – grafikas nekurtas.")

    # -----------------------------------------------------------------------
    # 4) Persemplaviimas iki 5 minučių
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("4) TEMPERATŪROS PERSEMPLAVIMAS IKI 5 MINUČIŲ:")
    temp_col = next(
        (c for c in ("airTemperature", "temperature", "temp") if c in df_hist.columns),
        None,
    )
    if temp_col:
        # Naudojame paskutinės paros duomenis kaip pavyzdį
        sample = df_hist[temp_col].last("1D")
        resampled = resample_to_5min(sample)
        print(f"   Pradinių taškų: {len(sample)}")
        print(f"   Po persemplavimo: {len(resampled)}")
        print(f"   Dažnis: {resampled.index.freq}")
        print("\n   Pirmos kelios reikšmės:")
        print(resampled.head(10).to_string())
    else:
        logger.warning("Temperatūros stulpelis nerastas persemplavimui.")

    print("\n" + "=" * 60)
    print("Visi skaičiavimai atlikti sėkmingai.")


if __name__ == "__main__":
    main()
