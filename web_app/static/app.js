const SVG_NS = "http://www.w3.org/2000/svg";

const state = {
  options: null,
  selectedEntityId: null,
};

const citySelect = document.getElementById("citySelect");
const modelSelect = document.getElementById("modelSelect");
const predictButton = document.getElementById("predictButton");
const countryLayer = document.getElementById("countryLayer");
const borderLayer = document.getElementById("borderLayer");
const mapLabels = document.getElementById("mapLabels");
const cityMarkers = document.getElementById("cityMarkers");
const statusChip = document.getElementById("statusChip");
const selectedCityTitle = document.getElementById("selectedCityTitle");
const forecastWindowLabel = document.getElementById("forecastWindowLabel");
const modelInputSummary = document.getElementById("modelInputSummary");
const currentWeatherStatus = document.getElementById("currentWeatherStatus");
const currentTemperature = document.getElementById("currentTemperature");
const currentCondition = document.getElementById("currentCondition");
const currentRain = document.getElementById("currentRain");
const currentHumidity = document.getElementById("currentHumidity");
const currentWind = document.getElementById("currentWind");
const currentProviderToday = document.getElementById("currentProviderToday");
const seriesTitle = document.getElementById("seriesTitle");
const seriesStatus = document.getElementById("seriesStatus");
const availableDays = document.getElementById("availableDays");
const meanRainfall = document.getElementById("meanRainfall");
const peakRainfall = document.getElementById("peakRainfall");
const wetDayRatio = document.getElementById("wetDayRatio");
const volatilityMetric = document.getElementById("volatilityMetric");
const dailySwing = document.getElementById("dailySwing");
const providerGap = document.getElementById("providerGap");
const trendSlope = document.getElementById("trendSlope");
const rainChart = document.getElementById("rainChart");
const sourceBreakdown = document.getElementById("sourceBreakdown");
const topPredictedDays = document.getElementById("topPredictedDays");
const comparisonBreakdown = document.getElementById("comparisonBreakdown");

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

const countryShapes = [
  {
    name: "Myanmar",
    fill: "#8ee6bd",
    label: [96.2, 21.2],
    polygons: [
      [
        [92.2, 27.8],
        [97.8, 28.1],
        [100.7, 24.3],
        [100.3, 19.4],
        [98.2, 16.2],
        [97.0, 12.2],
        [95.1, 13.7],
        [93.3, 17.1],
        [92.0, 22.1],
      ],
    ],
  },
  {
    name: "Thailand",
    fill: "#fff2a8",
    label: [101.0, 15.8],
    polygons: [
      [
        [97.4, 20.5],
        [101.8, 20.3],
        [105.5, 15.6],
        [104.4, 12.4],
        [101.6, 11.3],
        [100.1, 7.0],
        [98.7, 7.7],
        [99.1, 13.0],
        [97.5, 16.2],
      ],
    ],
  },
  {
    name: "Laos",
    fill: "#b9f3ff",
    label: [103.2, 18.4],
    polygons: [
      [
        [100.0, 22.5],
        [103.2, 22.0],
        [107.2, 18.9],
        [106.0, 15.1],
        [103.4, 14.3],
        [101.3, 16.9],
        [100.1, 20.1],
      ],
    ],
  },
  {
    name: "Cambodia",
    fill: "#ffb7cf",
    label: [104.5, 12.0],
    polygons: [
      [
        [102.2, 14.5],
        [106.7, 14.4],
        [107.6, 11.0],
        [105.1, 9.9],
        [102.5, 10.9],
      ],
    ],
  },
  {
    name: "Vietnam",
    fill: "#82d8ff",
    label: [107.6, 16.8],
    polygons: [
      [
        [104.4, 22.7],
        [106.9, 22.7],
        [109.0, 20.2],
        [108.2, 16.2],
        [109.4, 12.0],
        [106.7, 8.4],
        [104.8, 10.2],
        [106.2, 14.6],
        [105.3, 18.7],
      ],
    ],
  },
  {
    name: "Malaysia",
    fill: "#c8f7a8",
    label: [102.5, 4.1],
    polygons: [
      [
        [99.4, 7.2],
        [104.2, 6.7],
        [104.0, 1.0],
        [101.1, 1.1],
        [100.1, 4.5],
      ],
      [
        [109.6, 5.2],
        [116.7, 7.0],
        [119.4, 4.9],
        [117.0, 1.2],
        [111.1, 1.0],
      ],
    ],
  },
  {
    name: "Indonesia",
    fill: "#f3c6ff",
    label: [109.8, -4.8],
    polygons: [
      [
        [94.1, 5.6],
        [101.5, 4.6],
        [106.1, -1.2],
        [104.2, -5.2],
        [98.4, -4.1],
        [94.0, 0.2],
      ],
      [
        [105.2, -5.4],
        [113.8, -6.2],
        [115.2, -8.2],
        [107.2, -8.8],
      ],
      [
        [109.2, 1.6],
        [116.6, 3.5],
        [119.6, 0.1],
        [117.0, -4.2],
        [110.8, -3.5],
      ],
      [
        [119.2, 2.5],
        [123.8, 1.1],
        [124.8, -3.5],
        [121.2, -5.1],
        [119.0, -1.2],
      ],
      [
        [123.4, -8.0],
        [128.2, -8.4],
        [128.9, -10.6],
        [124.0, -10.2],
      ],
    ],
  },
  {
    name: "Philippines",
    fill: "#ffd19c",
    label: [122.4, 13.0],
    polygons: [
      [
        [119.5, 18.8],
        [122.0, 18.1],
        [123.6, 15.0],
        [121.0, 13.2],
        [119.0, 15.6],
      ],
      [
        [123.2, 13.0],
        [126.0, 11.5],
        [125.2, 7.0],
        [122.8, 6.0],
        [121.3, 9.5],
      ],
      [
        [120.2, 11.1],
        [122.3, 9.3],
        [121.0, 7.2],
        [118.6, 8.6],
      ],
    ],
  },
  {
    name: "Brunei",
    fill: "#fffbd1",
    label: [114.9, 5.8],
    polygons: [
      [
        [114.2, 5.3],
        [115.4, 5.3],
        [115.4, 4.4],
        [114.2, 4.4],
      ],
    ],
  },
  {
    name: "Timor-Leste",
    fill: "#ffc1a9",
    label: [125.6, -7.3],
    polygons: [
      [
        [124.2, -8.4],
        [127.5, -8.6],
        [127.1, -9.8],
        [124.5, -9.7],
      ],
    ],
  },
  {
    name: "Singapore",
    fill: "#f8fbff",
    label: [103.8, 2.3],
    polygons: [
      [
        [103.4, 1.6],
        [104.3, 1.6],
        [104.3, 1.1],
        [103.4, 1.1],
      ],
    ],
  },
];

