const state = {
  options: null,
  selectedEntityId: null,
};

const citySelect = document.getElementById("citySelect");
const modelSelect = document.getElementById("modelSelect");
const dateInput = document.getElementById("dateInput");
const dateModeSelect = document.getElementById("dateModeSelect");
const dateHelper = document.getElementById("dateHelper");
const predictButton = document.getElementById("predictButton");
const cityMarkers = document.getElementById("cityMarkers");
const statusChip = document.getElementById("statusChip");
const selectedCityTitle = document.getElementById("selectedCityTitle");
const cityCoverage = document.getElementById("cityCoverage");
const predictionValue = document.getElementById("predictionValue");
const groundtruthValue = document.getElementById("groundtruthValue");
const errorValue = document.getElementById("errorValue");
const splitValue = document.getElementById("splitValue");
const stationValue = document.getElementById("stationValue");
const resultNote = document.getElementById("resultNote");

const mapBounds = {
  minLon: 88,
  maxLon: 131,
  minLat: -13,
  maxLat: 29,
  width: 920,
  height: 620,
  paddingX: 48,
  paddingY: 42,
};

function formatMm(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return `${Number(value).toFixed(2)} mm`;
}

function formatPct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function formatDistance(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return `${Number(value).toFixed(1)} km`;
}

function localTodayIso() {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Ho_Chi_Minh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });

  return formatter.format(new Date());
}

function addDaysIso(isoDate, days) {
  const date = new Date(`${isoDate}T00:00:00`);
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function projectPoint(latitude, longitude) {
  const usableWidth = mapBounds.width - mapBounds.paddingX * 2;
  const usableHeight = mapBounds.height - mapBounds.paddingY * 2;

  const x =
    ((longitude - mapBounds.minLon) / (mapBounds.maxLon - mapBounds.minLon)) *
      usableWidth +
    mapBounds.paddingX;

  const y =
    (1 - (latitude - mapBounds.minLat) / (mapBounds.maxLat - mapBounds.minLat)) *
      usableHeight +
    mapBounds.paddingY;

  return { x, y };
}

function cityById(entityId) {
  return state.options.cities.find((city) => city.entity_id === entityId);
}

function clearResult(note) {
  predictionValue.textContent = "--";
  groundtruthValue.textContent = "--";
  errorValue.textContent = "--";
  splitValue.textContent = "--";
  stationValue.textContent = "--";
  resultNote.textContent = note;
}

function setSelectedCity(entityId) {
  state.selectedEntityId = entityId;
  citySelect.value = entityId;

  const city = cityById(entityId);
  if (!city) {
    selectedCityTitle.textContent = "Choose a city";
    cityCoverage.textContent = "Ground truth coverage: --";
    return;
  }

  selectedCityTitle.textContent = `${city.location_name}, ${city.country}`;
  cityCoverage.textContent = `Ground truth coverage: ${formatPct(
    city.groundtruth_coverage
  )}`;

  document.querySelectorAll(".city-marker").forEach((marker) => {
    marker.classList.toggle("active", marker.dataset.entityId === entityId);
  });
}

function setDateMode(mode) {
  const today = state.options.today_local || localTodayIso();

  if (mode === "forecast") {
    const forecastMin = state.options.forecast_min || today;
    const forecastMax = state.options.forecast_max || addDaysIso(today, 365);

    dateInput.disabled = false;
    dateInput.min = forecastMin;
    dateInput.max = forecastMax;

    if (
      !dateInput.value ||
      dateInput.value < forecastMin ||
      dateInput.value > forecastMax
    ) {
      dateInput.value = forecastMin;
    }

    dateHelper.textContent = `Future forecast: chọn ngày từ ${forecastMin} đến ${forecastMax} theo múi giờ ${state.options.timezone}. Ngày tương lai chưa có ground truth quan sát thực tế.`;
  } else {
    dateInput.disabled = false;
    dateInput.min = state.options.date_min;
    dateInput.max = state.options.date_max;

    if (
      !dateInput.value ||
      dateInput.value < state.options.date_min ||
      dateInput.value > state.options.date_max
    ) {
      dateInput.value = state.options.date_max;
    }

    dateHelper.textContent = `Historical test: chọn ngày từ ${state.options.date_min} đến ${state.options.date_max}. Ground truth chỉ hiện nếu file station có dữ liệu cho city-date đó.`;
  }

  clearResult(
    `Mode changed to ${
      mode === "forecast" ? "future forecast" : "historical test"
    }.`
  );
}

function renderOptions() {
  citySelect.innerHTML = state.options.cities
    .map(
      (city) =>
        `<option value="${city.entity_id}">${city.location_name}, ${city.country}</option>`
    )
    .join("");

  modelSelect.innerHTML = state.options.models
    .map((model) => `<option value="${model.model_name}">${model.label}</option>`)
    .join("");

  renderMapMarkers();

  if (state.options.cities.length > 0) {
    setSelectedCity(state.options.cities[0].entity_id);
  }

  dateModeSelect.value = "forecast";
  setDateMode("forecast");
}

function renderMapMarkers() {
  cityMarkers.innerHTML = "";

  state.options.cities.forEach((city) => {
    const point = projectPoint(city.latitude, city.longitude);

    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.classList.add("city-marker");
    group.dataset.entityId = city.entity_id;
    group.setAttribute("transform", `translate(${point.x} ${point.y})`);
    group.setAttribute("tabindex", "0");
    group.setAttribute("role", "button");
    group.setAttribute("aria-label", `${city.location_name}, ${city.country}`);

    const halo = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    halo.setAttribute("class", "marker-halo");
    halo.setAttribute("r", "15");

    const circle = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "circle"
    );
    circle.setAttribute("r", "7");

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", "11");
    label.setAttribute("y", "4");
    label.textContent = city.location_name;

    group.append(halo, circle, label);

    group.addEventListener("click", () => setSelectedCity(city.entity_id));

    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setSelectedCity(city.entity_id);
      }
    });

    cityMarkers.appendChild(group);
  });
}

