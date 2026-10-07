// Leaflet map: basemaps, drawing, AOI, search outlines and the results grid.
import { t } from "./i18n.js";
import { $, fmt, esc } from "./util.js";

export const RAMPS = {
  green: ["#e4f1e1", "#c2e0bb", "#97ca8f", "#68ae62", "#3f9044", "#25712e", "#135220"],
  blue: ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
  orange: ["#fde4d4", "#f9c3a3", "#f39d6e", "#eb6834", "#c94f1f", "#9c3a14", "#6e280c"],
};

const AOI_STYLE = { color: "#ffd166", weight: 2.5, fillColor: "#ffd166", fillOpacity: 0.08 };
const CANDIDATE_STYLE = { color: "#ffffff", weight: 2, dashArray: "6 6", fill: false };

let map, drawn, aoiLayer, candidateLayer, cellsLayer, selectedLayer, drawHandler;
let cellRects = [];
let aoiRenderer;
let baseLayers = {}, labelsLayer, layersControl;
let handlers = {};

export function initMap(meta, h) {
  handlers = h;
  map = L.map("map", { zoomControl: false, preferCanvas: true, worldCopyJump: true }).setView([-15, -52], 4);
  L.control.zoom({ position: "bottomright" }).addTo(map);
  L.control.scale({ position: "bottomright", imperial: false }).addTo(map);

  baseLayers = {
    "bm.esri_sat": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, attribution: t("map.attr_esri") }),
    "bm.esri_topo": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, attribution: "© Esri" }),
    "bm.osm": L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: t("map.attr_osm") }),
    "bm.carto": L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", { maxZoom: 19, attribution: "© OpenStreetMap, © CARTO" }),
  };
  labelsLayer = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, pane: "overlayPane" });
  baseLayers["bm.esri_sat"].addTo(map);
  labelsLayer.addTo(map);
  buildLayersControl();
  applyDrawLocale();

  if (meta.google_maps_api_key) addGoogle(meta.google_maps_api_key);

  drawn = L.featureGroup().addTo(map);
  map.on(L.Draw.Event.CREATED, (e) => {
    stopDrawing();
    handlers.onDrawn?.(e.layer.toGeoJSON().geometry);
  });
  map.on("draw:drawstop", () => setDrawButtons(null));

  // results grid on its own pane; AOI outlines above it on an SVG pane that
  // never captures clicks (a canvas there would swallow clicks on the cells)
  map.createPane("cells").style.zIndex = 390;
  const aoiPane = map.createPane("aoi");
  aoiPane.style.zIndex = 420;
  aoiPane.style.pointerEvents = "none";
  aoiRenderer = L.svg({ pane: "aoi" });
  setupDrop();
  return map;
}

function buildLayersControl() {
  if (layersControl) map.removeControl(layersControl);
  const base = {};
  Object.entries(baseLayers).forEach(([k, layer]) => { base[t(k)] = layer; });
  layersControl = L.control.layers(base, { [t("bm.labels")]: labelsLayer }, { position: "topright", collapsed: true }).addTo(map);
}

function applyDrawLocale() {
  const h = L.drawLocal.draw.handlers;
  h.polygon.tooltip.start = t("draw.poly_start");
  h.polygon.tooltip.cont = t("draw.poly_cont");
  h.polygon.tooltip.end = t("draw.poly_end");
  h.polyline.error = t("draw.intersect");
  h.rectangle.tooltip.start = t("draw.rect_start");
  h.simpleshape.tooltip.end = t("draw.shape_end");
}

/** Re-label map controls after a language change. */
export function relabel() {
  if (!map) return;
  applyDrawLocale();
  buildLayersControl();
  const esri = baseLayers["bm.esri_sat"];
  if (esri && map.hasLayer(esri)) {
    map.attributionControl.removeAttribution(esri.options.attribution);
    esri.options.attribution = t("map.attr_esri");
    map.attributionControl.addAttribution(esri.options.attribution);
  }
}

