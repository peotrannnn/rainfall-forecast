from __future__ import annotations

import argparse
import json
import math
import mimetypes
import time
from datetime import datetime, timedelta
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, unquote, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = Path(__file__).resolve().parent
APP_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")

MODEL_DIR = PROJECT_ROOT / "models" / "07_model_training"
X_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "model_ready"
    / "sea_rainfall_daily_2020_2025_model_ready_strict_forecast_X.csv"
)
Y_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "model_ready"
    / "sea_rainfall_daily_2020_2025_model_ready_targets_y.csv"
)

TARGET_COLUMN = "target_nasa_power_precipitation_mm"
PREDICTION_CAP_MM = 500.0
WET_DAY_THRESHOLD_MM = 1.0
LIVE_LOOKBACK_DAYS = 90
FUTURE_FORECAST_DAYS = 14
HTTP_TIMEOUT_SECONDS = 30

NASA_POWER_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

MODEL_FILES = {
    "hist_gradient_boosting_log": {
        "label": "Hist Gradient Boosting",
        "path": MODEL_DIR / "hist_gradient_boosting_log_log_target_pipeline.joblib",
    },
    "gradient_boosting_log": {
        "label": "Gradient Boosting",
        "path": MODEL_DIR / "gradient_boosting_log_log_target_pipeline.joblib",
    },
    "mlp_log": {
        "label": "MLP Neural Network",
        "path": MODEL_DIR / "mlp_log_log_target_pipeline.joblib",
    },
}

RAINFALL_CATEGORIES = [
    {"code": "unlikely", "label": "Rain unlikely", "min_mm": 0.0, "max_mm": 1.0},
    {"code": "light", "label": "Light rain", "min_mm": 1.0, "max_mm": 10.0},
    {"code": "moderate", "label": "Moderate rain", "min_mm": 10.0, "max_mm": 25.0},
    {"code": "heavy", "label": "Heavy rain", "min_mm": 25.0, "max_mm": 50.0},
    {"code": "extreme", "label": "Extreme rain", "min_mm": 50.0, "max_mm": None},
]


