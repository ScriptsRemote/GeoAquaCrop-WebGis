// Right sidebar: map layer controls, KPIs, charts, selected-cell series.
import { api } from "./api.js";
import { buildChart, legendHTML } from "./charts.js";
import { cropName, t, unitName, varName } from "./i18n.js";
import * as M from "./map.js";
import { openModal } from "./modal.js";
import { $, esc, fmt, fmtBig, fmtBytes } from "./util.js";

const FILE_INFO = {
  "seasons.csv": "files.seasons", "yield_grid.nc": "files.grid",
  "cells.geojson": "files.cells", "daily.nc": "files.daily",
};

let charts = [];
let st = null; // { job, map, varKey, year, opacity, cell }

function destroyCharts() { charts.forEach((c) => c.destroy()); charts = []; }

function setEmptyHeader() {
  $("#res-title").textContent = t("res.title");
  $("#res-sub").textContent = t("res.sub_empty");
}

export function clearResults() {
  destroyCharts();
  st = null;
  M.clearCells();
  $("#res-content").hidden = true;
  $("#res-content").innerHTML = "";
  $("#res-empty").hidden = false;
  setEmptyHeader();
  $("#btn-downloads").disabled = true;
}

export async function showResults(job) {
  const map = await api.map(job.id);
  destroyCharts();
  st = { job, map, varKey: "yield_dry", year: "mean", opacity: 0.85, cell: null };
  M.setCells(map);
  M.setAOIInteractive(false);
  renderAll();
  $("#res-empty").hidden = true;
  $("#res-content").hidden = false;
}

/** Re-render everything in the current language (after a language switch). */
export function rerenderResults() {
  if (!st) { setEmptyHeader(); return; }
  const cell = st.cell;
  destroyCharts();
  renderAll();
  if (cell !== null) onCellClick(cell, { scroll: false });
}

function renderAll() {
  const p = st.job.params;
  $("#res-title").textContent = `${cropName(p.crop)} · ${t(p.irrigation === "irrigated" ? "irr.irrigated_lc" : "irr.rainfed_lc")}`;
  $("#res-sub").textContent = `${p.aoi?.name || t("res.drawn")} · ${p.start_year}–${p.end_year} · ${fmt(p.resolution, 2)}° · ${t("res.cells", { n: fmt(st.job.result.n_ok, 0) })}`;
  renderDownloads(st.job);
  renderBody();
  applyLayer();
}

function renderDownloads(job) {
  const ul = $("#downloads");
  const files = job.result.files || {};
  ul.innerHTML = Object.entries(files).filter(([n]) => n !== "map.json").map(([n, size]) =>
    `<li><a href="${api.fileUrl(job.id, n)}" download><span>${esc(n)}</span><span class="sz">${fmtBytes(size)}</span><small>${esc(FILE_INFO[n] ? t(FILE_INFO[n]) : "")}</small></a></li>`).join("")
    + `<li><a href="/api/jobs/${job.id}/aoi" download="${job.id}_aoi.geojson"><span>aoi.geojson</span><span class="sz"></span><small>${esc(t("files.aoi"))}</small></a></li>`;
  $("#btn-downloads").disabled = false;
}

const weightingText = (w) => t(w === "crop_area" || String(w).includes("SPAM") ? "w.crop_area" : "w.cell_area");
const vLabel = (key) => varName(key, st.map.vars[key]?.label);
const vUnits = (key) => unitName(st.map.vars[key]?.units);

