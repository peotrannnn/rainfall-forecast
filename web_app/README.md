# Rainfall Forecast Series Web App

Local web app for interactive Southeast Asia rainfall prediction.

## Run

Double-click:

```text
web_app\start_web_app.bat
```

Or run manually:

```bash
python web_app/server.py --host 127.0.0.1 --port 8007
```

Then open:

```text
http://127.0.0.1:8007/
```

## What The App Does

1. Select one city.
2. Select one trained model from notebook 07.
3. The backend fetches the latest observed rainfall history from web APIs.
4. The backend rebuilds the same lag, rolling, wet-spell, dry-spell, location, and calendar features used during training.
5. The selected model predicts rainfall for the next 14 days after today.
6. The frontend plots the full predicted rainfall series, Open-Meteo web forecast, NASA historical baseline, rainfall-intensity bands, volatility metrics, and highest-risk days.

## Web Input Sources

The model is still your trained ML model. NASA POWER is used to provide the recent historical rainfall inputs needed by the model.

- NASA POWER Daily API: `PRECTOTCORR`.
- Local packaged NASA target data: final fallback for dates already inside the project dataset.
- NASA 2020-2025 day-of-year climatology: final NASA-only fallback when recent NASA NRT days are not yet available.

## NASA Context And Comparison

The dashboard also fetches recent daily context from NASA POWER:

- latest available NASA daily temperature
- latest available NASA daily rainfall
- latest available NASA daily humidity
- latest available NASA daily wind speed

NASA POWER does not provide the same kind of operational future weather forecast as a weather provider. Therefore, the chart keeps NASA as a seasonal baseline and adds a separate Open-Meteo web forecast line as an external reference.

## Three Forecast Lines

- ML forecast: the selected trained model.
- Web forecast: Open-Meteo Forecast API, used only as an external reference line.
- NASA seasonal baseline: NASA POWER 2020-2025 day-of-year average, used as a historical seasonal reference.

The web forecast and NASA baseline are not used as model input features.

## Leakage Rule

The app does not feed same-day target values, station ground truth, or alternative target columns into the model. It uses prior-day rainfall history only to rebuild model features.

Multi-day future forecasting needs future lag inputs. Day 1 uses observed web history only. Day 2 onward uses earlier ML predictions as rainfall-memory inputs because those future prior days have not happened yet. If the observed history needed for Day 1 is incomplete, the affected prediction rows are marked unavailable.

## Rainfall Classes

- Rain unlikely: below 1 mm/day.
- Light rain: 1 to below 10 mm/day.
- Moderate rain: 10 to below 25 mm/day.
- Heavy rain: 25 to below 50 mm/day.
- Extreme rain: 50 mm/day or more.
