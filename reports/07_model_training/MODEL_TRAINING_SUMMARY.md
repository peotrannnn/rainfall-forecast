# Model Training Summary

## Selected Target
- `target_nasa_power_precipitation_mm`.
- Reason: notebook 06 selected it as the closest target candidate to independent station ground truth on train/validation rows.

## Leakage Control
- Predictors come only from `strict_forecast_X`.
- Same-day target columns and alternative target candidates are not used as predictors.
- Station ground truth is not used as a model feature.
- Hyperparameter selection uses validation MAE; the test split is reserved for final reporting.

## Retraining Change
- Retrained on 2026-06-01 05:43 UTC.
- Used higher-capacity estimators and moderate rainfall-intensity sample weights (`scale=0.35`) to reduce flat underfitting.
- Web app file names were preserved, so `web_app/server.py` loads the updated models automatically after restart.

## Models Trained
- `hist_gradient_boosting_log`: tuned histogram gradient boosting with early stopping.
- `gradient_boosting_log`: tuned gradient boosting with early stopping.
- `mlp_log`: larger neural network baseline with early stopping.

## Best Model
- Best model: `gradient_boosting_log`.
- Validation MAE: 4.4763 mm/day.
- Validation prediction std capture: 0.487.
- Test MAE: 5.2256 mm/day.
- Test RMSE: 12.6507 mm/day.
- Test R2: 0.2195.
- Test wet-day accuracy: 0.8406.
- Test prediction std capture: 0.401.

## Saved Outputs
- Models: `models/07_model_training/`.
- Tables: `reports/07_model_training/tables/`.

## Important Prediction Note
The saved pipelines predict `log1p(rainfall_mm)`. For inference, convert prediction back with `expm1`, then clip to `[0, 500]` mm/day. The file `best_model_metadata.json` records this rule.
