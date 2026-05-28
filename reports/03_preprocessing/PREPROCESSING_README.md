# Preprocessing Report

This folder contains audit artifacts from `notebooks/03_preprocessing.ipynb`.

## Data Output
- Main processed dataset: `data/processed/sea_rainfall_daily_2020_2025_processed_features.csv`.
- The processed dataset is intentionally slim and already contains the `split` column.
- Separate train/validation/test files are not exported.
- Source-side raw measurements remain in `data/raw/`; the processed table keeps compact target, weather, history, and uncertainty features.

## Target Candidates
- `target_nasa_power_precipitation_mm`: NASA POWER rainfall.
- `target_open_meteo_precipitation_mm`: Open-Meteo rainfall.
- `target_baseline_two_source_mean_mm`: raw arithmetic mean of the two sources; use as baseline only.
- `target_nasa_reference_consensus_mm`: Open-Meteo calibrated to NASA using train city-month bias, then averaged.
- `target_open_meteo_reference_consensus_mm`: NASA calibrated to Open-Meteo using train city-month bias, then averaged.

## Why Some Columns Were Dropped
- Raw source rainfall columns duplicate target candidates.
- Raw source-specific weather columns are summarized by two-source means and source-gap features.
- Scaled `z_` columns are not exported to avoid doubling the feature count; scaling parameters are saved in `tables/03_scaling_parameters.csv`.
- Dropped columns are documented in `tables/07_excluded_columns_from_slim_dataset.csv`.

## Imputation
Raw targets and raw source measurements are not imputed because notebook 03 finds no missing values there.
Only lag/rolling/spell predictors are imputed when missing due to temporal warm-up.
Formula: if missing, fill with median_train(feature | entity_id); fallback median_train(feature).

## Recommended Use
Do not treat the raw two-source mean as an unquestioned ground truth. Train later models against multiple target candidates and report sensitivity.