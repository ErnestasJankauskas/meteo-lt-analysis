# meteo.lt duomenu analize

Trumpas Python projektas, kuris per `https://api.meteo.lt/v1` nuskaito Kauno meteorologinius duomenis ir atlieka uzduotyje prasytus skaiciavimus.

## Paleidimas

```bash
pip install -r requirements.txt
python main.py
```

## Failai

- `meteo_client.py` - `MeteoClient` klase API duomenims nuskaityti.
- `analysis.py` - skaiciavimu, grafiko ir interpoliavimo funkcijos.
- `main.py` - pagrindinis paleidimo failas.
- `meteo_ataskaita.docx` - trumpa darbo ataskaita.

## Kas atliekama

1. Istoriniai ir prognozes duomenys grazinami kaip `pandas.DataFrame` su `DatetimeIndex` ir `Europe/Vilnius` laiko zona.
2. Is paskutiniu metu istoriniu duomenu apskaiciuojama:
   - vidutine metu temperatura ir oro dregme;
   - vidutine dienos ir nakties temperatura;
   - lietingu savaitgaliu skaicius.
3. Sukuriamas grafikas `temperature_plot.png`, kuriame rodoma paskutines savaites ismatuota temperatura ir prognoze.
4. Funkcija `interpolate_temperature_5min` valandine temperatura interpoliuoja i 5 minuciu dazni.