def to_json_value(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    return value


def load_required_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required input is missing: {path}")
    return pd.read_csv(path, **kwargs)


def classify_rainfall(value) -> dict | None:
    numeric_value = to_json_value(value)
    if numeric_value is None:
        return None
    for category in RAINFALL_CATEGORIES:
        max_mm = category["max_mm"]
        if numeric_value >= category["min_mm"] and (
            max_mm is None or numeric_value < max_mm
        ):
            return dict(category)
    return dict(RAINFALL_CATEGORIES[-1])


def yyyymmdd(date_value) -> str:
    return pd.Timestamp(date_value).strftime("%Y%m%d")


def fetch_json(url: str, params: dict) -> dict:
    query = urlencode(params, doseq=True)
    request = Request(
        f"{url}?{query}",
        headers={
            "User-Agent": "DS108-rainfall-local-app/2.0",
            "Accept": "application/json",
        },
    )
    started = time.time()
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
    payload["_request_seconds"] = round(time.time() - started, 3)
    return payload


class RainfallAppState:
    def __init__(self) -> None:
        self.x = load_required_csv(X_PATH, parse_dates=["date"])
        self.y = load_required_csv(Y_PATH, parse_dates=["date"])
        if TARGET_COLUMN not in self.y.columns:
            raise KeyError(f"Missing selected target column: {TARGET_COLUMN}")

        self.base_feature_columns = ["entity_id"] + [
            column for column in self.x.columns if column.startswith("feature_")
        ]
        self.feature_columns = self._load_model_feature_columns(self.base_feature_columns)

        self.history_min_date = self.x["date"].min().date()
        self.history_max_date = self.x["date"].max().date()
        self.today = datetime.now(APP_TIMEZONE).date()
        self.series_start_date = max(
            self.today + timedelta(days=1),
            self.history_max_date + timedelta(days=1),
        )
        self.series_end_date = self.series_start_date + timedelta(
            days=FUTURE_FORECAST_DAYS - 1
        )
        self.history_fetch_start_date = self.series_start_date - timedelta(
            days=LIVE_LOOKBACK_DAYS
        )
        self.history_fetch_end_date = self.series_start_date - timedelta(days=1)

        self.city_lookup = self._build_city_lookup()
        self.latest_feature_by_entity = (
            self.x.sort_values("date")
            .groupby("entity_id", sort=False)
            .tail(1)
            .set_index("entity_id", drop=False)
        )
        self.local_target_history = self._build_local_target_history()

        self.models = {}
        for model_name, model_info in MODEL_FILES.items():
            model_path = model_info["path"]
            if not model_path.exists():
                raise FileNotFoundError(f"Model file is missing: {model_path}")
            self.models[model_name] = joblib.load(model_path)

        self.history_cache: dict[str, dict] = {}
        self.series_cache: dict[tuple[str, str], dict] = {}

    def _load_model_feature_columns(self, default_columns: list[str]) -> list[str]:
        metadata_paths = [
            MODEL_DIR / "best_model_metadata.json",
            MODEL_DIR / "hist_gradient_boosting_log_metadata.json",
            MODEL_DIR / "gradient_boosting_log_metadata.json",
            MODEL_DIR / "mlp_log_metadata.json",
        ]
        for path in metadata_paths:
            if not path.exists():
                continue
            try:
                metadata = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            feature_columns = metadata.get("feature_columns")
            if isinstance(feature_columns, list) and feature_columns:
                return [str(column) for column in feature_columns]
        return default_columns

    def _build_city_lookup(self) -> dict[str, dict]:
        rows = (
            self.x[
                [
                    "entity_id",
                    "country",
                    "location_name",
                    "feature_canonical_latitude",
                    "feature_canonical_longitude",
                ]
            ]
            .drop_duplicates("entity_id")
            .copy()
        )
        lookup = {}
        for row in rows.itertuples(index=False):
            lookup[row.entity_id] = {
                "entity_id": row.entity_id,
                "country": row.country,
                "location_name": row.location_name,
                "latitude": float(row.feature_canonical_latitude),
                "longitude": float(row.feature_canonical_longitude),
            }
        return lookup

    def _build_local_target_history(self) -> dict[str, dict[pd.Timestamp, float]]:
        history = {}
        for entity_id, frame in self.y.sort_values("date").groupby("entity_id"):
            entity_history = {}
            for row in frame[["date", TARGET_COLUMN]].itertuples(index=False):
                value = to_json_value(getattr(row, TARGET_COLUMN))
                if value is not None:
                    entity_history[pd.Timestamp(row.date).normalize()] = float(value)
            history[entity_id] = entity_history
        return history

    def options(self) -> dict:
        return {
            "models": [
                {"model_name": name, "label": info["label"]}
                for name, info in MODEL_FILES.items()
            ],
            "cities": sorted(
                list(self.city_lookup.values()),
                key=lambda item: (item["country"], item["location_name"]),
            ),
            "forecast_window": {
                "start": self.series_start_date.strftime("%Y-%m-%d"),
                "end": self.series_end_date.strftime("%Y-%m-%d"),
                "today": self.today.strftime("%Y-%m-%d"),
                "training_end": self.history_max_date.strftime("%Y-%m-%d"),
                "horizon_days": FUTURE_FORECAST_DAYS,
                "lookback_days": LIVE_LOOKBACK_DAYS,
                "rule": (
                    "The model predicts the next 14 days after today. Day 1 uses "
                    "the latest observed web history; later days reuse earlier ML "
                    "predictions as rainfall-memory inputs because their prior days "
                    "are not observed yet."
                ),
            },
            "rainfall_categories": RAINFALL_CATEGORIES,
            "model_input_summary": self.model_input_summary(),
            "live_weather_source": "NASA POWER Daily API",
        }

    def model_input_summary(self) -> dict:
        calendar_features = [
            col
            for col in self.feature_columns
            if any(token in col for token in ["month", "day_of_year", "dayofyear"])
        ]
        location_features = [
            col for col in self.feature_columns if "latitude" in col or "longitude" in col
        ]
        rainfall_memory_features = [
            col
            for col in self.feature_columns
            if any(token in col for token in ["lag", "rolling", "spell", "wet"])
        ]
        weather_forecast_features = [
            col
            for col in self.feature_columns
            if any(token in col for token in ["provider_forecast", "nasa_seasonal"])
        ]
        return {
            "feature_count": len(self.feature_columns),
            "location_feature_count": len(location_features),
            "calendar_feature_count": len(calendar_features),
            "rainfall_memory_feature_count": len(rainfall_memory_features),
            "weather_forecast_feature_count": len(weather_forecast_features),
            "lookback_days": LIVE_LOOKBACK_DAYS,
            "plain_language": (
                "The model uses city identity, coordinates, seasonal sine/cosine "
                "features, rainfall lags, rolling rainfall windows, wet/dry spell "
                "features, imputation flags, and optional weather-assisted provider "
                "forecast features when the loaded model was trained with them."
            ),
        }

    def forecast_series(self, entity_id: str, model_name: str) -> dict:
        if entity_id not in self.city_lookup:
            raise KeyError(f"Unknown city entity_id: {entity_id}")
        if model_name not in self.models:
            raise KeyError(f"Unknown model: {model_name}")

        cache_key = (entity_id, model_name)
        if cache_key in self.series_cache:
            return self.series_cache[cache_key]

        history_payload = self.observed_rainfall_history(entity_id)
        provider_notes = list(history_payload["notes"])
        nasa_baseline = self.build_nasa_reference_series(entity_id)
        try:
            web_forecast = self.fetch_web_forecast(self.city_lookup[entity_id])
        except Exception as exc:
            web_forecast = {}
            provider_notes.append(f"Open-Meteo web forecast unavailable: {exc}")
        running_rainfall_by_date = dict(history_payload["rainfall_by_date"])
        source_counts = dict(history_payload["source_counts"])
        recursive_input_days = 0
        rows = []
        for target_date in pd.date_range(self.series_start_date, self.series_end_date, freq="D"):
            target_day = target_date.date()
            window_dates = [
                pd.Timestamp(target_day - timedelta(days=back)).normalize()
                for back in range(LIVE_LOOKBACK_DAYS, 0, -1)
            ]
            missing_days = [
                day.strftime("%Y-%m-%d")
                for day in window_dates
                if day not in running_rainfall_by_date
            ]
            if missing_days:
                rows.append(
                    {
                        "date": target_day.strftime("%Y-%m-%d"),
                        "prediction_mm": None,
                        "prediction_category": None,
                        "available": False,
                        "missing_input_days": len(missing_days),
                        "missing_input_sample": missing_days[:5],
                    }
                )
                continue

            feature_row = self.build_feature_row(
                entity_id,
                target_day,
                {"rainfall_by_date": running_rainfall_by_date},
                web_forecast_day=web_forecast.get(target_day.strftime("%Y-%m-%d"), {}),
                nasa_baseline_day=nasa_baseline.get(target_day.strftime("%Y-%m-%d"), {}),
            )
            prediction_mm = self.predict_from_feature_row(model_name, feature_row)
            recursive_step = (target_day - self.series_start_date).days
            rows.append(
                {
                    "date": target_day.strftime("%Y-%m-%d"),
                    "prediction_mm": prediction_mm,
                    "prediction_category": classify_rainfall(prediction_mm),
                    "web_forecast_mm": web_forecast.get(
                        target_day.strftime("%Y-%m-%d"), {}
                    ).get("precipitation_sum_mm"),
                    "web_forecast_probability_pct": web_forecast.get(
                        target_day.strftime("%Y-%m-%d"), {}
                    ).get("precipitation_probability_max_pct"),
                    "nasa_baseline_mm": nasa_baseline.get(
                        target_day.strftime("%Y-%m-%d"), {}
                    ).get("precipitation_sum_mm"),
                    "available": True,
                    "missing_input_days": 0,
                    "recursive_step": recursive_step,
                    "feature_memory_source": (
                        "observed web history"
                        if recursive_step == 0
                        else "observed web history + previous ML predictions"
                    ),
                }
            )
            running_rainfall_by_date[pd.Timestamp(target_day).normalize()] = prediction_mm
            recursive_input_days += 1

        available = [row for row in rows if row["available"]]
        if recursive_input_days:
            source_counts["previous ML predictions reused as future lag inputs"] = (
                recursive_input_days
            )
        result = {
            "city": self.city_lookup[entity_id],
            "model": {"model_name": model_name, "label": MODEL_FILES[model_name]["label"]},
            "forecast_window": {
                "start": self.series_start_date.strftime("%Y-%m-%d"),
                "end": self.series_end_date.strftime("%Y-%m-%d"),
                "today": self.today.strftime("%Y-%m-%d"),
                "training_end": self.history_max_date.strftime("%Y-%m-%d"),
                "horizon_days": FUTURE_FORECAST_DAYS,
                "lookback_days": LIVE_LOOKBACK_DAYS,
                "strategy": "recursive_ml_forecast_after_day_1",
            },
            "input_sources": source_counts,
            "web_forecast_source": "Open-Meteo Forecast API",
            "nasa_baseline_source": "NASA POWER 2020-2025 day-of-year climatology baseline",
            "provider_notes": provider_notes,
            "rows": rows,
            "summary": self.series_summary(available, rows),
            "web_comparison_summary": self.comparison_summary(available, "web_forecast_mm"),
            "nasa_baseline_summary": self.comparison_summary(available, "nasa_baseline_mm"),
        }
        self.series_cache[cache_key] = result
        return result

    def build_nasa_reference_series(self, entity_id: str) -> dict[str, dict]:
        climatology = self.nasa_dayofyear_climatology(entity_id)

        reference = {}
        for target_date in pd.date_range(self.series_start_date, self.series_end_date, freq="D"):
            day_of_year = target_date.dayofyear
            value = climatology.get(day_of_year)
            if value is None:
                reference[target_date.strftime("%Y-%m-%d")] = {
                    "precipitation_sum_mm": None,
                    "precipitation_probability_max_pct": None,
                }
                continue
            reference[target_date.strftime("%Y-%m-%d")] = {
                "precipitation_sum_mm": value,
                "precipitation_probability_max_pct": None,
            }
        return reference

    def nasa_dayofyear_climatology(self, entity_id: str) -> dict[int, float]:
        entity_history = self.local_target_history.get(entity_id, {})
        grouped: dict[int, list[float]] = {}
        for date_key, value in entity_history.items():
            day_of_year = pd.Timestamp(date_key).dayofyear
            grouped.setdefault(day_of_year, []).append(float(value))
        return {
            day_of_year: float(np.mean(values))
            for day_of_year, values in grouped.items()
            if values
        }

    def series_summary(self, available_rows: list[dict], all_rows: list[dict]) -> dict:
        if not available_rows:
            return {
                "available_days": 0,
                "total_days": len(all_rows),
                "mean_prediction_mm": None,
                "max_prediction_mm": None,
                "max_prediction_date": None,
                "wet_day_ratio": None,
            }
        values = np.asarray([row["prediction_mm"] for row in available_rows], dtype=float)
        max_index = int(np.argmax(values))
        wet_day_ratio = float(np.mean(values >= WET_DAY_THRESHOLD_MM))
        diffs = np.diff(values)
        day_numbers = np.arange(len(values), dtype=float)
        trend_slope = (
            float(np.polyfit(day_numbers, values, 1)[0]) if len(values) >= 2 else 0.0
        )
        return {
            "available_days": len(available_rows),
            "total_days": len(all_rows),
            "mean_prediction_mm": float(np.mean(values)),
            "max_prediction_mm": float(values[max_index]),
            "max_prediction_date": available_rows[max_index]["date"],
            "wet_day_ratio": wet_day_ratio,
            "std_prediction_mm": float(np.std(values, ddof=0)),
            "p90_prediction_mm": float(np.percentile(values, 90)),
            "mean_daily_change_mm": float(np.mean(np.abs(diffs))) if len(diffs) else 0.0,
            "max_daily_jump_mm": float(np.max(np.abs(diffs))) if len(diffs) else 0.0,
            "trend_slope_mm_per_day": trend_slope,
        }

    def comparison_summary(self, available_rows: list[dict], comparison_field: str) -> dict:
        paired_rows = [
            row
            for row in available_rows
            if to_json_value(row.get(comparison_field)) is not None
        ]
        if not paired_rows:
            return {
                "paired_days": 0,
                "mean_comparison_mm": None,
                "mean_absolute_gap_mm": None,
                "max_absolute_gap_mm": None,
                "correlation": None,
            }
        ml_values = np.asarray([row["prediction_mm"] for row in paired_rows], dtype=float)
        provider_values = np.asarray(
            [row[comparison_field] for row in paired_rows], dtype=float
        )
        gaps = np.abs(ml_values - provider_values)
        correlation = (
            float(np.corrcoef(ml_values, provider_values)[0, 1])
            if len(paired_rows) > 1 and np.std(ml_values) > 0 and np.std(provider_values) > 0
            else None
        )
        return {
            "paired_days": len(paired_rows),
            "mean_comparison_mm": float(np.mean(provider_values)),
            "mean_absolute_gap_mm": float(np.mean(gaps)),
            "max_absolute_gap_mm": float(np.max(gaps)),
            "correlation": correlation,
        }

    def observed_rainfall_history(self, entity_id: str) -> dict:
        if entity_id in self.history_cache:
            return self.history_cache[entity_id]

        city = self.city_lookup[entity_id]
        start_date = self.history_fetch_start_date
        end_date = self.history_fetch_end_date
        notes = []
        nasa_values = {}

        try:
            nasa_values = self.fetch_nasa_power_history(city, start_date, end_date)
        except Exception as exc:
            notes.append(f"NASA POWER unavailable: {exc}")

        local_values = self.local_target_history.get(entity_id, {})
        climatology = self.nasa_dayofyear_climatology(entity_id)
        rainfall_by_date = {}
        source_by_date = {}
        for current_date in pd.date_range(start_date, end_date, freq="D"):
            day = current_date.date()
            key = pd.Timestamp(day).normalize()
            iso = day.strftime("%Y-%m-%d")
            if iso in nasa_values:
                rainfall_by_date[key] = nasa_values[iso]
                source_by_date[iso] = "NASA POWER live"
            elif key in local_values:
                rainfall_by_date[key] = local_values[key]
                source_by_date[iso] = "local packaged NASA fallback"
            elif current_date.dayofyear in climatology:
                rainfall_by_date[key] = climatology[current_date.dayofyear]
                source_by_date[iso] = "NASA 2020-2025 climatology fallback"

        source_counts = pd.Series(source_by_date).value_counts().to_dict()
        result = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "rainfall_by_date": rainfall_by_date,
            "source_by_date": source_by_date,
            "source_counts": source_counts,
            "notes": notes,
        }
        self.history_cache[entity_id] = result
        return result

    def fetch_nasa_power_history(self, city: dict, start_date, end_date) -> dict[str, float]:
        payload = fetch_json(
            NASA_POWER_DAILY_URL,
            {
                "parameters": "PRECTOTCORR",
                "community": "AG",
                "longitude": round(city["longitude"], 4),
                "latitude": round(city["latitude"], 4),
                "start": yyyymmdd(start_date),
                "end": yyyymmdd(end_date),
                "format": "JSON",
            },
        )
        raw_values = payload.get("properties", {}).get("parameter", {}).get("PRECTOTCORR", {})
        values = {}
        for raw_date, value in raw_values.items():
            parsed = to_json_value(value)
            if parsed is not None and parsed > -900:
                values[pd.to_datetime(raw_date).strftime("%Y-%m-%d")] = float(parsed)
        return values

    def fetch_web_forecast(self, city: dict) -> dict[str, dict]:
        payload = fetch_json(
            OPEN_METEO_FORECAST_URL,
            {
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "daily": "precipitation_sum,precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": FUTURE_FORECAST_DAYS + 1,
            },
        )
        daily = payload.get("daily", {})
        dates = daily.get("time", [])
        rainfall_values = daily.get("precipitation_sum", [])
        probability_values = daily.get("precipitation_probability_max", [])
        forecast = {}
        for index, date in enumerate(dates):
            rainfall = rainfall_values[index] if index < len(rainfall_values) else None
            probability = (
                probability_values[index] if index < len(probability_values) else None
            )
            forecast[date] = {
                "precipitation_sum_mm": to_json_value(rainfall),
                "precipitation_probability_max_pct": to_json_value(probability),
            }
        return forecast

    def current_weather(self, entity_id: str) -> dict:
        if entity_id not in self.city_lookup:
            raise KeyError(f"Unknown city entity_id: {entity_id}")
        city = self.city_lookup[entity_id]
        payload = fetch_json(
            NASA_POWER_DAILY_URL,
            {
                "parameters": "PRECTOTCORR,T2M,RH2M,WS10M",
                "community": "AG",
                "longitude": round(city["longitude"], 4),
                "latitude": round(city["latitude"], 4),
                "start": yyyymmdd(self.today - timedelta(days=10)),
                "end": yyyymmdd(self.today),
                "format": "JSON",
            },
        )
        parameters = payload.get("properties", {}).get("parameter", {})
        rainfall = parameters.get("PRECTOTCORR", {})
        latest_raw_date = None
        for raw_date, value in sorted(rainfall.items(), reverse=True):
            parsed = to_json_value(value)
            if parsed is not None and parsed > -900:
                latest_raw_date = raw_date
                break
        if latest_raw_date is None:
            raise ValueError("NASA POWER did not return recent daily weather values.")

        def parameter_value(parameter: str):
            value = parameters.get(parameter, {}).get(latest_raw_date)
            parsed = to_json_value(value)
            if parsed is None or parsed <= -900:
                return None
            return parsed

        return {
            "city": city,
            "source": "NASA POWER Daily API",
            "updated_at": pd.to_datetime(latest_raw_date).strftime("%Y-%m-%d"),
            "timezone": "daily local solar time from NASA POWER",
            "temperature_2m_c": parameter_value("T2M"),
            "relative_humidity_2m_pct": parameter_value("RH2M"),
            "precipitation_mm": parameter_value("PRECTOTCORR"),
            "rain_mm": parameter_value("PRECTOTCORR"),
            "wind_speed_10m_kmh": parameter_value("WS10M"),
            "weather_code": None,
            "weather_label": "NASA daily observed context",
            "today_provider_precipitation_sum_mm": parameter_value("PRECTOTCORR"),
            "today_provider_precipitation_probability_pct": None,
        }

    def build_feature_row(
        self,
        entity_id: str,
        target_date,
        history_payload: dict,
        web_forecast_day: dict | None = None,
        nasa_baseline_day: dict | None = None,
    ) -> pd.Series:
        row = self.latest_feature_by_entity.loc[entity_id].copy()
        row["date"] = pd.Timestamp(target_date)
        row["date_key"] = target_date.strftime("%Y-%m-%d")
        row["split"] = "web_forecast_series"
        row["sample_id"] = f"{entity_id}__{target_date:%Y%m%d}"
        self.patch_calendar_features(row, target_date)
        self.patch_temporal_features(row, target_date, history_payload["rainfall_by_date"])
        self.patch_weather_assisted_features(row, web_forecast_day or {}, nasa_baseline_day or {})
        return row

    def patch_weather_assisted_features(
        self, row: pd.Series, web_forecast_day: dict, nasa_baseline_day: dict
    ) -> None:
        web_mm = to_json_value(web_forecast_day.get("precipitation_sum_mm"))
        web_probability = to_json_value(
            web_forecast_day.get("precipitation_probability_max_pct")
        )
        nasa_baseline_mm = to_json_value(nasa_baseline_day.get("precipitation_sum_mm"))
        web_mm = 0.0 if web_mm is None else float(web_mm)
        web_probability = (
            100.0 if web_mm >= WET_DAY_THRESHOLD_MM else 0.0
            if web_probability is None
            else float(web_probability)
        )
        nasa_baseline_mm = 0.0 if nasa_baseline_mm is None else float(nasa_baseline_mm)
        updates = {
            "feature_provider_forecast_precipitation_mm": web_mm,
            "feature_provider_forecast_log1p_precipitation": math.log1p(max(web_mm, 0.0)),
            "feature_provider_forecast_probability_pct": web_probability,
            "feature_provider_forecast_is_wet": 1.0
            if web_mm >= WET_DAY_THRESHOLD_MM
            else 0.0,
            "feature_nasa_seasonal_baseline_mm": nasa_baseline_mm,
            "feature_provider_minus_nasa_baseline_mm": web_mm - nasa_baseline_mm,
        }
        for column, value in updates.items():
            row[column] = value

    def patch_calendar_features(self, row: pd.Series, target_date) -> None:
        day_of_year = target_date.timetuple().tm_yday
        updates = {
            "feature_month_sin": math.sin(2 * math.pi * target_date.month / 12),
            "feature_month_cos": math.cos(2 * math.pi * target_date.month / 12),
            "feature_day_of_year_sin": math.sin(2 * math.pi * day_of_year / 366),
            "feature_day_of_year_cos": math.cos(2 * math.pi * day_of_year / 366),
            "feature_dayofyear_sin": math.sin(2 * math.pi * day_of_year / 366),
            "feature_dayofyear_cos": math.cos(2 * math.pi * day_of_year / 366),
        }
        for column, value in updates.items():
            if column in row.index:
                row[column] = value

    def patch_temporal_features(
        self, row: pd.Series, target_date, rainfall_by_date: dict[pd.Timestamp, float]
    ) -> None:
        def rain_days_back(days: int) -> float:
            key = pd.Timestamp(target_date - timedelta(days=days)).normalize()
            return float(rainfall_by_date[key])

        def previous_window(days: int) -> np.ndarray:
            return np.asarray([rain_days_back(back) for back in range(days, 0, -1)], dtype=float)

        lag_1 = rain_days_back(1)
        lag_7 = rain_days_back(7)
        lag_30 = rain_days_back(30)
        window_7 = previous_window(7)
        window_30 = previous_window(30)
        window_90 = previous_window(90)
        updates = {
            "feature_rainfall_lag_1d_mm": lag_1,
            "feature_rainfall_lag_7d_mm": lag_7,
            "feature_rainfall_lag_30d_mm": lag_30,
            "feature_rainfall_rolling_7d_mean_prev_mm": float(window_7.mean()),
            "feature_rainfall_rolling_30d_sum_prev_mm": float(window_30.sum()),
            "feature_rainfall_rolling_90d_mean_prev_mm": float(window_90.mean()),
            "feature_wet_spell_days_prev": self.spell_length(target_date, rainfall_by_date, wet=True),
            "feature_dry_spell_days_prev": self.spell_length(target_date, rainfall_by_date, wet=False),
            "feature_was_wet_previous_day": 1.0 if lag_1 >= WET_DAY_THRESHOLD_MM else 0.0,
        }
        for column, value in updates.items():
            if column in row.index:
                row[column] = value
        for column in row.index:
            if column.endswith("_was_imputed") and column.startswith("feature_"):
                row[column] = 0

    def spell_length(
        self, target_date, rainfall_by_date: dict[pd.Timestamp, float], wet: bool
    ) -> int:
        count = 0
        cursor = target_date - timedelta(days=1)
        while count < LIVE_LOOKBACK_DAYS:
            key = pd.Timestamp(cursor).normalize()
            if key not in rainfall_by_date:
                break
            is_wet = float(rainfall_by_date[key]) >= WET_DAY_THRESHOLD_MM
            if is_wet != wet:
                break
            count += 1
            cursor -= timedelta(days=1)
        return count

    def predict_from_feature_row(self, model_name: str, feature_row: pd.Series) -> float:
        model_input = feature_row.reindex(self.feature_columns).to_frame().T
        log_prediction = np.asarray(self.models[model_name].predict(model_input), dtype=float)
        max_log = np.log1p(PREDICTION_CAP_MM)
        log_prediction = np.nan_to_num(log_prediction, nan=0.0, posinf=max_log, neginf=0.0)
        prediction = np.expm1(np.clip(log_prediction[0], 0.0, max_log))
        return float(np.clip(prediction, 0.0, PREDICTION_CAP_MM))


