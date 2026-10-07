// GeoAquaCrop WebGIS front end: guided steps on the left, map in the middle, results on the right.
import { api } from "./api.js";
import { applyDOM, cropName, getLang, initLang, setLang, sspName, stepMessage, stepName, t } from "./i18n.js";
import * as M from "./map.js";
import { initModal } from "./modal.js";
import { clearResults, onCellClick, rerenderResults, showResults } from "./results.js";
import { $, $$, debounce, esc, fmt, fmtBytes, fmtDuration, toast } from "./util.js";

const S = { meta: null, aoi: null, jobId: null, poll: null, lastJob: null, estimate: null };

// ------------------------------------------------------------------- boot --
async function boot() {
  initLang();
  try {
    S.meta = await api.meta();
  } catch (e) {
    toast(e.message, { error: true, ms: 10000 });
    return;
  }
  const m = S.meta;
  fillSelects();
  $("#in-ssp").value = "ssp245";
  const lastFull = m.years.agera5[1];
  $("#in-start").value = lastFull - 2;
  $("#in-end").value = lastFull;
  if (!m.real_mode_available) {
    $('input[name=mode][value=real]').disabled = true;
    $('input[name=mode][value=demo]').checked = true;
  }

  M.initMap(m, {
    onDrawn: (geom) => setAOIFromGeometry(geom, t("s1.drawn"), "draw"),
    onFile: uploadFile,
    onCellClick,
  });
  initModal();
  wireSteps();
  wireAOI();
  wireSearch();
  wireForm();
  wirePanels();
  wireCache();
  wireCredits();
  wireLanguage();
  refreshAll();
  await loadHistory(true);
}

function fillSelects() {
  const m = S.meta;
  const keep = (sel) => $(sel).value;
  const crop = keep("#in-crop"), res = keep("#in-res"), ssp = keep("#in-ssp"), model = keep("#in-model");
  $("#in-crop").innerHTML = m.crops.map((c) => `<option value="${c.id}">${esc(cropName(c.id))}</option>`).join("");
  $("#in-res").innerHTML = m.resolutions.map((r) => `<option value="${r}">${fmt(r, 2)}° (~${fmt(r * 111, r < 0.1 ? 1 : 0)} km)</option>`).join("");
  $("#in-model").innerHTML = m.nex_models.map((x) => `<option value="${x.id}" data-ens="${x.ensemble}">${x.id}</option>`).join("");
  $("#in-ssp").innerHTML = m.ssps.map((x) => `<option value="${x.id}">${esc(sspName(x.id))}</option>`).join("");
  if (crop) $("#in-crop").value = crop;
  if (res) $("#in-res").value = res;
  if (ssp) $("#in-ssp").value = ssp;
  if (model) $("#in-model").value = model;
}

// --------------------------------------------------------------- language --
function wireLanguage() {
  $$("[data-lang]").forEach((b) => b.addEventListener("click", () => setLang(b.dataset.lang)));
  window.addEventListener("langchange", async () => {
    fillSelects();
    M.relabel();
    if (S.aoi) showAOIInfo(S.aoi);
    refreshAll();
    await loadHistory();
    if (S.lastJob) renderProgress(S.lastJob);
    rerenderResults();
  });
}

// ------------------------------------------------------------------ steps --
function openStep(n) {
  $$(".step").forEach((li) => {
    const open = li.dataset.step === String(n);
    li.classList.toggle("is-open", open);
    li.querySelector(".step-head").setAttribute("aria-expanded", open);
  });
}
function wireSteps() {
  $$(".step-head").forEach((b) => b.addEventListener("click", () => {
    const li = b.closest(".step");
    if (li.classList.contains("is-open")) { li.classList.remove("is-open"); b.setAttribute("aria-expanded", false); }
    else openStep(li.dataset.step);
  }));
  openStep(1);
}

function mode() { return $('input[name=mode]:checked').value; }
function irrigation() { return $('input[name=irrigation]:checked').value; }
function climateSource() {
  const s = +$("#in-start").value, e = +$("#in-end").value;
  return s >= 1979 && e < S.meta.years.current ? "agera5" : "nex";
}
const irrLabel = (irr) => t(irr === "irrigated" ? "irr.irrigated_lc" : "irr.rainfed_lc");