// ------------------------------------------------------------------ layout --
function renderBody() {
  const { job, map } = st;
  const r = job.result;
  const p = job.params;
  const varOpts = Object.keys(map.vars)
    .filter((k) => !(k === "irrigation_mm" && p.irrigation !== "irrigated"))
    .map((k) => `<option value="${k}">${esc(vLabel(k))}</option>`).join("");
  const yearOpts = `<option value="mean">${esc(t("res.mean_period"))}</option>` + map.years.map((y) => `<option value="${y}">${esc(t("res.season_n", { y }))}</option>`).join("");

  const notices = [];
  if (p.mode === "demo") notices.push(t("res.demo_notice"));
  const missing = r.missing_years || [];
  if (missing.length) notices.push(t("res.missing_years", { years: missing.join(", ") }));
  else if (r.note) notices.push(r.note);                      // analyses saved by older versions
  if (r.n_failed) notices.push(t("res.failed", { n: r.n_failed, total: r.n_cells,
    reasons: Object.entries(r.failure_reasons || {}).map(([k, v]) => `${k} (${v})`).join("; ") }));

  $("#res-content").innerHTML = `
    ${notices.map((n) => `<p class="notice">${esc(n)}</p>`).join("")}
    <div class="layer-controls" style="margin-top:12px">
      <label class="field wide"><span>${esc(t("res.var"))}</span><select id="r-var">${varOpts}</select></label>
      <label class="field"><span>${esc(t("res.season"))}</span><select id="r-year">${yearOpts}</select></label>
      <label class="field"><span>${esc(t("res.opacity"))}</span><span class="opacity"><input type="range" id="r-op" min="0.2" max="1" step="0.05" value="${st.opacity}"></span></label>
    </div>
    <div class="kpis" id="kpis"></div>
    <div id="cards"></div>
    <section class="card" id="cell-card">
      <div class="card-head"><h3>${esc(t("cell.title"))}</h3></div>
      <p class="cell-empty" id="cell-empty">${esc(t("cell.empty"))}</p>
      <div id="cell-content"></div>
    </section>
    <section class="card">
      <h3>${esc(t("about.title"))}</h3>
      <ul class="notes" id="about"></ul>
    </section>`;
  $("#r-var").value = st.varKey;
  $("#r-year").value = st.year;
  $("#r-var").onchange = (e) => { st.varKey = e.target.value; applyLayer(); renderCards(); };
  $("#r-year").onchange = (e) => { st.year = e.target.value; applyLayer(); renderKPIs(); renderCards(); };
  $("#r-op").oninput = (e) => { st.opacity = +e.target.value; applyLayer(); };
  renderKPIs();
  renderCards();
  renderAbout();
}

function layerValues(varKey, year) {
  const vals = st.map.values[varKey];
  if (!vals) return [];
  if (year !== "mean") return vals[year] || [];
  const ys = st.map.years.map(String);
  return st.map.cells.map((_, k) => {
    const xs = ys.map((y) => vals[y][k]).filter((v) => v !== null && v !== undefined);
    return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
  });
}

function applyLayer() {
  const meta = st.map.vars[st.varKey];
  const values = layerValues(st.varKey, st.year);
  const range = st.map.values[st.varKey]._range;
  const u = meta.units;
  const digits = u === "t" || u === "mm" || u === "dias" || u === "days" ? 0 : 2;
  M.styleCells(values, range, meta.ramp, st.opacity, (v, k) => {
    const [, x, y, area] = st.map.cells[k];
    return `<strong>${fmt(v, digits)} ${esc(vUnits(st.varKey))}</strong><br>${fmt(y, 3)}, ${fmt(x, 3)}${area ? `<br>${esc(t("res.cell_tip_area", { ha: fmt(area, 0) }))}` : ""}`;
  });
  M.renderLegend(`${vLabel(st.varKey)} · ${st.year === "mean" ? t("res.mean_short") : st.year}`, vUnits(st.varKey), range, meta.ramp);
}

// -------------------------------------------------------------------- KPIs --
function yearRows() {
  const rows = st.job.result.by_year;
  return st.year === "mean" ? rows : rows.filter((r) => String(r.year) === String(st.year));
}
const avg = (xs) => { const v = xs.filter((x) => x !== null && x !== undefined); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; };
const pick = (rows, key, f = "mean") => avg(rows.map((r) => (r[key] && typeof r[key] === "object" ? r[key][f] : r[key])));