function setLoading(isLoading) {
  predictButton.disabled = isLoading;
  predictButton.textContent = isLoading ? "Predicting..." : "Predict rainfall";
}

async function predict() {
  setLoading(true);
  resultNote.textContent = "Running local model inference.";

  try {
    const response = await fetch("/api/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        entity_id: citySelect.value,
        date: dateInput.value,
        model_name: modelSelect.value,
      }),
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Prediction request failed.");
    }

    predictionValue.textContent = formatMm(payload.prediction_mm);

    groundtruthValue.textContent = payload.groundtruth.available
      ? formatMm(payload.groundtruth.groundtruth_precipitation_mm)
      : "missing";

    errorValue.textContent = formatMm(payload.absolute_error_vs_groundtruth);
    splitValue.textContent = payload.split || payload.prediction_mode;
    stationValue.textContent = formatDistance(
      payload.groundtruth.nearest_station_distance_km
    );

    const gtText = payload.groundtruth.available
      ? `Ground truth is available from ${
          payload.groundtruth.station_count || "station"
        } station record(s).`
      : payload.prediction_mode === "future"
      ? "Future dates do not have observed ground truth yet, so error is not computed."
      : "Ground truth is missing for this city-date, so error is not computed.";

    const sourceText =
      payload.prediction_mode === "future"
        ? ` Future mode reused the latest model-ready feature template from ${payload.feature_source_date} and patched calendar features.`
        : "";

    resultNote.textContent = `${payload.model_label} predicted ${formatMm(
      payload.prediction_mm
    )} for ${payload.location_name} on ${payload.date} (${
      payload.timezone
    }). ${gtText}${sourceText}`;
  } catch (error) {
    clearResult(error.message);
  } finally {
    setLoading(false);
  }
}

async function boot() {
  try {
    const response = await fetch("/api/options");

    if (!response.ok) {
      throw new Error("Cannot connect to the local prediction server.");
    }

    state.options = await response.json();

    renderOptions();
    statusChip.textContent = "Server ready";
  } catch (error) {
    statusChip.textContent = "Server offline";
    resultNote.textContent =
      "Open this page through the local Python server so the models can be loaded.";
  }
}

citySelect.addEventListener("change", () => setSelectedCity(citySelect.value));
dateModeSelect.addEventListener("change", () => setDateMode(dateModeSelect.value));
predictButton.addEventListener("click", predict);

boot();