function refreshAll() {
  if (!S.meta) return;
  // step 1
  const done1 = !!S.aoi;
  $('.step[data-step="1"]').classList.toggle("is-done", done1);
  $("#sum-1").textContent = done1 ? `${S.aoi.name || t("s1.unnamed")} · ${fmt(S.aoi.area_km2, 0)} km²` : t("s1.none");
  // step 2
  const irr = irrigation();
  $('.step[data-step="2"]').classList.toggle("is-done", done1);
  $("#sum-2").textContent = `${cropName($("#in-crop").value)} · ${irrLabel(irr)}`;
  $("#irr-hint").textContent = t(irr === "irrigated" ? "s2.hint_irrigated" : "s2.hint_rainfed");
  // step 3
  const s = +$("#in-start").value, e = +$("#in-end").value;
  const src = climateSource();
  const yearsOk = s && e && s <= e && s >= 1950 && e <= 2100;
  const isDemo = mode() === "demo";
  $("#agera5-box").hidden = isDemo || src !== "agera5";
  $("#nex-box").hidden = isDemo || src !== "nex";
  $("#source-box").innerHTML = !yearsOk ? t("s3.bad_period")
    : isDemo ? t("s3.src_demo", { s, e }) : src === "agera5" ? t("s3.src_agera5", { s, e }) : t("s3.src_nex", { s, e });
  $("#in-token").placeholder = t(S.meta.has_cds_token ? "s3.token_ph_set" : "s3.token_ph");
  $("#token-hint").textContent = t(S.meta.has_cds_token ? "s3.token_hint_set" : "s3.token_hint");
  const tokenOk = isDemo || src !== "agera5" || S.meta.has_cds_token || $("#in-token").value.trim().length > 30;
  $('.step[data-step="3"]').classList.toggle("is-done", done1 && yearsOk && tokenOk);
  $("#sum-3").textContent = yearsOk
    ? `${s}–${e} · ${isDemo ? t("s3.sum_synth") : src === "agera5" ? "AgERA5" : "CMIP6 " + $("#in-ssp").value} · ${fmt(+$("#in-res").value, 2)}°`
    : t("s3.sum_invalid");
  $("#in-co2").disabled = isDemo || src !== "nex";
  // step 4
  $("#mode-guide").textContent = t(isDemo ? "s4.guide_demo" : "s4.guide_real");
  const busy = S.poll !== null;
  let blocker = "";
  if (!done1) blocker = t("s4.block_area");
  else if (!yearsOk) blocker = t("s4.block_period");
  else if (!tokenOk) blocker = t("s4.block_token");
  else if (S.estimate?.over) blocker = S.estimate.overMsg();
  $("#run-blocker").textContent = blocker;
  $("#btn-run").disabled = !!blocker || busy;
  $("#btn-run").textContent = t(busy ? "s4.running" : "s4.run");
  if (!S.lastJob) $("#sum-4").textContent = "";
  updateEstimate();
}

const updateEstimate = debounce(async () => {
  const el = $("#estimate");
  if (!S.aoi) { el.textContent = t("s3.est_none"); el.classList.remove("is-over"); S.estimate = null; return; }
  try {
    const est = await api.estimate(jobBody());
    const isDemo = mode() === "demo";
    const over = isDemo ? est.cells > 3000 : est.over_limit;
    S.estimate = { over, overMsg: () => (isDemo ? t("s3.over_demo") : t("s3.over_real", { max: fmt(S.meta.max_cells, 0) })) };
    el.classList.toggle("is-over", over);
    el.innerHTML = t("s3.est", { cells: fmt(est.cells, 0), years: est.years, time: fmtDuration(est.simulation_seconds + 5), workers: est.workers })
      + (isDemo ? "." : `${t("s3.est_dl")}${est.climate_source === "agera5" ? t("s3.est_dl_cds") : ""}.`);
    $("#btn-run").disabled = over || !!$("#run-blocker").textContent || S.poll !== null;
  } catch { /* estimate is best effort */ }
}, 350);

// -------------------------------------------------------------------- AOI --
function warningText(aoi) {
  // the server sends keys too, so warnings follow the selected language
  if (aoi.warning_keys?.length) return aoi.warning_keys.map((w) => t(w.key, w.args || {}));
  return aoi.warnings || [];
}

function showAOIInfo(aoi) {
  $("#aoi-name").textContent = aoi.name || t("s1.unnamed");
  $("#aoi-area").textContent = `${fmt(aoi.area_km2, 0)} km²`;
  $("#aoi-parts").textContent = aoi.n_parts;
  const [w, s, e, n] = aoi.bbox;
  $("#aoi-extent").textContent = `${fmt(e - w, 2)}° × ${fmt(n - s, 2)}°`;
  $("#aoi-warnings").innerHTML = warningText(aoi).map((x) => `<li>${esc(x)}</li>`).join("");
}