APP_STATE = RainfallAppState()


class RainfallRequestHandler(SimpleHTTPRequestHandler):
    server_version = "RainfallModelServer/5.4"

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: HTTPStatus) -> None:
        self.send_json({"error": message}, status=status)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self.send_json({"status": "ok", "server_version": self.server_version})
        if parsed.path == "/api/options":
            return self.send_json(APP_STATE.options())
        if parsed.path == "/api/current_weather":
            query = parse_qs(parsed.query)
            entity_id = (query.get("entity_id") or [""])[0]
            try:
                return self.send_json(APP_STATE.current_weather(entity_id))
            except KeyError as exc:
                return self.send_error_json(str(exc), HTTPStatus.BAD_REQUEST)
            except Exception as exc:
                return self.send_error_json(
                    f"Current weather failed: {exc}", HTTPStatus.INTERNAL_SERVER_ERROR
                )
        return self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/forecast_series":
            return self.send_error_json("Unknown endpoint", HTTPStatus.NOT_FOUND)
        content_length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            result = APP_STATE.forecast_series(
                entity_id=str(payload["entity_id"]),
                model_name=str(payload["model_name"]),
            )
        except KeyError as exc:
            return self.send_error_json(str(exc), HTTPStatus.BAD_REQUEST)
        except ValueError as exc:
            return self.send_error_json(str(exc), HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            return self.send_error_json(
                f"Forecast failed: {exc}", HTTPStatus.INTERNAL_SERVER_ERROR
            )
        return self.send_json(result)

    def serve_static(self, request_path: str) -> None:
        if request_path in {"/", ""}:
            relative_path = Path("index.html")
        else:
            relative_path = Path(unquote(request_path.lstrip("/")))
        target = (WEB_ROOT / relative_path).resolve()
        if not str(target).startswith(str(WEB_ROOT.resolve())):
            return self.send_error_json("Invalid static path", HTTPStatus.FORBIDDEN)
        if not target.exists() or not target.is_file():
            return self.send_error_json("File not found", HTTPStatus.NOT_FOUND)
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local rainfall forecast web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8007)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), RainfallRequestHandler)
    print(f"Rainfall web app: http://{args.host}:{args.port}/")
    print("Forecast series mode: select city + model, then predict the next 14 future days.")
    print("Press Ctrl+C to stop the server.")
    server.serve_forever()


if __name__ == "__main__":
    main()
