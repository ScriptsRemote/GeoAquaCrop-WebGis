// Expanded view of any chart: larger chart, data table and CSV download.
import { buildChart, legendHTML, specToTable } from "./charts.js";
import { t } from "./i18n.js";
import { $, downloadCSV, esc, fmt } from "./util.js";

let chart = null;

export function initModal() {
  const dlg = $("#modal");
  $("#modal-close").onclick = () => dlg.close();
  dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener("close", () => { if (chart) { chart.destroy(); chart = null; } });
  window.addEventListener("langchange", () => { if (dlg.open) dlg.close(); });
}

export function openModal(title, desc, spec, filename) {
  const dlg = $("#modal");
  $("#modal-title").textContent = title;
  $("#modal-desc").innerHTML = esc(desc) + legendHTML(spec);
  const { header, rows } = specToTable(spec);
  const digits = spec.digits ?? 1;
  const shown = rows.length > 1500 ? rows.filter((r) => r.slice(1).some((v) => v !== null && v !== 0)) : rows;
  $("#modal-table").innerHTML = `<table class="data"><thead><tr>${header.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead>
    <tbody>${shown.slice(0, 3000).map((r) => `<tr><td>${esc(r[0])}</td>${r.slice(1).map((v) => `<td>${fmt(v, digits)}</td>`).join("")}</tr>`).join("")}</tbody></table>
    ${shown.length > 3000 ? `<p class="hint">${esc(t("modal.rows", { n: fmt(shown.length, 0) }))}</p>` : ""}`;
  $("#modal-csv").onclick = () => downloadCSV(filename, header, rows);
  if (!dlg.open) dlg.showModal();
  if (chart) chart.destroy();
  chart = buildChart($("#modal-canvas"), spec, { large: true });
}
