# Southeast Asia Rainfall Forecast Project

Dự án này xây dựng bộ dữ liệu mưa hằng ngày cho 12 thành phố Đông Nam Á, xử lý dữ liệu đa nguồn, chọn target có kiểm chứng với station ground truth, huấn luyện mô hình dự báo mưa, và cung cấp một web app local để dự báo chuỗi mưa 14 ngày.

## Cấu Trúc Dự Án

```text
.
├── data/                         <- Dữ liệu raw, processed, model-ready, ground truth
├── models/                       <- Model đã train và metadata
├── notebooks/                    <- Notebook chạy pipeline từ 01 đến 07
├── reports/                      <- Báo cáo, bảng audit, hình ảnh EDA/modeling
├── scripts/                      <- Thư mục script phụ trợ nếu cần mở rộng
├── web_app/                      <- Web app dự báo mưa local
├── requirements.txt              <- Danh sách thư viện theo pip freeze
└── README.md                     <- Hướng dẫn chạy toàn bộ dự án
```

## Yêu Cầu

- Python: môi trường hiện tại dùng `Python 3.13.5`.
- Hệ điều hành khuyến nghị: Windows, vì file `requirements.txt` được freeze từ môi trường Windows.
- Internet:
  - Cần khi chạy lại notebook thu thập dữ liệu từ NASA POWER, Open-Meteo và NOAA GHCN-Daily.
  - Cần khi chạy web app để lấy NASA context và Open-Meteo forecast mới nhất.
- Không cần API key cho các nguồn dữ liệu đang dùng trong dự án.

## Cài Đặt Môi Trường

Mở terminal tại root project:

```bash
cd D:\DS\Project
```

Tạo virtual environment:

```bash
python -m venv .venv
```

Kích hoạt môi trường trên Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu dùng Command Prompt:

```bat
.\.venv\Scripts\activate.bat
```

Cài thư viện:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Nếu chỉ muốn chạy notebook trong VS Code, hãy chọn kernel là `.venv`. Nếu muốn chạy notebook bằng giao diện Jupyter trong browser mà môi trường chưa có Jupyter Lab, cài thêm:

```bash
python -m pip install jupyterlab
python -m jupyter lab
```

## Chạy Nhanh Web App

Nếu repo đã có sẵn dữ liệu processed và model trong `data/` + `models/`, bạn có thể chạy web app ngay mà không cần chạy lại notebook.

Cách 1: double-click file:

```text
web_app\start_web_app.bat
```

Cách 2: chạy thủ công:

```bash
python web_app/server.py --host 127.0.0.1 --port 8007
```

Sau đó mở:

```text
http://127.0.0.1:8007/
```

Web app dùng các artifact chính:

- `data/processed/model_ready/sea_rainfall_daily_2020_2025_model_ready_strict_forecast_X.csv`
- `data/processed/model_ready/sea_rainfall_daily_2020_2025_model_ready_targets_y.csv`
- `models/07_model_training/*.joblib`

## Chạy Lại Toàn Bộ Pipeline Từ A-Z

Chạy các notebook theo đúng thứ tự trong thư mục `notebooks/`. Mỗi notebook sẽ đọc output của bước trước và ghi artifact sang `data/`, `reports/`, hoặc `models/`.

### 01. Data Collection And Entity Resolution

Notebook:

```text
notebooks/01_data_collection.ipynb
```

Mục tiêu:

- Tải dữ liệu NASA POWER Daily API.
- Tải dữ liệu Open-Meteo Historical Weather API.
- Chuẩn hóa đơn vị đo.
- Thực hiện entity resolution theo tọa độ.
- Merge hai nguồn theo `entity_id + date`.

Entity resolution trong dự án là phương pháp rule-based nearest-coordinate matching: mỗi tọa độ nguồn trả về được map tới city canonical gần nhất trong bán kính 50 km bằng Haversine distance.

Output chính:

- `data/raw/sea_rainfall_daily_2020_2025_raw_api_responses.jsonl`
- `data/raw/sea_rainfall_daily_2020_2025_source_observations.csv`
- `data/raw/sea_rainfall_daily_2020_2025_entity_resolved.csv`
- `data/raw/sea_rainfall_daily_2020_2025_entity_registry.csv`
- `data/raw/sea_rainfall_daily_2020_2025_manifest.json`
- `reports/01_data_collection_report/`

### 02. Data Quality EDA

Notebook:

```text
notebooks/02_data_quality_eda.ipynb
```

Mục tiêu:

- Kiểm tra missing value, duplicate, coverage.
- Phân tích phân bố mưa theo thành phố/tháng/năm.
- So sánh mức độ agreement giữa NASA POWER và Open-Meteo.
- Tạo bảng và hình EDA.

Output chính:

- `reports/02_EDA_report/`

### 03. Preprocessing

Notebook:

```text
notebooks/03_preprocessing.ipynb
```

Mục tiêu:

- Tạo target candidates.
- Tạo lag features, rolling features, wet/dry spell features.
- Tạo calendar/location features.
- Chia temporal split train/validation/test.
- Xử lý imputation cho feature bị thiếu do temporal warm-up.

