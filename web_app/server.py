from __future__ import annotations

import argparse
import json
import math
import mimetypes
from datetime import datetime, timedelta
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = Path(__file__).resolve().parent
APP_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
FORECAST_HORIZON_DAYS = 365

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
GROUNDTRUTH_PATH = (
    PROJECT_ROOT
    / "data"
    / "groundtruth"
    / "sea_station_rainfall_daily_2020_2025_entity_groundtruth.csv"
)

TARGET_COLUMN = "target_nasa_power_precipitation_mm"
PREDICTION_CAP_MM = 500.0

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


def _to_json_value(value):
    if value is None or pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating, float)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
        return float(value)

    return value


def _load_required_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required input is missing: {path}")

    return pd.read_csv(path, **kwargs)


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col

    return None


class RainfallAppState:
    def __init__(self) -> None:
        self.x = _load_required_csv(X_PATH, parse_dates=["date"])
        self.y = _load_required_csv(Y_PATH, parse_dates=["date"])
        self.groundtruth = _load_required_csv(GROUNDTRUTH_PATH, parse_dates=["date"])

        self.groundtruth_value_col = _first_existing_column(
            self.groundtruth,
            [
                "groundtruth_precipitation_mm",
                "station_groundtruth_precipitation_mm",
                "precipitation_mm",
                "rainfall_mm",
            ],
        )

        if self.groundtruth_value_col is None:
            raise KeyError("Ground-truth file has no supported precipitation column.")

        self.groundtruth_station_count_col = _first_existing_column(
            self.groundtruth,
            [
                "groundtruth_station_count",
                "station_count",
                "n_stations",
            ],
        )

        self.groundtruth_distance_col = _first_existing_column(
            self.groundtruth,
            [
                "nearest_station_distance_km",
                "station_distance_km",
                "nearest_distance_km",
            ],
        )

        self.groundtruth_method_col = _first_existing_column(
            self.groundtruth,
            [
                "groundtruth_method",
                "method",
                "aggregation_method",
            ],
        )

        self.feature_columns = ["entity_id"] + [
            col for col in self.x.columns if col.startswith("feature_")
        ]

        self.x["date_key"] = self.x["date"].dt.strftime("%Y-%m-%d")
        self.y["date_key"] = self.y["date"].dt.strftime("%Y-%m-%d")
        self.groundtruth["date_key"] = self.groundtruth["date"].dt.strftime("%Y-%m-%d")

        self.feature_index = self.x.set_index(["entity_id", "date_key"], drop=False)
        self.target_index = self.y.set_index(["entity_id", "date_key"], drop=False)
        self.groundtruth_index = self.groundtruth.set_index(
            ["entity_id", "date_key"], drop=False
        )

        self.latest_feature_by_entity = (
            self.x.sort_values("date")
            .groupby("entity_id", sort=False)
            .tail(1)
            .set_index("entity_id", drop=False)
        )

        self.models = {}
        for model_name, model_info in MODEL_FILES.items():
            model_path = model_info["path"]

            if not model_path.exists():
                raise FileNotFoundError(f"Model file is missing: {model_path}")

            self.models[model_name] = joblib.load(model_path)

        self.cities = self._build_city_payload()

    def _build_city_payload(self) -> list[dict]:
        city_rows = (
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

        agg_spec = {
            "groundtruth_days": ("has_groundtruth", "sum"),
            "total_days": ("has_groundtruth", "size"),
        }

        if self.groundtruth_distance_col:
            agg_spec["nearest_station_distance_km"] = (
                self.groundtruth_distance_col,
                "min",
            )

        coverage = (
            self.groundtruth.assign(
                has_groundtruth=self.groundtruth[self.groundtruth_value_col].notna()
            )
            .groupby("entity_id")
            .agg(**agg_spec)
            .reset_index()
        )

        coverage["groundtruth_coverage"] = (
            coverage["groundtruth_days"] / coverage["total_days"]
        )

        if "nearest_station_distance_km" not in coverage.columns:
            coverage["nearest_station_distance_km"] = np.nan

        city_rows = city_rows.merge(coverage, on="entity_id", how="left")
        city_rows = city_rows.sort_values(["country", "location_name"])

        return [
            {
                "entity_id": row.entity_id,
                "country": row.country,
                "location_name": row.location_name,
                "latitude": _to_json_value(row.feature_canonical_latitude),
                "longitude": _to_json_value(row.feature_canonical_longitude),
                "groundtruth_coverage": _to_json_value(row.groundtruth_coverage),
                "nearest_station_distance_km": _to_json_value(
                    row.nearest_station_distance_km
                ),
            }
            for row in city_rows.itertuples(index=False)
        ]

    def options(self) -> dict:
        today = datetime.now(APP_TIMEZONE).date()
        forecast_max = today + timedelta(days=FORECAST_HORIZON_DAYS)

        return {
            "models": [
                {
                    "model_name": model_name,
                    "label": MODEL_FILES[model_name]["label"],
                }
                for model_name in MODEL_FILES
            ],
            "cities": self.cities,
            "date_min": self.x["date_key"].min(),
            "date_max": self.x["date_key"].max(),
            "today_local": today.strftime("%Y-%m-%d"),
            "forecast_min": today.strftime("%Y-%m-%d"),
            "forecast_max": forecast_max.strftime("%Y-%m-%d"),
            "forecast_horizon_days": FORECAST_HORIZON_DAYS,
            "timezone": "Asia/Ho_Chi_Minh",
            "target_column": TARGET_COLUMN,
            "prediction_cap_mm": PREDICTION_CAP_MM,
        }

    def _get_feature_row(
        self,
        entity_id: str,
        date_key: str,
    ) -> tuple[pd.Series, str, str | None]:
        if (entity_id, date_key) in self.feature_index.index:
            feature_row = self.feature_index.loc[(entity_id, date_key)]

            if isinstance(feature_row, pd.DataFrame):
                feature_row = feature_row.iloc[0]

            return feature_row.copy(), "historical", None

        requested_date = pd.to_datetime(date_key, errors="raise").date()
        today = datetime.now(APP_TIMEZONE).date()
        forecast_max = today + timedelta(days=FORECAST_HORIZON_DAYS)

        if requested_date < today:
            raise KeyError(
                f"No historical model-ready feature row for {entity_id} on {date_key}. "
                f"Switch to Future forecast for dates from {today:%Y-%m-%d}, "
                f"or choose a historical date that exists in the dataset."
            )

        if requested_date > forecast_max:
            raise ValueError(
                f"Future forecast is limited to {FORECAST_HORIZON_DAYS} days ahead "
                f"({forecast_max:%Y-%m-%d})."
            )

        if entity_id not in self.latest_feature_by_entity.index:
            raise KeyError(f"No model-ready feature row for entity {entity_id}")

        feature_row = self.latest_feature_by_entity.loc[entity_id].copy()
        source_date = _to_json_value(feature_row["date"])

        self._patch_calendar_features(feature_row, requested_date)

        feature_row["date"] = pd.Timestamp(requested_date)
        feature_row["date_key"] = date_key
        feature_row["split"] = "future_forecast"

        return feature_row, "future", source_date

    def _patch_calendar_features(self, row: pd.Series, requested_date) -> None:
        updates = {
            "feature_year": requested_date.year,
            "feature_month": requested_date.month,
            "feature_day": requested_date.day,
            "feature_dayofyear": requested_date.timetuple().tm_yday,
            "feature_day_of_year": requested_date.timetuple().tm_yday,
            "feature_dayofweek": requested_date.weekday(),
            "feature_day_of_week": requested_date.weekday(),
            "feature_quarter": (requested_date.month - 1) // 3 + 1,
        }

        for col, value in updates.items():
            if col in row.index:
                row[col] = value

        month_angle = 2 * math.pi * requested_date.month / 12
        doy_angle = 2 * math.pi * requested_date.timetuple().tm_yday / 366

        cyclical_updates = {
            "feature_month_sin": math.sin(month_angle),
            "feature_month_cos": math.cos(month_angle),
            "feature_dayofyear_sin": math.sin(doy_angle),
            "feature_dayofyear_cos": math.cos(doy_angle),
            "feature_day_of_year_sin": math.sin(doy_angle),
            "feature_day_of_year_cos": math.cos(doy_angle),
        }

        for col, value in cyclical_updates.items():
            if col in row.index:
                row[col] = value

    def _groundtruth_payload(
        self,
        entity_id: str,
        date_key: str,
    ) -> tuple[dict, float | None]:
        groundtruth = {
            "available": False,
            "groundtruth_precipitation_mm": None,
            "station_count": None,
            "nearest_station_distance_km": None,
            "method": None,
        }

        if (entity_id, date_key) not in self.groundtruth_index.index:
            return groundtruth, None

        gt_row = self.groundtruth_index.loc[(entity_id, date_key)]

        if isinstance(gt_row, pd.DataFrame):
            gt_row = gt_row.iloc[0]

        gt_value = _to_json_value(gt_row[self.groundtruth_value_col])

        groundtruth = {
            "available": gt_value is not None,
            "groundtruth_precipitation_mm": gt_value,
            "station_count": _to_json_value(gt_row[self.groundtruth_station_count_col])
            if self.groundtruth_station_count_col
            else None,
            "nearest_station_distance_km": _to_json_value(
                gt_row[self.groundtruth_distance_col]
            )
            if self.groundtruth_distance_col
            else None,
            "method": _to_json_value(gt_row[self.groundtruth_method_col])
            if self.groundtruth_method_col
            else None,
        }

        return groundtruth, gt_value

    def predict(self, entity_id: str, date_key: str, model_name: str) -> dict:
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        feature_row, prediction_mode, feature_source_date = self._get_feature_row(
            entity_id,
            date_key,
        )

        model_input = feature_row[self.feature_columns].to_frame().T

        log_prediction = np.asarray(
            self.models[model_name].predict(model_input),
            dtype=float,
        )

        max_log = np.log1p(PREDICTION_CAP_MM)

        log_prediction = np.nan_to_num(
            log_prediction,
            nan=0.0,
            posinf=max_log,
            neginf=0.0,
        )

        prediction_mm = float(
            np.clip(
                np.expm1(np.clip(log_prediction[0], 0, max_log)),
                0,
                PREDICTION_CAP_MM,
            )
        )

        selected_target_mm = None

        if (entity_id, date_key) in self.target_index.index:
            target_row = self.target_index.loc[(entity_id, date_key)]

            if isinstance(target_row, pd.DataFrame):
                target_row = target_row.iloc[0]

            selected_target_mm = _to_json_value(target_row[TARGET_COLUMN])

        groundtruth, gt_value = self._groundtruth_payload(entity_id, date_key)

        absolute_error_vs_groundtruth = None
        if gt_value is not None:
            absolute_error_vs_groundtruth = abs(prediction_mm - gt_value)

        return {
            "model_name": model_name,
            "model_label": MODEL_FILES[model_name]["label"],
            "entity_id": entity_id,
            "country": feature_row["country"],
            "location_name": feature_row["location_name"],
            "date": date_key,
            "timezone": "Asia/Ho_Chi_Minh",
            "prediction_mode": prediction_mode,
            "feature_source_date": feature_source_date,
            "split": feature_row["split"],
            "prediction_mm": prediction_mm,
            "selected_target_mm": selected_target_mm,
            "groundtruth": groundtruth,
            "absolute_error_vs_groundtruth": _to_json_value(
                absolute_error_vs_groundtruth
            ),
        }


APP_STATE = RainfallAppState()


class RainfallRequestHandler(SimpleHTTPRequestHandler):
    server_version = "RainfallModelServer/1.2"

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _send_json(
        self,
        payload: dict,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message: str, status: HTTPStatus) -> None:
        self._send_json({"error": message}, status=status)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            return self._send_json({"status": "ok"})

        if path == "/api/options":
            return self._send_json(APP_STATE.options())

        return self._serve_static(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path != "/api/predict":
            return self._send_error_json("Unknown endpoint", HTTPStatus.NOT_FOUND)

        content_length = int(self.headers.get("Content-Length", "0"))

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))

            entity_id = str(payload["entity_id"])
            date_key = str(payload["date"])
            model_name = str(payload["model_name"])

            result = APP_STATE.predict(entity_id, date_key, model_name)

        except KeyError as exc:
            return self._send_error_json(str(exc), HTTPStatus.BAD_REQUEST)

        except ValueError as exc:
            return self._send_error_json(str(exc), HTTPStatus.BAD_REQUEST)

        except Exception as exc:
            return self._send_error_json(
                f"Prediction failed: {exc}",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return self._send_json(result)

    def _serve_static(self, request_path: str) -> None:
        if request_path in {"/", ""}:
            relative_path = Path("index.html")
        else:
            relative_path = Path(unquote(request_path.lstrip("/")))

        target = (WEB_ROOT / relative_path).resolve()

        if not str(target).startswith(str(WEB_ROOT.resolve())):
            return self._send_error_json("Invalid static path", HTTPStatus.FORBIDDEN)

        if not target.exists() or not target.is_file():
            return self._send_error_json("File not found", HTTPStatus.NOT_FOUND)

        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        body = target.read_bytes()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local rainfall model web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8007)

    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), RainfallRequestHandler)

    print(f"Rainfall web app: http://{args.host}:{args.port}/")
    print("Press Ctrl+C to stop the server.")

    server.serve_forever()


if __name__ == "__main__":
    main()