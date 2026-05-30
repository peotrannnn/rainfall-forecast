# Rainfall Web App

Local web app for interactive rainfall prediction with the three models trained in notebook 07.

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

The app loads:

- `models/07_model_training/*_pipeline.joblib`
- `data/processed/model_ready/sea_rainfall_daily_2020_2025_model_ready_strict_forecast_X.csv`
- `data/processed/model_ready/sea_rainfall_daily_2020_2025_model_ready_targets_y.csv`
- `data/groundtruth/sea_station_rainfall_daily_2020_2025_entity_groundtruth.csv`

Predictions are converted from `log1p(rainfall_mm)` back to millimeters with `expm1`, then clipped to `[0, 500]` mm/day, matching notebook 07.