const rainfallBands = [
  { min: 0, max: 1, label: "Rain unlikely", range: "0-1 mm", cssClass: "band-unlikely" },
  { min: 1, max: 10, label: "Light rain", range: "1-10 mm", cssClass: "band-light" },
  { min: 10, max: 25, label: "Moderate rain", range: "10-25 mm", cssClass: "band-moderate" },
  { min: 25, max: 50, label: "Heavy rain", range: "25-50 mm", cssClass: "band-heavy" },
  { min: 50, max: null, label: "Extreme rain", range: ">=50 mm", cssClass: "band-extreme" },
];

const cityLabelOffsets = {
  SEA_BN_BANDAR_SERI_BEGAWAN: { dx: 18, dy: -22, width: 168 },
  SEA_ID_JAKARTA: { dx: -104, dy: 22, width: 92 },
  SEA_KH_PHNOM_PENH: { dx: -122, dy: 24, width: 132 },
  SEA_LA_VIENTIANE: { dx: -116, dy: -18, width: 112 },
  SEA_MM_YANGON: { dx: -94, dy: 24, width: 86 },
  SEA_MY_KUALA_LUMPUR: { dx: -152, dy: -16, width: 148 },
  SEA_PH_MANILA: { dx: 20, dy: -18, width: 84 },
  SEA_SG_SINGAPORE: { dx: 18, dy: 18, width: 104 },
  SEA_TH_BANGKOK: { dx: 18, dy: 14, width: 92 },
  SEA_TL_DILI: { dx: 18, dy: -16, width: 58 },
  SEA_VN_HANOI: { dx: 20, dy: -20, width: 72 },
  SEA_VN_HO_CHI_MINH: { dx: 20, dy: 22, width: 152 },
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

function formatPctRaw(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return `${Number(value).toFixed(0)}%`;
}

function formatSignedMm(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  const numeric = Number(value);
  const sign = numeric > 0 ? "+" : "";
  return `${sign}${numeric.toFixed(2)} mm/day`;
}

function categoryLabel(category) {
  return category && category.label ? category.label : "--";
}

function cityById(entityId) {
  return state.options.cities.find((city) => city.entity_id === entityId);
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

function polygonPoints(points) {
  return points
    .map(([lon, lat]) => {
      const point = projectPoint(lat, lon);
      return `${point.x.toFixed(1)},${point.y.toFixed(1)}`;
    })
    .join(" ");
}

function createSvgElement(tag, attributes = {}) {
  const element = document.createElementNS(SVG_NS, tag);
  Object.entries(attributes).forEach(([key, value]) => {
    element.setAttribute(key, value);
  });
  return element;
}

function renderBaseMap() {
  countryLayer.innerHTML = "";
  borderLayer.innerHTML = "";
  mapLabels.innerHTML = "";

  countryShapes.forEach((country) => {
    country.polygons.forEach((polygon) => {
      const shape = createSvgElement("polygon", {
        points: polygonPoints(polygon),
        class: "country-shape",
        fill: country.fill,
      });
      const title = createSvgElement("title");
      title.textContent = country.name;
      shape.appendChild(title);
      countryLayer.appendChild(shape);

      const border = createSvgElement("polyline", {
        points: polygonPoints([...polygon, polygon[0]]),
        class: "country-border",
      });
      borderLayer.appendChild(border);
    });

    const [lon, lat] = country.label;
    const labelPoint = projectPoint(lat, lon);
    const label = createSvgElement("text", {
      x: labelPoint.x,
      y: labelPoint.y,
      class: "country-label",
      "text-anchor": "middle",
    });
    label.textContent = country.name;
    mapLabels.appendChild(label);
  });
}

function setSelectedCity(entityId) {
  state.selectedEntityId = entityId;
  citySelect.value = entityId;
  const city = cityById(entityId);
  selectedCityTitle.textContent = city
    ? `${city.location_name}, ${city.country}`
    : "Choose a city";
  document.querySelectorAll(".city-label-marker").forEach((marker) => {
    marker.classList.toggle("active", marker.dataset.entityId === entityId);
  });
  loadCurrentWeather(entityId);
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

  const windowInfo = state.options.forecast_window;
  forecastWindowLabel.textContent = `Future window: ${windowInfo.start} to ${windowInfo.end}`;

  renderBaseMap();
  renderMapCityLabels();
  renderFeatureSummary();

  if (state.options.cities.length > 0) {
    setSelectedCity(state.options.cities[0].entity_id);
  }
}

function renderFeatureSummary() {
  const summary = state.options.model_input_summary;
  modelInputSummary.innerHTML = `
    <p>${summary.plain_language}</p>
    <div class="feature-pill-grid">
      <span>${summary.feature_count} model inputs</span>
      <span>${summary.location_feature_count} location features</span>
      <span>${summary.calendar_feature_count} seasonal features</span>
      <span>${summary.rainfall_memory_feature_count} rainfall-memory features</span>
      <span>${summary.lookback_days}-day live observed lookback</span>
    </div>
  `;
}

function renderMapCityLabels() {
  cityMarkers.innerHTML = "";
  state.options.cities.forEach((city) => {
    const point = projectPoint(city.latitude, city.longitude);
    const offset = cityLabelOffsets[city.entity_id] || { dx: 16, dy: -16, width: 110 };
    const height = 28;
    const group = createSvgElement("g", {
      class: "city-label-marker",
      transform: `translate(${point.x.toFixed(1)} ${point.y.toFixed(1)})`,
      tabindex: "0",
      role: "button",
      "aria-label": `${city.location_name}, ${city.country}`,
    });
    group.dataset.entityId = city.entity_id;

    const connector = createSvgElement("line", {
      x1: "0",
      y1: "0",
      x2: offset.dx > 0 ? offset.dx : offset.dx + offset.width,
      y2: offset.dy,
      class: "city-connector",
    });
    const labelBox = createSvgElement("rect", {
      x: offset.dx,
      y: offset.dy - height / 2,
      width: offset.width,
      height,
      rx: "6",
      ry: "6",
      class: "city-label-box",
    });
    const labelText = createSvgElement("text", {
      x: offset.dx + 10,
      y: offset.dy + 5,
      class: "city-label-text",
    });
    labelText.textContent = city.location_name;

    group.append(connector, labelBox, labelText);
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

function setWeatherLoading(city) {
  currentWeatherStatus.textContent = city
    ? `${city.location_name}, ${city.country}`
    : "Loading weather";
  currentTemperature.textContent = "--";
  currentCondition.textContent = "Loading";
  currentRain.textContent = "--";
  currentHumidity.textContent = "--";
  currentWind.textContent = "--";
  currentProviderToday.textContent = "--";
}

async function loadCurrentWeather(entityId) {
  const city = cityById(entityId);
  setWeatherLoading(city);
  try {
    const response = await fetch(
      `/api/current_weather?entity_id=${encodeURIComponent(entityId)}`
    );
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Current weather request failed.");
    }
    currentWeatherStatus.textContent = `${payload.city.location_name}, ${payload.city.country} - ${payload.source}`;
    currentTemperature.textContent =
      payload.temperature_2m_c === null ? "--" : `${Number(payload.temperature_2m_c).toFixed(1)} C`;
    currentCondition.textContent = payload.weather_label || "--";
    currentRain.textContent = formatMm(payload.precipitation_mm);
    currentHumidity.textContent =
      payload.relative_humidity_2m_pct === null
        ? "--"
        : `${Number(payload.relative_humidity_2m_pct).toFixed(0)}%`;
    currentWind.textContent =
      payload.wind_speed_10m_kmh === null
        ? "--"
        : `${Number(payload.wind_speed_10m_kmh).toFixed(1)} km/h`;
    currentProviderToday.textContent = `${formatMm(
      payload.today_provider_precipitation_sum_mm
    )} / ${formatPctRaw(payload.today_provider_precipitation_probability_pct)}`;
  } catch (error) {
    currentWeatherStatus.textContent = "Current weather unavailable";
    currentCondition.textContent = error.message;
  }
}

function setLoading(isLoading) {
  predictButton.disabled = isLoading;
  predictButton.textContent = isLoading ? "Generating..." : "Generate forecast series";
  seriesStatus.textContent = isLoading ? "Fetching web inputs" : "Ready";
}

async function generateForecastSeries() {
  setLoading(true);
  try {
    const response = await fetch("/api/forecast_series", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entity_id: citySelect.value,
        model_name: modelSelect.value,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Forecast request failed.");
    }
    renderForecastResult(payload);
  } catch (error) {
    seriesStatus.textContent = "Error";
    seriesTitle.textContent = error.message;
    rainChart.innerHTML = "";
  } finally {
    setLoading(false);
  }
}

function renderForecastResult(payload) {
  const summary = payload.summary;
  const webComparison = payload.web_comparison_summary || {};
  const nasaComparison = payload.nasa_baseline_summary || {};
  seriesTitle.textContent = `${payload.city.location_name}, ${payload.city.country} - ${payload.model.label}`;
  seriesStatus.textContent = `${payload.forecast_window.start} to ${payload.forecast_window.end}`;
  availableDays.textContent = `${summary.available_days}/${summary.total_days}`;
  meanRainfall.textContent = formatMm(summary.mean_prediction_mm);
  peakRainfall.textContent =
    summary.max_prediction_mm === null
      ? "--"
      : `${formatMm(summary.max_prediction_mm)} on ${summary.max_prediction_date}`;
  wetDayRatio.textContent = formatPct(summary.wet_day_ratio);
  volatilityMetric.textContent = formatMm(summary.std_prediction_mm);
  dailySwing.textContent = formatMm(summary.mean_daily_change_mm);
  providerGap.textContent = formatMm(webComparison.mean_absolute_gap_mm);
  trendSlope.textContent = formatSignedMm(summary.trend_slope_mm_per_day);
  renderChart(payload.rows);
  renderSourceBreakdown(payload.input_sources, payload.provider_notes);
  renderTopDays(payload.rows);
  renderComparison(
    webComparison,
    nasaComparison,
    payload.web_forecast_source,
    payload.nasa_baseline_source
  );
}

function renderSourceBreakdown(sourceCounts, notes) {
  const cards = Object.entries(sourceCounts || {})
    .map(
      ([source, count]) => `
        <article class="provider-card">
          <strong>${source}</strong>
          <span>${count} day(s)</span>
        </article>
      `
    )
    .join("");
  const noteBlock =
    notes && notes.length
      ? `<article class="provider-card provider-error"><strong>Provider notes</strong><p>${notes.join(
          "<br>"
        )}</p></article>`
      : "";
  sourceBreakdown.innerHTML = cards || "<p>No source information returned.</p>";
  if (noteBlock) {
    sourceBreakdown.innerHTML += noteBlock;
  }
}

function renderComparison(webComparison, nasaComparison, webSource, nasaSource) {
  if (
    (!webComparison || !webComparison.paired_days) &&
    (!nasaComparison || !nasaComparison.paired_days)
  ) {
    comparisonBreakdown.innerHTML = "<p>No comparison overlap returned.</p>";
    return;
  }
  const card = (label, source, comparison) => {
    if (!comparison || !comparison.paired_days) {
      return `
        <article class="provider-card">
          <strong>${label}</strong>
          <span>No paired day(s)</span>
          <p>${source || "Unavailable"}</p>
        </article>
      `;
    }
    return `
      <article class="provider-card">
        <strong>${label}</strong>
        <span>${comparison.paired_days} paired day(s)</span>
        <p>${source}</p>
        <p>Mean: ${formatMm(comparison.mean_comparison_mm)}</p>
        <p>MAE gap: ${formatMm(comparison.mean_absolute_gap_mm)}</p>
        <p>Correlation: ${
          comparison.correlation === null || comparison.correlation === undefined
            ? "--"
            : Number(comparison.correlation).toFixed(3)
        }</p>
      </article>
    `;
  };
  comparisonBreakdown.innerHTML = `
    ${card("Web forecast", webSource, webComparison)}
    ${card("NASA seasonal baseline", nasaSource, nasaComparison)}
    <article class="provider-card">
      <strong>Reading the chart</strong>
      <span>Three separate references</span>
      <p>ML is your trained model. Web forecast is external. NASA baseline is historical seasonality, not a future forecast.</p>
    </article>
  `;
}

function renderTopDays(rows) {
  const topRows = rows
    .filter((row) => row.available)
    .sort((a, b) => b.prediction_mm - a.prediction_mm)
    .slice(0, 8);
  if (!topRows.length) {
    topPredictedDays.innerHTML = "<p>No available prediction rows.</p>";
    return;
  }
  topPredictedDays.innerHTML = topRows
    .map(
      (row) => `
        <article class="provider-card">
          <strong>${row.date}</strong>
          <span>${formatMm(row.prediction_mm)} - ${categoryLabel(
            row.prediction_category
          )}</span>
          <p>Web forecast: ${formatMm(row.web_forecast_mm)} / ${formatPctRaw(
        row.web_forecast_probability_pct
      )}</p>
          <p>NASA seasonal baseline: ${formatMm(row.nasa_baseline_mm)}</p>
        </article>
      `
    )
    .join("");
}

function buildPath(rows, valueGetter, xFor, yFor) {
  const parts = [];
  rows.forEach((row, index) => {
    const value = valueGetter(row);
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return;
    }
    const command = parts.length ? "L" : "M";
    parts.push(`${command} ${xFor(index).toFixed(2)} ${yFor(Number(value)).toFixed(2)}`);
  });
  return parts.join(" ");
}

function renderChart(rows) {
  const availableRows = rows.filter((row) => row.available);
  if (!availableRows.length) {
    rainChart.innerHTML =
      '<text x="40" y="80" class="chart-empty">No available prediction rows.</text>';
    return;
  }

  const width = 1120;
  const height = 420;
  const margin = { top: 34, right: 28, bottom: 54, left: 68 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const allValues = rows.flatMap((row) => {
    const values = [];
    if (row.available) {
      values.push(row.prediction_mm);
    }
    if (row.web_forecast_mm !== null && row.web_forecast_mm !== undefined) {
      values.push(row.web_forecast_mm);
    }
    if (row.nasa_baseline_mm !== null && row.nasa_baseline_mm !== undefined) {
      values.push(row.nasa_baseline_mm);
    }
    return values;
  });
  const maxValue = Math.max(5, ...allValues.map(Number));
  const yMax = Math.max(60, Math.ceil(maxValue / 5) * 5);
  const meanValue =
    availableRows.reduce((sum, row) => sum + row.prediction_mm, 0) /
    availableRows.length;

  const xFor = (index) =>
    margin.left + (index / Math.max(1, rows.length - 1)) * plotWidth;
  const yFor = (value) => margin.top + (1 - value / yMax) * plotHeight;
  const mlPath = buildPath(rows, (row) => (row.available ? row.prediction_mm : null), xFor, yFor);
  const webPath = buildPath(rows, (row) => row.web_forecast_mm, xFor, yFor);
  const nasaPath = buildPath(rows, (row) => row.nasa_baseline_mm, xFor, yFor);

  const bandMarkup = rainfallBands
    .map((band) => {
      const minValue = Math.max(0, band.min);
      const maxBandValue = Math.min(yMax, band.max === null ? yMax : band.max);
      if (maxBandValue <= 0 || minValue >= yMax) {
        return "";
      }
      const y = yFor(maxBandValue);
      const bandHeight = Math.max(1, yFor(minValue) - y);
      const labelY = y + Math.min(bandHeight - 4, Math.max(14, bandHeight / 2));
      return `
        <rect class="rain-band ${band.cssClass}" x="${margin.left}" y="${y}" width="${plotWidth}" height="${bandHeight}"></rect>
        <text class="rain-band-label" x="${margin.left + 10}" y="${labelY}">${band.label} (${band.range})</text>
      `;
    })
    .join("");

  const gridLines = [0, 0.25, 0.5, 0.75, 1]
    .map((fraction) => {
      const value = yMax * fraction;
      const y = yFor(value);
      return `
        <line class="chart-grid" x1="${margin.left}" y1="${y}" x2="${
        width - margin.right
      }" y2="${y}"></line>
        <text class="chart-label" x="18" y="${y + 4}">${value.toFixed(0)} mm</text>
      `;
    })
    .join("");

  const dateLabels = rows
    .filter((_, index) => index % 2 === 0 || index === rows.length - 1)
    .map((row) => {
      const index = rows.indexOf(row);
      return `<text class="chart-label" x="${xFor(index)}" y="${
        height - 20
      }" text-anchor="middle">${row.date.slice(5)}</text>`;
    })
    .join("");

  const meanLineY = yFor(meanValue);
  const lineEndLabel = (path, label, cssClass, yOffset = 0) => {
    if (!path) {
      return "";
    }
    const lastRowIndex = rows.length - 1;
    let lastValue = null;
    if (cssClass.includes("ml")) {
      lastValue = rows[lastRowIndex].prediction_mm;
    } else if (cssClass.includes("web")) {
      lastValue = rows[lastRowIndex].web_forecast_mm;
    } else {
      lastValue = rows[lastRowIndex].nasa_baseline_mm;
    }
    if (lastValue === null || lastValue === undefined) {
      return "";
    }
    return `<text class="line-end-label ${cssClass}" x="${width - margin.right - 92}" y="${
      yFor(lastValue) + yOffset
    }">${label}</text>`;
  };
  const points = availableRows
    .map((row) => {
      const index = rows.indexOf(row);
      return `<circle class="chart-point category-${row.prediction_category.code}" cx="${xFor(
        index
      )}" cy="${yFor(row.prediction_mm)}" r="4"><title>${row.date}: ${formatMm(
        row.prediction_mm
      )} - ${categoryLabel(row.prediction_category)}</title></circle>`;
    })
    .join("");

  rainChart.innerHTML = `
    <rect class="chart-bg" x="0" y="0" width="${width}" height="${height}"></rect>
    ${bandMarkup}
    ${gridLines}
    <line class="chart-axis" x1="${margin.left}" y1="${
    height - margin.bottom
  }" x2="${width - margin.right}" y2="${height - margin.bottom}"></line>
    <line class="chart-axis" x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${
    height - margin.bottom
  }"></line>
    <line class="chart-mean" x1="${margin.left}" y1="${meanLineY}" x2="${
    width - margin.right
  }" y2="${meanLineY}"></line>
    <text class="chart-label" x="${width - margin.right - 92}" y="${
    meanLineY - 8
  }">ML mean</text>
    <path class="chart-line nasa-chart-line" d="${nasaPath}"></path>
    <path class="chart-line web-chart-line" d="${webPath}"></path>
    <path class="chart-line ml-chart-line" d="${mlPath}"></path>
    ${lineEndLabel(mlPath, "ML", "ml-label", -8)}
    ${lineEndLabel(webPath, "Web", "web-label", 14)}
    ${lineEndLabel(nasaPath, "NASA", "nasa-label", 30)}
    ${points}
    ${dateLabels}
  `;
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
    seriesStatus.textContent = "Ready";
  } catch (error) {
    statusChip.textContent = "Server offline";
    seriesTitle.textContent = error.message;
  }
}

citySelect.addEventListener("change", () => setSelectedCity(citySelect.value));
predictButton.addEventListener("click", generateForecastSeries);

boot();
