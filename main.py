from __future__ import annotations

from datetime import date, timedelta

from analysis import (
    annual_averages,
    day_night_temperature,
    interpolate_temperature_5min,
    plot_temperature,
    rainy_weekends,
)
from meteo_client import MeteoClient


API_URL = "https://api.meteo.lt/v1"
STATION_CODE = "kauno-ams"
PLACE_CODE = "kaunas"
PLOT_FILE = "temperature_plot.png"


def main() -> None:
    today = date.today()
    start = today - timedelta(days=365)

    client = MeteoClient(
        station_code=STATION_CODE,
        api_url=API_URL,
        place_code=PLACE_CODE,
    )

    print(f"Nuskaitomi istoriniai duomenys: {start} - {today}", flush=True)
    historical = client.get_historical_data(start, today)

    forecast = client.get_forecast_data()

    print("Skaiciuojami rezultatai...", flush=True)
    averages = annual_averages(historical)
    day_night = day_night_temperature(historical)
    weekends = rainy_weekends(historical)
    plot_temperature(historical, forecast, PLOT_FILE)
    temp_5min = interpolate_temperature_5min(historical["airTemperature"].tail(24))

    print("\nRezultatai")
    print(f"Laikotarpis: {start} - {today}")
    print(f"Vidutine metu temperatura: {averages['temperature']} C")
    print(f"Vidutine metu oro dregme: {averages['humidity']} %")
    print(f"Vidutine dienos temperatura: {day_night['day']} C")
    print(f"Vidutine nakties temperatura: {day_night['night']} C")
    print(f"Lietingi savaitgaliai: {weekends}")
    print(f"Grafikas issaugotas: {PLOT_FILE}")
    print(f"5 min. interpoliuotu reiksmiu pavyzdys: {len(temp_5min)} eilutes")
    print(temp_5min.head())


if __name__ == "__main__":
    main()