Output chính:

- `data/processed/sea_rainfall_daily_2020_2025_processed_features.csv`
- `reports/03_preprocessing/`

### 04. Processed Model Readiness EDA

Notebook:

```text
notebooks/04_processed_model_readiness_eda.ipynb
```

Mục tiêu:

- Audit lại dữ liệu processed trước khi đóng gói model-ready.
- Kiểm tra vai trò cột, target, split, uncertainty và leakage risk.

Output chính:

- `reports/04_processed_model_readiness_eda/`

### 05. Model-Ready Packaging

Notebook:

```text
notebooks/05_model_ready_packaging.ipynb
```

Mục tiêu:

- Tách X và y.
- Đảm bảo X chỉ chứa strict forecast features.
- Loại bỏ same-day target, same-day source uncertainty và các cột có leakage.
- Ghi schema cho feature và target.

Output chính:

- `data/processed/model_ready/sea_rainfall_daily_2020_2025_model_ready_strict_forecast_X.csv`
- `data/processed/model_ready/sea_rainfall_daily_2020_2025_model_ready_targets_y.csv`
- `reports/05_model_ready_packaging/`

### 06. Ground-Truth Target Selection

Notebook:

```text
notebooks/06_target_selection_eda_for_model_training.ipynb
```

Mục tiêu:

- Tải và xử lý NOAA GHCN-Daily station rainfall.
- Ghép station ground truth với entity-date.
- So sánh các target candidates trên train/validation.
- Chọn target tốt nhất cho model training.

Target được chọn:

```text
target_nasa_power_precipitation_mm
```

Output chính:

- `data/groundtruth/sea_station_rainfall_daily_2020_2025_station_observations.csv`
- `data/groundtruth/sea_station_rainfall_daily_2020_2025_entity_groundtruth.csv`
- `data/groundtruth/sea_station_rainfall_daily_2020_2025_station_registry.csv`
- `data/groundtruth/sea_station_rainfall_daily_2020_2025_manifest.json`
- `reports/06_groundtruth_target_selection/`

### 07. Model Training

Notebook:

```text
notebooks/07_model_training.ipynb
```

Mục tiêu:

- Train các model:
  - Hist Gradient Boosting
  - Gradient Boosting
  - MLP Neural Network
- Tune theo validation MAE.
- Đánh giá final trên test split.
- Lưu pipeline model và metadata.

Best model hiện tại:

```text
mlp_log
```

Output chính:

- `models/07_model_training/best_model_metadata.json`
- `models/07_model_training/*_pipeline.joblib`
- `reports/07_model_training/`

## Luồng Dữ Liệu Chính

```text
NASA POWER + Open-Meteo
        |
        v
01 data collection + entity resolution
        |
        v
02 EDA
        |
        v
03 preprocessing
        |
        v
04 readiness audit
        |
        v
05 model-ready X/y
        |
        v
06 target selection with NOAA station ground truth
        |
        v
07 model training
        |
        v
web_app local rainfall forecast
```

## Ghi Chú Về Leakage

Dự án tách rõ:

- `X`: feature dùng để train/predict, chỉ chứa thông tin strict forecast-safe.
- `y`: target candidates, tách riêng khỏi feature.
- NOAA station ground truth: chỉ dùng để chọn target, không dùng làm predictor.
- Test split: không dùng để chọn target hoặc tune hyperparameter.

Web app khi forecast nhiều ngày sẽ dùng rainfall history quan sát được cho ngày đầu tiên. Từ ngày thứ hai trở đi, app dùng prediction trước đó làm rainfall-memory input vì các ngày tương lai chưa có quan sát thật.

## Troubleshooting

Nếu thiếu model khi chạy web app:

```text
FileNotFoundError: Model file is missing
```

Hãy chạy lại `notebooks/07_model_training.ipynb`.

Nếu thiếu file X/y model-ready:

```text
Required input is missing
```

Hãy chạy lại từ `notebooks/03_preprocessing.ipynb` đến `notebooks/05_model_ready_packaging.ipynb`.

Nếu web app không mở được port `8007`, có thể đổi port:

```bash
python web_app/server.py --host 127.0.0.1 --port 8010
```

Nếu notebook tải dữ liệu lỗi do mạng, hãy kiểm tra internet rồi chạy lại cell bị lỗi. Các nguồn NASA POWER, Open-Meteo và NOAA GHCN-Daily không cần API key.

## Tài Liệu Chi Tiết

- Data collection: `reports/01_data_collection_report/DATA_COLLECTION_REPORT.md`
- EDA: `reports/02_EDA_report/EDA_CONCLUSIONS_AND_NEXT_STEPS.md`
- Preprocessing: `reports/03_preprocessing/PREPROCESSING_README.md`
- Model-ready package: `reports/05_model_ready_packaging/MODEL_READY_PACKAGE_SUMMARY.md`
- Ground-truth target selection: `reports/06_groundtruth_target_selection/GROUNDTRUTH_TARGET_SELECTION_CONCLUSIONS.md`
- Model training: `reports/07_model_training/MODEL_TRAINING_SUMMARY.md`
- Web app: `web_app/README.md`