function renderKPIs() {
  const rows = yearRows();
  const irrigated = st.job.params.irrigation === "irrigated";
  const scope = st.year === "mean" ? t("kpi.scope_mean", { n: rows.length }) : t("kpi.scope_one", { y: st.year });
  const kp = [
    { l: t("kpi.yield"), v: fmt(pick(rows, "yield_dry"), 2), u: "t/ha", d: scope },
    { l: t("kpi.gap"), v: fmt(pick(rows, "yield_gap"), 2), u: "t/ha", d: t("kpi.gap_d") },
    { l: t("kpi.et"), v: fmt(pick(rows, "et_mm"), 0), u: "mm", d: t("kpi.et_d", { p: fmt(pick(rows, "precip_mm"), 0) }) },
    { l: t("kpi.wp"), v: fmt(pick(rows, "wp_et"), 2), u: "kg/m³", d: t("kpi.wp_d") },
  ];
  const prod = pick(rows, "production_t");
  if (prod !== null) kp.push({ l: t("kpi.prod"), v: fmtBig(prod), u: "t", d: t("kpi.prod_d", { ha: fmtBig(pick(rows, "crop_area_ha")) }) });
  if (irrigated) kp.push({ l: t("kpi.irr"), v: fmt(pick(rows, "irrigation_mm"), 0), u: "mm", d: t("kpi.irr_d") });
  $("#kpis").innerHTML = kp.map((k) => `<div class="kpi"><div class="l">${esc(k.l)}</div><div><span class="v">${k.v}</span><span class="u">${k.u}</span></div><div class="d">${esc(k.d)}</div></div>`).join("");
}

// ------------------------------------------------------------------ charts --
function card(id, title, sub, spec, short = false) { return { id, title, sub, spec, short }; }

function domainSpecs() {
  const rows = st.job.result.by_year;
  const labels = rows.map((r) => String(r.year));
  const g = (k, f = "mean") => rows.map((r) => (r[k] ? r[k][f] : null));
  const irrigated = st.job.params.irrigation === "irrigated";
  const yieldSpec = {
    kind: "bar", labels, units: "t/ha", digits: 2, xLabel: t("ch.season"), yTitle: "t/ha",
    datasets: [
      { label: t("ch.yield_actual"), data: g("yield_dry"), color: "series-1" },
      { label: t("ch.yield_pot"), data: g("yield_pot"), color: "series-2", type: "line", points: true },
    ],
  };
  const waterSpec = {
    kind: "bar", labels, units: "mm", digits: 0, xLabel: t("ch.season"), yTitle: t("ch.water_axis"), stacked: true,
    datasets: [
      { label: t("ch.tr"), data: g("tr_mm"), color: "series-1", stack: "s" },
      { label: t("ch.es"), data: g("es_mm"), color: "series-2", stack: "s" },
      { label: t("ch.ro"), data: g("runoff_mm"), color: "series-3", stack: "s" },
      { label: t("ch.dp"), data: g("deep_perc_mm"), color: "series-4", stack: "s" },
      { label: t(irrigated ? "ch.rain_irr" : "ch.rain_season"), data: rows.map((r) => (r.precip_mm?.mean ?? 0) + (irrigated ? (r.irrigation_mm?.mean ?? 0) : 0)), color: "ink", type: "line", points: true, dashed: true },
    ],
  };
  const vals = layerValues(st.varKey, st.year).filter((v) => v !== null);
  const [lo, hi] = st.map.values[st.varKey]._range;
  const nb = 12;
  const w = (hi - lo) / nb || 1;
  const counts = new Array(nb).fill(0);
  vals.forEach((v) => { counts[Math.min(nb - 1, Math.max(0, Math.floor((v - lo) / w)))]++; });
  const dg = Math.abs(hi - lo) < 10 ? 1 : 0;
  const histSpec = {
    kind: "bar", units: t("ch.cells"), digits: 0, xLabel: `${vLabel(st.varKey)} (${vUnits(st.varKey)})`, yTitle: t("ch.cells"),
    labels: counts.map((_, i) => `${fmt(lo + i * w, dg)}–${fmt(lo + (i + 1) * w, dg)}`),
    datasets: [{ label: t("ch.cells_title"), data: counts, color: "series-3" }],
  };
  const when = st.year === "mean" ? t("ch.hist_when_mean") : t("kpi.scope_one", { y: st.year });
  return [
    card("c-yield", t("ch.yield"), t("ch.yield_sub", { w: weightingText(st.job.result.weighting) }), yieldSpec),
    card("c-water", t("ch.water"), t("ch.water_sub"), waterSpec),
    card("c-hist", t("ch.hist"), t("ch.hist_sub", { v: vLabel(st.varKey), when }), histSpec, true),
  ];
}

