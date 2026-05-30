# Model Training Summary

## Selected Target
- `target_nasa_power_precipitation_mm`.
- Reason: notebook 06 selected it as the closest target candidate to independent NOAA GHCN-Daily station ground truth on train/validation rows.

## Leakage Control
- Predictors come only from `strict_forecast_X`.
- Same-day target columns and alternative target candidates are not used as predictors.
- NOAA station ground truth is not used as a model feature.
- Hyperparameter selection uses validation MAE; the test split is reserved for final reporting.

## Models Trained
- `hist_gradient_boosting_log`: nonlinear tabular model with early stopping.
- `gradient_boosting_log`: classical gradient boosting with early stopping.
- `mlp_log`: neural network baseline with early stopping.

## Best Model
- Best model: `mlp_log`.
- Best trial: `mlp_log_trial_01`.
- Train MAE: 4.4583 mm/day.
- Validation MAE: 4.3448 mm/day.
- Test MAE: 5.0929 mm/day.
- Test RMSE: 12.3594 mm/day.
- Test R2: 0.2550.
- Test wet-day accuracy: 0.8395.

## Saved Outputs
- Models: `models/07_model_training/`.
- Tables: `reports/07_model_training/tables/`.
- Figures: `reports/07_model_training/figures/`.

## Important Prediction Note
The saved pipelines predict `log1p(rainfall_mm)`. For inference, convert prediction back with `expm1`, then clip to `[0, 500]` mm/day. The file `best_model_metadata.json` records this rule.
