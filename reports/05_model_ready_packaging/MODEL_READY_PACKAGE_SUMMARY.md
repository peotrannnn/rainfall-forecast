# Leakage-Free Model-Ready Package

## Output Files
- X matrix: `data/processed/model_ready/sea_rainfall_daily_2020_2025_model_ready_strict_forecast_X.csv`
- y targets: `data/processed/model_ready/sea_rainfall_daily_2020_2025_model_ready_targets_y.csv`

## Leakage Policy
- X contains only strict forecast features: location, cyclic calendar, previous rainfall history, previous wet/dry spell features, and imputation flags.
- X contains no target columns.
- X contains no same-day source uncertainty columns.
- X contains no same-day weather columns.
- y contains target candidates only and is stored separately.

## Row Alignment
- X and y share the same `sample_id`, `entity_id`, `date`, and `split` columns.
- Use `sample_id` or `(entity_id, date)` to join predictions back to targets.