function mountCards(container, cards) {
  container.innerHTML = cards.map((c) => `
    <section class="card" id="${c.id}">
      <div class="card-head"><div><h3>${esc(c.title)}</h3></div>
        <button class="icon-btn" data-expand="${c.id}" aria-label="${esc(t("ch.expand", { t: c.title }))}">
          <svg viewBox="0 0 20 20"><path d="M12 3h5v5M8 17H3v-5M17 3l-6 6M3 17l6-6"/></svg></button></div>
      <p class="sub">${esc(c.sub)}</p>
      ${legendHTML(c.spec)}
      <div class="chart-box ${c.short ? "short" : ""}"><canvas></canvas></div>
    </section>`).join("");
  cards.forEach((c) => {
    const el = container.querySelector(`#${c.id}`);
    charts.push(buildChart(el.querySelector("canvas"), c.spec));
    el.querySelector("[data-expand]").onclick = () => openModal(c.title, c.sub, c.spec, `${st.job.id}_${c.id}.csv`);
  });
}

function renderCards() {
  charts = charts.filter((ch) => { if (ch.canvas.closest("#cards")) { ch.destroy(); return false; } return true; });
  mountCards($("#cards"), domainSpecs());
}

// ------------------------------------------------------------ cell series --
export async function onCellClick(k, { scroll = true } = {}) {
  if (!st) return;
  st.cell = k;
  M.selectCell(k);
  const [id, x, y, area] = st.map.cells[k];
  if (scroll) { $("#panel-right").dataset.collapsed = "false"; M.invalidate(); }
  $("#cell-empty").hidden = true;
  $("#cell-content").innerHTML = `<p class="sub">${esc(t("cell.loading", { id }))}</p>`;
  let d;
  try {
    d = await api.cell(st.job.id, id);
  } catch (e) {
    $("#cell-content").innerHTML = `<p class="error-box">${esc(e.message)}</p>`;
    return;
  }
  if (st.cell !== k) return;
  const start = new Date(d.start + "T00:00:00Z");
  const labels = d.series.season.map((_, i) => new Date(start.getTime() + i * 864e5).toISOString().slice(0, 10));
  const s = d.series;
  const inField = (arr) => arr.map((v, i) => (s.dap[i] >= 1 ? v : null));
  const date = t("ch.date");
  const ccSpec = { kind: "line", labels, xIsDate: true, units: "%", digits: 0, yTitle: "%", xLabel: date,
    datasets: [{ label: t("cell.cc"), data: inField(s.canopy_cover.map((v) => (v === null ? null : v * 100))), color: "series-3" }] };
  const bioSpec = { kind: "line", labels, xIsDate: true, units: "t/ha", digits: 2, yTitle: "t/ha", xLabel: date,
    datasets: [{ label: t("cell.bio"), data: inField(s.biomass.map((v) => (v === null ? null : v / 100))), color: "series-1" }] };
  const et = s.Tr.map((v, i) => (v === null || s.Es[i] === null ? null : v + s.Es[i]));
  const mmd = t("unit.mm_day");
  const wSpec = { kind: "bar", labels, xIsDate: true, units: mmd, digits: 1, yTitle: mmd, xLabel: date,
    datasets: [
      { label: t("cell.rain"), data: s.Precipitation, color: "series-1" },
      { label: t("cell.eta"), data: et, color: "series-2", type: "line" },
      { label: t("cell.et0"), data: s.ReferenceET, color: "ink", type: "line", dashed: true },
    ] };
  const wrSpec = { kind: "line", labels, xIsDate: true, units: "mm", digits: 0, yTitle: "mm", xLabel: date,
    datasets: [{ label: t("cell.wr"), data: s.Wr, color: "series-1" }] };
  if (st.job.params.irrigation === "irrigated") wSpec.datasets.splice(1, 0, { label: t("cell.irr"), data: s.IrrDay, color: "series-4" });

  const rowsHtml = st.map.years.map((yr) => {
    const v = (key) => st.map.values[key]?.[yr]?.[k];
    return `<tr><td>${yr}</td><td>${fmt(v("yield_dry"), 2)}</td><td>${fmt(v("yield_pot"), 2)}</td><td>${fmt(v("precip_mm"), 0)}</td><td>${fmt(v("et_mm"), 0)}</td><td>${fmt(v("wp_et"), 2)}</td></tr>`;
  }).join("");
  const th = ["ch.season", "cell.th_actual", "cell.th_pot", "cell.th_rain", "cell.th_et", "cell.th_wp"].map((key) => `<th>${esc(t(key))}</th>`).join("");

  $("#cell-content").innerHTML = `
    <p class="sub">${esc(t("cell.header", { id, lat: fmt(y, 3), lon: fmt(x, 3) }))}${area ? ` · ${esc(t("res.cell_tip_area", { ha: fmt(area, 0) }))}` : ""}</p>
    <div style="overflow-x:auto"><table class="data"><thead><tr>${th}</tr></thead><tbody>${rowsHtml}</tbody></table></div>
    <div id="cell-cards"></div>`;
  charts = charts.filter((ch) => { if (ch.canvas.closest("#cell-cards")) { ch.destroy(); return false; } return true; });
  mountCards($("#cell-cards"), [
    card("cc-cc", t("cell.cc"), t("cell.cc_sub"), ccSpec, true),
    card("cc-bio", t("cell.bio"), t("cell.bio_sub"), bioSpec, true),
    card("cc-water", t("cell.water"), t("cell.water_sub"), wSpec, true),
    card("cc-wr", t("cell.wr"), t("cell.wr_sub"), wrSpec, true),
  ]);
  if (scroll) $("#cell-card").scrollIntoView({ behavior: "smooth", block: "start" });
}