function addGoogle(key) {
  // Official Google Maps JS API + GoogleMutant, only when a key is configured.
  const s = document.createElement("script");
  s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}`;
  s.async = true;
  s.onload = () => {
    const m = document.createElement("script");
    m.src = "https://unpkg.com/leaflet.gridlayer.googlemutant@0.14.1/dist/Leaflet.GoogleMutant.js";
    m.onload = () => { baseLayers["bm.google"] = L.gridLayer.googleMutant({ type: "hybrid", maxZoom: 21 }); buildLayersControl(); };
    document.head.appendChild(m);
  };
  document.head.appendChild(s);
}

// ------------------------------------------------------------------ drawing --
function setDrawButtons(kind) {
  $("#btn-draw-poly").setAttribute("aria-pressed", kind === "polygon");
  $("#btn-draw-rect").setAttribute("aria-pressed", kind === "rectangle");
}
export function startDrawing(kind) {
  stopDrawing();
  const opts = { shapeOptions: AOI_STYLE, showArea: false };
  drawHandler = kind === "rectangle" ? new L.Draw.Rectangle(map, opts) : new L.Draw.Polygon(map, { ...opts, allowIntersection: false });
  drawHandler.enable();
  setDrawButtons(kind);
}
export function stopDrawing() {
  if (drawHandler) { drawHandler.disable(); drawHandler = null; }
  setDrawButtons(null);
}

// ---------------------------------------------------------------------- AOI --
export function setAOI(geometry, { fit = true } = {}) {
  clearCandidate();
  if (aoiLayer) map.removeLayer(aoiLayer);
  aoiLayer = null;
  if (!geometry) return;
  aoiLayer = L.geoJSON(geometry, { style: AOI_STYLE, interactive: false, pane: "aoi", renderer: aoiRenderer }).addTo(map);
  if (fit) map.fitBounds(aoiLayer.getBounds(), { padding: [40, 40], maxZoom: 12 });
}
export function setAOIInteractive(on) {
  // keep the outline but let clicks reach the result cells underneath
  if (aoiLayer) aoiLayer.setStyle({ fillOpacity: on ? 0.08 : 0 });
}

export function showCandidate(item) {
  clearCandidate();
  if (item.geometry) {
    candidateLayer = L.geoJSON(item.geometry, { style: CANDIDATE_STYLE, interactive: false, pane: "aoi", renderer: aoiRenderer }).addTo(map);
    map.fitBounds(candidateLayer.getBounds(), { padding: [40, 40], maxZoom: 13 });
  } else if (item.bbox) {
    const [w, s, e, n] = item.bbox;
    map.fitBounds([[s, w], [n, e]], { padding: [40, 40], maxZoom: 14 });
  } else {
    map.setView([item.lat, item.lon], 11);
  }
}
export function clearCandidate() {
  if (candidateLayer) map.removeLayer(candidateLayer);
  candidateLayer = null;
}

// ------------------------------------------------------------- result grid --
export function setCells(mapData) {
  clearCells();
  const h = mapData.resolution / 2;
  const renderer = L.canvas({ pane: "cells", padding: 0.3 });
  cellsLayer = L.layerGroup().addTo(map);
  cellRects = mapData.cells.map(([id, x, y], k) => {
    const r = L.rectangle([[y - h, x - h], [y + h, x + h]], {
      renderer, pane: "cells", weight: 0, fillOpacity: 0.85, fillColor: "#999",
    });
    r._k = k;
    r.on("click", () => handlers.onCellClick?.(k));
    r.on("mouseover", () => r.setStyle({ weight: 1.5, color: "#ffffff" }));
    r.on("mouseout", () => r.setStyle({ weight: 0 }));
    r.addTo(cellsLayer);
    return r;
  });
  if (cellRects.length) {
    const b = L.featureGroup(cellRects).getBounds();
    if (!aoiLayer) map.fitBounds(b, { padding: [40, 40] });
  }
}

export function clearCells() {
  if (cellsLayer) map.removeLayer(cellsLayer);
  if (selectedLayer) map.removeLayer(selectedLayer);
  cellsLayer = selectedLayer = null;
  cellRects = [];
  $("#legend").hidden = true;
}

export function colorFor(value, range, ramp) {
  if (value === null || value === undefined) return null;
  const [lo, hi] = range;
  const t = hi > lo ? Math.min(1, Math.max(0, (value - lo) / (hi - lo))) : 0.5;
  const colors = RAMPS[ramp] || RAMPS.green;
  return colors[Math.min(colors.length - 1, Math.floor(t * colors.length))];
}

export function styleCells(values, range, ramp, opacity, labelFn) {
  cellRects.forEach((r, k) => {
    const v = values[k];
    const c = colorFor(v, range, ramp);
    r.setStyle({ fillColor: c || "#000", fillOpacity: c ? opacity : 0 });
    r.unbindTooltip();
    if (c) r.bindTooltip(labelFn(v, k), { className: "cell-tip", sticky: true, direction: "top" });
  });
}

export function selectCell(k, res) {
  if (selectedLayer) map.removeLayer(selectedLayer);
  const r = cellRects[k];
  if (!r) return;
  selectedLayer = L.rectangle(r.getBounds(), { color: "#ffd166", weight: 3, fill: false, interactive: false, pane: "aoi", renderer: aoiRenderer }).addTo(map);
}

export function renderLegend(title, units, range, ramp) {
  const colors = RAMPS[ramp] || RAMPS.green;
  const el = $("#legend");
  const steps = colors.length;
  const [lo, hi] = range;
  const tick = (t) => fmt(lo + (hi - lo) * t, Math.abs(hi - lo) < 10 ? 2 : 0);
  el.innerHTML = `<span class="lt">${esc(title)} <span style="font-weight:400;color:var(--ink-3)">(${esc(units)})</span></span>
    <div class="ramp" style="background:linear-gradient(to right, ${colors.map((c, i) => `${c} ${(i / steps) * 100}%, ${c} ${((i + 1) / steps) * 100}%`).join(",")})"></div>
    <div class="ticks"><span>≤ ${tick(0)}</span><span>${tick(0.5)}</span><span>≥ ${tick(1)}</span></div>`;
  el.hidden = false;
}

export function invalidate() { setTimeout(() => map && map.invalidateSize(), 260); }
export function getMap() { return map; }

// ---------------------------------------------------------------- drag-drop --
function setupDrop() {
  const wrap = $(".map-wrap");
  const hint = $("#drop-hint");
  let depth = 0;
  wrap.addEventListener("dragenter", (e) => { if (e.dataTransfer?.types?.includes("Files")) { depth++; hint.hidden = false; e.preventDefault(); } });
  wrap.addEventListener("dragover", (e) => { if (e.dataTransfer?.types?.includes("Files")) e.preventDefault(); });
  wrap.addEventListener("dragleave", () => { depth = Math.max(0, depth - 1); if (!depth) hint.hidden = true; });
  wrap.addEventListener("drop", (e) => {
    e.preventDefault(); depth = 0; hint.hidden = true;
    const f = e.dataTransfer.files?.[0];
    if (f) handlers.onFile?.(f);
  });
}