function showAOI(aoi) {
  S.aoi = aoi;
  M.setAOI(aoi ? aoi.geometry : null);
  $("#aoi-card").hidden = !aoi;
  if (aoi) showAOIInfo(aoi);
  refreshAll();
}

async function setAOIFromGeometry(geom, name, source) {
  try {
    const aoi = await api.geometryAOI(geom, name, source);
    showAOI(aoi);
    toast(t("s1.set", { area: fmt(aoi.area_km2, 0) }));
  } catch (e) { toast(e.message, { error: true, ms: 8000 }); }
}

async function uploadFile(file) {
  toast(t("s1.reading", { name: file.name }));
  try {
    const aoi = await api.uploadAOI(file);
    showAOI(aoi);
    toast(t("s1.from_file", { name: file.name, area: fmt(aoi.area_km2, 0) }));
    openStep(1);
  } catch (e) { toast(e.message, { error: true, ms: 9000 }); }
}

function wireAOI() {
  $("#btn-draw-poly").onclick = () => { M.startDrawing("polygon"); toast(t("s1.draw_poly_hint")); closeMobile(); };
  $("#btn-draw-rect").onclick = () => { M.startDrawing("rectangle"); toast(t("s1.draw_rect_hint")); closeMobile(); };
  $("#btn-upload").addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("#file-input").click(); } });
  $("#file-input").onchange = (e) => { const f = e.target.files[0]; if (f) uploadFile(f); e.target.value = ""; };
  $("#btn-focus-search").onclick = () => { closeMobile(); $("#search-input").focus(); };
  $("#btn-aoi-clear").onclick = () => showAOI(null);
}

// ----------------------------------------------------------------- search --
function wireSearch() {
  const input = $("#search-input"), list = $("#search-results");
  let results = [];
  $("#search-form").onsubmit = async (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (q.length < 2) return;
    list.hidden = false;
    list.innerHTML = `<li class="muted">${esc(t("search.searching"))}</li>`;
    try {
      results = await api.search(q);
    } catch (err) {
      list.innerHTML = `<li class="muted">${esc(err.message)}</li>`;
      return;
    }
    if (!results.length) { list.innerHTML = `<li class="muted">${esc(t("search.none", { q }))}</li>`; return; }
    list.innerHTML = results.map((r, i) => `<li data-i="${i}" tabindex="0"><span>${esc(r.name)}</span>
      <span class="k">${esc(t(r.geometry ? "search.has_boundary" : "search.point_only"))}</span>
      ${r.geometry ? `<button class="btn btn-small use" data-use="${i}">${esc(t("search.use"))}</button>` : ""}</li>`).join("");
  };
  list.addEventListener("click", (e) => {
    const use = e.target.closest("[data-use]");
    const li = e.target.closest("li[data-i]");
    if (!li) return;
    const r = results[+li.dataset.i];
    if (use) {
      e.preventDefault();
      list.hidden = true;
      setAOIFromGeometry(r.geometry, r.name.split(",")[0], "search");
      return;
    }
    $$("li", list).forEach((x) => x.classList.toggle("is-active", x === li));
    M.showCandidate(r);
  });
  list.addEventListener("keydown", (e) => { if (e.key === "Enter") e.target.closest("li")?.click(); });
  document.addEventListener("click", (e) => { if (!e.target.closest("#search-form")) list.hidden = true; });
  input.addEventListener("keydown", (e) => { if (e.key === "Escape") { list.hidden = true; M.clearCandidate(); } });
  input.addEventListener("focus", () => { if (list.innerHTML) list.hidden = false; });
}

// ------------------------------------------------------------------- form --
function jobBody() {
  const model = $("#in-model");
  const src = climateSource();
  return {
    aoi: S.aoi || { geometry: null },
    mode: mode(),
    crop: $("#in-crop").value,
    irrigation: irrigation(),
    start_year: +$("#in-start").value,
    end_year: +$("#in-end").value,
    resolution: +$("#in-res").value,
    climate: { nasanex_model: model.value, nasanex_scenario: $("#in-ssp").value,
      nasanex_ensemble: model.selectedOptions[0]?.dataset.ens || "r1i1p1f1" },
    patches: { soil_profile: $("#in-soilfix").checked,
      co2_scenario: $("#in-co2").checked && src === "nex" && mode() === "real" ? $("#in-ssp").value : null },
    api_token: $("#in-token").value.trim(),
    keep_area_cache: $("#in-cache").checked,
    label: S.aoi?.name || "",
  };
}

