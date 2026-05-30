# 01 Data Collection Report

## Purpose
Notebook `notebooks/01_data_collection.ipynb` builds the raw multi-source rainfall dataset for Southeast Asia. It is a data collection and entity-resolution notebook, not a modeling notebook.

## What It Downloads
- Source 1: NASA POWER Daily API.
- Source 2: Open-Meteo Historical Weather API.
- Both sources require no API key.
- Date range: `2020-01-01` to `2025-12-31`.
- Frequency: `daily`.
- Locations: 12 canonical Southeast Asia city entities.
- Total API requests: 24.

The collected variables are daily precipitation, temperature, relative humidity, wind speed, and surface pressure. Units are standardized into `mm/day`, `C`, `percent`, `m/s`, and `kPa`.

## Entity Resolution
Each source-returned coordinate is mapped to the nearest canonical city coordinate within 50 km using the Haversine distance. After that, NASA POWER and Open-Meteo records are merged by `entity_id + date`.

## Output Files
- `data\raw\sea_rainfall_daily_2020_2025_raw_api_responses.jsonl`: raw JSONL API audit trail.
- `data\raw\sea_rainfall_daily_2020_2025_source_observations.csv`: long-form source observations.
- `data\raw\sea_rainfall_daily_2020_2025_entity_resolved.csv`: wide entity-date table with both sources side by side.
- `data\raw\sea_rainfall_daily_2020_2025_entity_registry.csv`: entity-resolution registry.
- `data\raw\sea_rainfall_daily_2020_2025_manifest.json`: dataset manifest and hashes.

## Row Counts
- Raw API requests: 24.
- Source observation rows: 52608.
- Rows per source: 26304.
- Entity-resolved rows: 26304.
- Entity registry rows: 12.

Formula: `12 cities x 2,192 daily dates = 26,304 rows per source`.

## Quality Result
- Source duplicate rows: 0.
- Entity-date duplicate rows after resolution: 0.
- Negative precipitation rows: 0.
- Missing rate for standard variables: 0 percent for both sources.

## Interpretation
Notebook 01 does not decide which source is more correct. It only collects and aligns NASA POWER and Open-Meteo. Because there is no independent station/rain-gauge ground truth here, source disagreement must be analyzed in later notebooks.

## Report Tables
See `reports/01_data_collection_report/tables/` for compact CSV documentation tables.
