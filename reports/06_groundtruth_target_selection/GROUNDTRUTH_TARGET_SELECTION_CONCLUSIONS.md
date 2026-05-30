# Ground-Truth Target Selection Conclusions

## Recommended Target
- Primary training target: `target_nasa_power_precipitation_mm` (NASA POWER raw).
- Selection rule: lowest train/validation MAE against independent NOAA GHCN-Daily station ground truth; tie-broken by RMSE and absolute bias.
- MAE: 9.421 mm/day.
- RMSE: 17.645 mm/day.
- Bias: -0.220 mm/day.
- Paired train/validation rows: 11840.

## Ground-Truth Coverage
- Ground-truth entity-date rows: 26,304.
- Paired train/validation rows used for target selection: 11,840.
- Mean city coverage: 0.509.
- Minimum city coverage: 0.018.

## Leakage Guard
- Station ground truth is used only as the target-selection reference, not as a model predictor.
- The target decision uses only train and validation rows.
- The test split remains untouched for final model evaluation.

## Output Data
- `data/groundtruth/sea_station_rainfall_daily_2020_2025_station_observations.csv`
- `data/groundtruth/sea_station_rainfall_daily_2020_2025_entity_groundtruth.csv`
- `data/groundtruth/sea_station_rainfall_daily_2020_2025_station_registry.csv`
- `data/groundtruth/sea_station_rainfall_daily_2020_2025_manifest.json`