// ------------------------------------------------------------------- about --
function renderAbout() {
  const { job } = st;
  const p = job.params;
  const r = job.result;
  const demo = p.mode === "demo";
  const patches = [];
  if (p.patches?.soil_profile) patches.push(t("about.patch_soil"));
  if (p.patches?.co2_scenario) patches.push(t("about.patch_co2", { s: p.patches.co2_scenario.toUpperCase() }));
  const clim = demo ? t("about.synthetic") : p.climate_source === "agera5" ? "AgERA5 (Copernicus)"
    : `NASA NEX-GDDP-CMIP6 · ${p.climate?.nasanex_model} · ${p.climate?.nasanex_scenario}`;
  const syn = t("about.synthetic_short");
  const items = [
    t("about.sources", { clim, soil: demo ? syn : "SoilGrids 2.0", cal: demo ? syn : "GGCMI", area: demo ? syn : "SPAM" }),
    t("about.model"),
    t("about.dating"),
    t("about.weighting", { w: weightingText(r.weighting) }),
    t("about.seasonal"),
    patches.length ? t("about.patches", { list: patches.join("; ") }) : t("about.no_patches"),
    t("about.id", { id: job.id }),
  ];
  $("#about").innerHTML = items.map((x) => `<li>${esc(x)}</li>`).join("");
}
