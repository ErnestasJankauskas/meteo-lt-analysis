# meteo.lt API – Meteorologinių duomenų analizė

Python projektas, kuris naudoja [meteo.lt REST API](https://api.meteo.lt/) meteorologiniams duomenims nuskaityti ir analizuoti.

## Struktūra

```
meteo_project/
├── meteo_client.py     # MeteoClient klasė (1 punktas)
├── analysis.py         # Analizės funkcijos (2–4 punktai)
├── main.py             # Pagrindinis scenarijus
├── meteo_analysis.ipynb  # Jupyter Notebook versija
├── requirements.txt
└── README.md
```

## Įdiegimas

```bash
pip install -r requirements.txt
```

## Paleidimas

```bash
python main.py
```

arba Jupyter Notebook:

```bash
jupyter notebook meteo_analysis.ipynb
```

## Funkcionalumas

### 1. `MeteoClient` klasė
- `fetch_historical(start, end)` – istoriniai stebėjimai už nurodytą laikotarpį
- `fetch_forecast()` – trumpalaikė prognozė
- Grąžina `pd.DataFrame` su `pd.DatetimeIndex` (LT laiko zona `Europe/Vilnius`)

### 2. Analizė
- **2a** – vidutinė metų temperatūra ir oro drėgmė
- **2b** – dienos (08:00–20:00) ir nakties vidutinė temperatūra
- **2c** – lietingų savaitgalių skaičius

### 3. Grafikas
Kombinuotas grafikas: paskutinė savaitė (išmatuota) + prognozė

### 4. Persemplavimas
`resample_to_5min(series)` – valandinę Series konvertuoja į 5 min dažnį naudojant tiesinę interpoliaciją

## API dokumentacija
https://api.meteo.lt/