function wireForm() {
  ["#in-crop", "#in-start", "#in-end", "#in-res", "#in-token", "#in-model", "#in-ssp", "#in-soilfix", "#in-co2", "#in-cache"]
    .forEach((s) => $(s).addEventListener("input", refreshAll));
  $$('input[name=irrigation], input[name=mode]').forEach((r) => r.addEventListener("change", refreshAll));
  $("#btn-run").onclick = runJob;
  $("#btn-cancel").onclick = async () => {
    if (!S.jobId) return;
    try { await api.cancel(S.jobId); toast(t("s4.cancelling")); } catch (e) { toast(e.message, { error: true }); }
  };
}

async function runJob() {
  try {
    const job = await api.createJob(jobBody());
    toast(t("s4.sent"));
    trackJob(job.id);
    loadHistory();
  } catch (e) { toast(e.message, { error: true, ms: 9000 }); }
}

// --------------------------------------------------------------- progress --
function trackJob(id) {
  S.jobId = id;
  clearInterval(S.poll);
  openStep(4);
  $("#progress").hidden = false;
  const tick = async () => {
    let job;
    try { job = await api.job(id); } catch { return; }
    renderProgress(job);
    if (["done", "error", "cancelled"].includes(job.status)) {
      clearInterval(S.poll);
      S.poll = null;
      refreshAll();
      loadHistory();
      if (job.status === "done") {
        $('.step[data-step="4"]').classList.add("is-done");
        await openResults(job);
      }
    }
  };
  S.poll = setInterval(tick, 1500);
  refreshAll();
  tick();
}

const statusText = (st) => t(`status.${st}`);
function renderProgress(job) {
  S.lastJob = job;
  $("#job-status").textContent = statusText(job.status) + (job.status === "queued" && job.queue_position ? t("status.position", { n: job.queue_position }) : "");
  $("#btn-cancel").hidden = !["queued", "running"].includes(job.status);
  $("#sum-4").textContent = statusText(job.status);
  $("#pipeline").innerHTML = job.steps.map((s) => {
    const bar = s.status === "running"
      ? `<div class="bar ${s.progress === null ? "indeterminate" : ""}"><i style="width:${(s.progress || 0) * 100}%"></i></div>` : "";
    return `<li data-status="${s.status}"><span class="dot"></span><span>${esc(stepName(s.key, s.label))}<span class="msg">${esc(stepMessage(s, fmt, fmtDuration))}</span>${bar}</span></li>`;
  }).join("") + (job.error ? `<li><span></span><span class="error-box">${esc(job.error)}</span></li>` : "");
  const pre = $("#log");
  const atBottom = pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 20;
  pre.textContent = (job.log || []).join("\n");
  if (atBottom) pre.scrollTop = pre.scrollHeight;
}

async function openResults(job) {
  try {
    await showResults(job);
    $("#panel-right").dataset.collapsed = "false";
    $("#btn-open-results").hidden = true;
    M.invalidate();
    $$(".history-item").forEach((li) => li.classList.toggle("is-active", li.dataset.id === job.id));
  } catch (e) { toast(t("res.open_failed", { err: e.message }), { error: true }); }
}

// ---------------------------------------------------------------- history --
async function loadHistory(resume = false) {
  let jobs = [];
  try { jobs = await api.jobs(); } catch { return; }
  const ul = $("#history-list");
  if (!jobs.length) { ul.innerHTML = `<li class="empty">${esc(t("hist.empty"))}</li>`; return; }
  ul.innerHTML = jobs.map((j) => {
    const chip = j.status === "done" ? "ok" : j.status === "error" ? "err" : "";
    return `<li class="history-item ${j.id === S.jobId ? "is-active" : ""}" data-id="${j.id}" tabindex="0">
      <span class="t">${esc(cropName(j.crop))} · ${esc(j.label || t("hist.area"))}</span>
      <span class="s">${j.start_year}–${j.end_year} · ${esc(irrLabel(j.irrigation))} ·
        <span class="chip ${chip}">${esc(statusText(j.status))}</span>${j.mode === "demo" ? ` <span class="chip demo">demo</span>` : ""}</span>
      <button class="icon-btn del" data-del="${j.id}" aria-label="${esc(t("hist.delete"))}"><svg viewBox="0 0 20 20"><path d="M5 6h10M8 6V4h4v2m-6 0 1 10h6l1-10"/></svg></button>
    </li>`;
  }).join("");
  $$(".history-item", ul).forEach((li) => {
    li.addEventListener("click", (e) => { if (!e.target.closest("[data-del]")) openJob(li.dataset.id); });
    li.addEventListener("keydown", (e) => { if (e.key === "Enter") openJob(li.dataset.id); });
  });
  $$("[data-del]", ul).forEach((b) => b.addEventListener("click", async () => {
    const id = b.dataset.del;
    if (!confirm(t("hist.confirm"))) return;
    try {
      await api.remove(id);
      if (S.jobId === id) { clearResults(); $("#progress").hidden = true; S.jobId = null; S.lastJob = null; }
      loadHistory();
    } catch (e) { toast(e.message, { error: true }); }
  }));
  if (resume) {
    const active = jobs.find((j) => ["queued", "running"].includes(j.status));
    if (active) trackJob(active.id);
  }
}

