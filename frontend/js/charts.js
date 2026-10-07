// Chart.js builders. Every chart is described by a plain "spec" so the same
// description renders in the sidebar card, in the expanded modal, and as a
// CSV/table — one source of truth per chart.
import { cssVar, fmt } from "./util.js";

export function themeColors() {
  return {
    ink: cssVar("--ink"), ink2: cssVar("--ink-2"), ink3: cssVar("--ink-3"),
    grid: cssVar("--grid"), surface: cssVar("--surface-1"),
    s1: cssVar("--series-1"), s2: cssVar("--series-2"), s3: cssVar("--series-3"), s4: cssVar("--series-4"),
    accent: cssVar("--accent"),
  };
}

function resolveColor(role, c) {
  return ({ "series-1": c.s1, "series-2": c.s2, "series-3": c.s3, "series-4": c.s4, ink: c.ink, ink3: c.ink3, accent: c.accent })[role] || role;
}

/**
 * spec = {
 *   kind: 'bar' | 'line',
 *   labels: [...],
 *   datasets: [{ label, data, color, type?, stack?, dashed?, points? }],
 *   yTitle, stacked, digits, xIsDate, beginAtZero
 * }
 */
export function buildChart(canvas, spec, { large = false } = {}) {
  const c = themeColors();
  Chart.defaults.font.family = '"Public Sans", system-ui, sans-serif';
  Chart.defaults.color = c.ink2;
  const datasets = spec.datasets.map((d) => {
    const col = resolveColor(d.color, c);
    const type = d.type || spec.kind;
    const base = { label: d.label, data: d.data, type, order: d.order ?? (type === "line" ? 0 : 1) };
    if (type === "bar") {
      return { ...base, backgroundColor: col, borderColor: c.surface, borderWidth: spec.stacked ? { top: 2 } : 0,
        borderRadius: spec.stacked ? 0 : { topLeft: 4, topRight: 4 }, borderSkipped: "bottom",
        stack: d.stack, maxBarThickness: large ? 64 : 34, categoryPercentage: 0.7, barPercentage: 0.9 };
    }
    return { ...base, borderColor: col, backgroundColor: col, borderWidth: 2, tension: 0,
      borderDash: d.dashed ? [5, 4] : [], pointRadius: d.points ? 4 : 0, pointHoverRadius: d.points ? 6 : 4,
      pointBorderColor: c.surface, pointBorderWidth: 2, spanGaps: !spec.xIsDate, fill: false };
  });
  const digits = spec.digits ?? 1;
  return new Chart(canvas, {
    type: spec.kind,
    data: { labels: spec.labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: c.surface, titleColor: c.ink, bodyColor: c.ink2, borderColor: c.grid, borderWidth: 1,
          padding: 10, boxPadding: 4, usePointStyle: true,
          callbacks: {
            title: (items) => spec.titleFn ? spec.titleFn(items[0].label) : items[0].label,
            label: (item) => `${item.dataset.label}: ${item.raw === null || item.raw === undefined ? "–" : fmt(item.raw, digits)}${spec.units ? " " + spec.units : ""}`,
          },
        },
      },
      scales: {
        x: {
          stacked: !!spec.stacked, grid: { display: false }, border: { color: c.grid },
          ticks: spec.xIsDate
            ? { maxTicksLimit: large ? 14 : 6, autoSkip: true, maxRotation: 0, callback(v) { const l = this.getLabelForValue(v); return l ? l.slice(5, 7) + "/" + l.slice(2, 4) : ""; } }
            : { maxRotation: 0, autoSkip: true },
        },
        y: {
          stacked: !!spec.stacked, beginAtZero: spec.beginAtZero ?? true,
          grid: { color: c.grid }, border: { display: false },
          title: { display: !!spec.yTitle, text: spec.yTitle, color: c.ink3, font: { size: 11 } },
          ticks: { callback: (v) => fmt(v, Math.abs(v) < 10 && v % 1 ? 1 : 0), maxTicksLimit: large ? 8 : 5 },
        },
      },
    },
  });
}

export function legendHTML(spec) {
  if (spec.datasets.length < 2) return "";
  const c = themeColors();
  return `<div class="legend-row">${spec.datasets.map((d) => {
    const col = resolveColor(d.color, c);
    const line = (d.type || spec.kind) === "line";
    return `<span><i class="${line ? "line" : ""}" style="background:${col}"></i>${d.label}</span>`;
  }).join("")}</div>`;
}

export function specToTable(spec) {
  const header = [spec.xLabel || "", ...spec.datasets.map((d) => `${d.label}${spec.units ? ` (${spec.units})` : ""}`)];
  const rows = spec.labels.map((l, i) => [l, ...spec.datasets.map((d) => d.data[i])]);
  return { header, rows };
}
