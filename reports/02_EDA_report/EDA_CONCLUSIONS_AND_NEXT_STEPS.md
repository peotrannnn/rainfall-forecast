# EDA Conclusions and Next-Step Plan

## Main EDA Results
- Coverage: 26,304 daily entity-date rows, 12 canonical locations, 2020-01-01 to 2025-12-31.
- Wettest city by total rainfall: Singapore (24812 mm).
- Driest city by total rainfall: Bangkok (9681 mm).
- Highest wet-day persistence: Singapore (91.9%).

## Source Agreement
- Global MAE: 5.88 mm/day.
- Global RMSE: 12.38 mm/day.
- Global Pearson correlation: 0.42.
- Global wet-day Cohen kappa: 0.58.
- Highest city-level source disagreement: Singapore (10.46 mm/day MAE).

## Processing Decision
- Strict direct averaging is supported for 0/12 cities.
- Do-not-blindly-average is triggered for 11/12 cities.
- Recommended strategy: keep both sources, create uncertainty features, calibrate by city-month where justified, and compare multiple target candidates.

## Next Notebook
- Build `03_preprocessing.ipynb` around target sensitivity, city/month bias correction, temporal splits, and model-ready feature tables.