async function openJob(id) {
  const job = await api.job(id);
  S.jobId = id;
  if (job.params?.aoi?.geometry) showAOI(job.params.aoi);
  restoreForm(job.params);
  if (["queued", "running"].includes(job.status)) { trackJob(id); return; }
  $("#progress").hidden = false;
  renderProgress(job);
  if (job.status === "done") await openResults(job);
  else { clearResults(); openStep(4); }
  closeMobile();
}

function restoreForm(p) {
  if (!p) return;
  $("#in-crop").value = p.crop;
  $(`input[name=irrigation][value=${p.irrigation}]`).checked = true;
  $(`input[name=mode][value=${p.mode}]`).checked = true;
  $("#in-start").value = p.start_year;
  $("#in-end").value = p.end_year;
  $("#in-res").value = String(p.resolution);
  if (p.climate) { $("#in-model").value = p.climate.nasanex_model; $("#in-ssp").value = p.climate.nasanex_scenario; }
  $("#in-soilfix").checked = !!p.patches?.soil_profile;
  $("#in-co2").checked = !!p.patches?.co2_scenario;
  $("#in-cache").checked = p.keep_area_cache !== false;
  refreshAll();
}

// ----------------------------------------------------------------- panels --
function closeMobile() { $("#panel-left").classList.remove("is-open"); }
function wirePanels() {
  $$("[data-open-panel]").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.openPanel === "left") $("#panel-left").classList.add("is-open");
    else { $("#panel-right").dataset.collapsed = "false"; $("#btn-open-results").hidden = true; M.invalidate(); }
  }));
  $$("[data-close-panel]").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.closePanel === "left") closeMobile();
    else { $("#panel-right").dataset.collapsed = "true"; $("#btn-open-results").hidden = false; M.invalidate(); }
  }));
  const dl = $("#btn-downloads"), menu = $("#downloads");
  dl.onclick = (e) => { e.stopPropagation(); menu.hidden = !menu.hidden; dl.setAttribute("aria-expanded", !menu.hidden); };
  document.addEventListener("click", (e) => { if (!e.target.closest(".menu")) { menu.hidden = true; dl.setAttribute("aria-expanded", false); } });
}

// ------------------------------------------------------- cache & credits --
function wireCache() {
  const dlg = $("#cache-modal");
  $("#cache-close").onclick = () => dlg.close();
  $("#btn-cache").onclick = async () => { await renderCache(); dlg.showModal(); };
  window.addEventListener("langchange", () => { if (dlg.open) renderCache(); });
}
async function renderCache() {
  const c = await api.cache();
  $("#cache-body").innerHTML = `
    <p class="guide">${esc(t("cache.guide"))}</p>
    <dl>
      <dt>${esc(t("cache.global"))}</dt><dd>${fmtBytes(c.global_bytes)}</dd>
      <dt>${esc(t("cache.areas", { n: c.areas }))}</dt><dd>${fmtBytes(c.areas_bytes)}</dd>
      <dt>${esc(t("cache.tmp"))}</dt><dd>${fmtBytes(c.tmp_bytes)}</dd>
    </dl>
    <p class="hint">${esc(t("cache.folder", { path: c.path }))}</p>
    <div class="actions">
      <button class="btn btn-small" data-scope="areas">${esc(t("cache.clear_areas"))}</button>
      <button class="btn btn-small" data-scope="global">${esc(t("cache.clear_global"))}</button>
      <button class="btn btn-small" data-scope="all">${esc(t("cache.clear_all"))}</button>
    </div>`;
  $$("#cache-body [data-scope]").forEach((b) => b.onclick = async () => {
    try { await api.clearCache(b.dataset.scope); toast(t("cache.cleared")); renderCache(); } catch (e) { toast(e.message, { error: true }); }
  });
}
function wireCredits() {
  const dlg = $("#credits-modal");
  $("#btn-credits").onclick = () => dlg.showModal();
  $("#credits-close").onclick = () => dlg.close();
  dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
}

boot();
