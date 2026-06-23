"""
meteo_client.py
---------------
Lietuvos hidrometeorologijos tarnybos (meteo.lt) REST API klientas.

Naudojimas:
    client = MeteoClient(station_code="vilnius", base_url="https://api.meteo.lt/v1")
    df_hist = client.fetch_historical(start="2025-06-23", end="2026-06-23")
    df_fore = client.fetch_forecast()
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class MeteoClient:
    """Sąsaja su meteo.lt REST API.

    Parameters
    ----------
    station_code : str
        Stoties kodas (pvz. "vilnius", "kaunas").
    base_url : str
        API pagrindinis URL (numatytasis: "https://api.meteo.lt/v1").
    timeout : int
        HTTP užklausos laukimo laikas sekundėmis.
    """

    _TIMEZONE = "Europe/Vilnius"
    _DATETIME_FMT = "%Y-%m-%dT%H:%M:%S"

    def __init__(
        self,
        station_code: str,
        base_url: str = "https://api.meteo.lt/v1",
        timeout: int = 30,
    ) -> None:
        self.station_code = station_code
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    # ------------------------------------------------------------------
    # Vidiniai pagalbiniai metodai
    # ------------------------------------------------------------------

    def _get(self, path: str) -> dict | list:
        """Atlieka GET užklausą ir grąžina atsakymo JSON."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.debug("GET %s", url)
        response = self._session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _records_to_dataframe(self, records: list[dict]) -> pd.DataFrame:
        """Konvertuoja API įrašų sąrašą į DataFrame su DatetimeIndex (LT laiko zona)."""
        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)

        # Laikotarpio stulpelio identifikavimas
        time_col = next(
            (c for c in ("forecastTimeUtc", "observationTimeUtc") if c in df.columns),
            None,
        )
        if time_col is None:
            raise ValueError(f"Nerasta laiko stulpelio. Stulpeliai: {df.columns.tolist()}")

        df[time_col] = pd.to_datetime(df[time_col], format=self._DATETIME_FMT, utc=True)
        df = df.set_index(time_col)
        df.index = df.index.tz_convert(self._TIMEZONE)
        df.index.name = "time"

        # Skaitiniai stulpeliai
        numeric_cols = df.select_dtypes(include="object").columns
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="ignore")

        return df.sort_index()

    # ------------------------------------------------------------------
    # Viešieji metodai
    # ------------------------------------------------------------------

    def fetch_historical(
        self,
        start: str | datetime,
        end: str | datetime,
    ) -> pd.DataFrame:
        """Grąžina istorinius stebėjimų duomenis už nurodytą laikotarpį.

        Parameters
        ----------
        start : str | datetime
            Pradžios data (imtinai), pvz. "2025-01-01" arba datetime objektas.
        end : str | datetime
            Pabaigos data (imtinai).

        Returns
        -------
        pd.DataFrame
            DataFrame su pd.DatetimeIndex (LT laiko zona).
        """
        if isinstance(start, datetime):
            start = start.strftime("%Y-%m-%d")
        if isinstance(end, datetime):
            end = end.strftime("%Y-%m-%d")

        path = (
            f"stations/{self.station_code}/observations/{start}/{end}"
        )
        data = self._get(path)
        observations = data.get("observations", data) if isinstance(data, dict) else data
        logger.info(
            "Gauta %d istorinių įrašų (%s – %s)", len(observations), start, end
        )
        return self._records_to_dataframe(observations)

    def fetch_forecast(self) -> pd.DataFrame:
        """Grąžina trumpalaikę prognozę.

        Returns
        -------
        pd.DataFrame
            DataFrame su pd.DatetimeIndex (LT laiko zona).
        """
        path = f"places/{self.station_code}/forecasts/long-range"
        data = self._get(path)
        forecasts = data.get("forecastTimestamps", data) if isinstance(data, dict) else data
        logger.info("Gauta %d prognozės įrašų", len(forecasts))
        return self._records_to_dataframe(forecasts)
