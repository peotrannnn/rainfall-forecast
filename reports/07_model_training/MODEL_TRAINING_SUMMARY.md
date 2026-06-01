# Model Training Summary

## Selected Target
- `target_nasa_power_precipitation_mm`.
- The target choice comes from notebook 06.

## Data Inputs
- `sea_rainfall_daily_2020_2025_model_ready_strict_forecast_X.csv`.
- `sea_rainfall_daily_2020_2025_model_ready_targets_y.csv`.
- No raw collection files are used in this notebook.

## Retraining Change
- Retrained on 2026-06-01 05:56 UTC.
- Added weather-assisted model-ready features so the web forecast series does not collapse into an overly flat recursive line.
- Open-Meteo target is used during training as a proxy for the future web forecast feature used by the frontend/backend.
- NASA seasonal baseline is computed from the train split only.

## Leakage Control
- The selected NASA target column is not used as a direct feature.
- Station ground truth is not used as a model feature.
- Future deployment fills provider features from web forecast, not from the observed target table.

## Models Trained
- `hist_gradient_boosting_log`.
- `gradient_boosting_log`.
- `mlp_log`.

## Best Model
- Best model: `hist_gradient_boosting_log`.
- Validation MAE: 4.5833 mm/day.
- Validation prediction std capture: 0.540.
- Test MAE: 5.2291 mm/day.
- Test RMSE: 12.9303 mm/day.
- Test R2: 0.1846.
- Test wet-day accuracy: 0.8532.
- Test prediction std capture: 0.432.

## Saved Outputs
- Models: `models/07_model_training/`.
- Tables: `reports/07_model_training/tables/`.

## Important Prediction Note
The saved pipelines predict `log1p(rainfall_mm)`. For inference, convert prediction back with `expm1`, then clip to `[0, 500]` mm/day.
