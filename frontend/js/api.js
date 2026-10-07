// Thin wrappers around the GeoAquaCrop WebGIS backend.
import { getLang, t } from "./i18n.js";

async function request(method, url, body, isForm = false) {
  const opts = { method, headers: { "X-Lang": getLang() } };
  if (body !== undefined) {
    if (isForm) opts.body = body;
    else { opts.body = JSON.stringify(body); opts.headers["Content-Type"] = "application/json"; }
  }
  let res;
  try {
    res = await fetch(url, opts);
  } catch {
    throw new Error(t("api.offline"));
  }
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    let msg = data && data.detail ? data.detail : t("api.error", { status: res.status });
    if (Array.isArray(msg)) msg = msg.map((d) => d.msg).join("; ");
    throw new Error(msg);
  }
  return data;
}

export const api = {
  meta: () => request("GET", "/api/meta"),
  uploadAOI: (file) => { const f = new FormData(); f.append("file", file); return request("POST", "/api/aoi/upload", f, true); },
  geometryAOI: (geometry, name = "", source = "desenho") => request("POST", "/api/aoi/geometry", { geometry, name, source }),
  search: (q) => request("GET", `/api/search?q=${encodeURIComponent(q)}`),
  estimate: (body) => request("POST", "/api/estimate", body),
  createJob: (body) => request("POST", "/api/jobs", body),
  jobs: () => request("GET", "/api/jobs"),
  job: (id) => request("GET", `/api/jobs/${id}`),
  cancel: (id) => request("POST", `/api/jobs/${id}/cancel`),
  remove: (id) => request("DELETE", `/api/jobs/${id}`),
  map: (id) => request("GET", `/api/jobs/${id}/map`),
  aoi: (id) => request("GET", `/api/jobs/${id}/aoi`),
  cell: (id, cell) => request("GET", `/api/jobs/${id}/cell/${cell}`),
  cache: () => request("GET", "/api/cache"),
  clearCache: (scope) => request("DELETE", `/api/cache?scope=${scope}`),
  fileUrl: (id, name) => `/api/jobs/${id}/files/${name}`,
};
