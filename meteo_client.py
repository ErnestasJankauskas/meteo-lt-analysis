from __future__ import annotations

from datetime import date, datetime
from time import sleep
import pandas as pd
import requests


class MeteoClient:
    """Klientas meteo.lt REST API duomenims nuskaityti."""

    timezone = "Europe/Vilnius"

    def __init__(
        self,
        station_code: str,
        api_url: str = "https://api.meteo.lt/v1",
        place_code: str = "vilnius",
        timeout: int = 30,
        request_delay: float = 0.15,
    ) -> None:
        self.station_code = station_code
        self.api_url = api_url.rstrip("/")
        self.place_code = place_code
        self.timeout = timeout
        self.request_delay = request_delay
        self.session = requests.Session()

    def get_historical_data(self, start: date | str, end: date | str) -> pd.DataFrame:
        """Nuskaito istorinius valandinius duomenis uz intervala nuo-iki."""
        dates = pd.date_range(start=start, end=end, freq="D")
        frames: list[pd.DataFrame] = []

        total_days = len(dates)

        for number, day in enumerate(dates, start=1):
            url = f"{self.api_url}/stations/{self.station_code}/observations/{day:%Y-%m-%d}"
            response = self._get(url)
            observations = response.json().get("observations", [])
            frame = self._to_dataframe(observations, "observationTimeUtc")
            if not frame.empty:
                frames.append(frame)
            if number == 1 or number % 25 == 0 or number == total_days:
                print(f"Istoriniai duomenys: {number}/{total_days} dienu", flush=True)
            sleep(self.request_delay)

        if not frames:
            return pd.DataFrame()

        return pd.concat(frames).sort_index()

    def get_forecast_data(self) -> pd.DataFrame:
        """Nuskaito prognozes valandinius duomenis."""
        print("Nuskaitoma prognoze...", flush=True)
        url = f"{self.api_url}/places/{self.place_code}/forecasts/long-term"
        response = self._get(url)
        forecasts = response.json().get("forecastTimestamps", [])
        return self._to_dataframe(forecasts, "forecastTimeUtc")

    def _get(self, url: str) -> requests.Response:
        for attempt in range(5):
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 429:
                response.raise_for_status()
                return response
            sleep(1 + attempt)

        response.raise_for_status()
        return response

    def _to_dataframe(self, rows: list[dict], time_column: str) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df[time_column] = pd.to_datetime(df[time_column], utc=True)
        df = df.set_index(time_column).sort_index()
        df.index = df.index.tz_convert(self.timezone)
        df.index.name = "time"

        for column in df.columns:
            numeric = pd.to_numeric(df[column], errors="coerce")
            if numeric.notna().any():
                df[column] = numeric

        return df


# Suderinamumas su ankstesniais failais, jei notebook'e naudoti seni vardai.
MeteoClient.fetch_historical = MeteoClient.get_historical_data
MeteoClient.fetch_forecast = MeteoClient.get_forecast_data
