// Small helpers shared by the modules.
import { locale } from "./i18n.js";

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const nf = (d) => new Intl.NumberFormat(locale(), { maximumFractionDigits: d, minimumFractionDigits: d });
export function fmt(v, d = 1) {
  if (v === null || v === undefined || Number.isNaN(v)) return "–";
  return nf(d).format(v);
}
export function fmtBig(v) {
  if (v === null || v === undefined) return "–";
  const a = Math.abs(v);
  const pt = locale() === "pt-BR";
  if (a >= 1e6) return `${fmt(v / 1e6, 2)} ${pt ? "mi" : "M"}`;
  if (a >= 1e4) return `${fmt(v / 1e3, 1)} ${pt ? "mil" : "k"}`;
  return fmt(v, 0);
}
export function fmtBytes(b) {
  if (!b) return "0 MB";
  if (b < 1e6) return `${fmt(b / 1e3, 0)} kB`;
  if (b < 1e9) return `${fmt(b / 1e6, 1)} MB`;
  return `${fmt(b / 1e9, 2)} GB`;
}
export function fmtDuration(s) {
  s = Math.max(0, Math.round(s));
  if (s < 60) return `${s} s`;
  if (s < 3600) return `${Math.round(s / 60)} min`;
  const h = Math.floor(s / 3600);
  return `${h} h ${String(Math.round((s % 3600) / 60)).padStart(2, "0")} min`;
}

export function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

let toastTimer;
export function toast(msg, { error = false, ms = 4200 } = {}) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.toggle("err", error);
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), ms);
}

export function downloadCSV(filename, header, rows) {
  const q = (v) => (v === null || v === undefined ? "" : /[",;\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : v);
  const text = [header.map(q).join(","), ...rows.map((r) => r.map(q).join(","))].join("\n");
  const blob = new Blob(["﻿" + text], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

export function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}
