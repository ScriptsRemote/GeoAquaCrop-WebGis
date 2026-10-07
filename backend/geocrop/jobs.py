"""Job store and the single background worker that runs analyses.

One analysis runs at a time: preprocessing downloads are network-bound and the
simulation already uses every CPU, so running two at once only makes both
slower. Further jobs wait in the queue. Job state is mirrored to
``data/jobs/<id>/job.json`` so finished analyses survive a restart.
"""
from __future__ import annotations

import json
import queue
import threading
import time
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .i18n import fmt_duration, fmt_int, tr
from .settings import settings

STEP_KEYS = ("area", "soil", "crop_areas", "crop_calendar", "climate", "synthetic",
             "simulate", "results", "cleanup")


def step_label(key: str, lang: str = "pt") -> str:
    return tr(f"step.{key}", lang)


class Cancelled(Exception):
    pass


@dataclass
class Step:
    key: str
    label: str
    status: str = "pending"          # pending | running | done | skipped | error
    progress: float | None = None    # 0..1 when measurable
    message: str = ""
    msg_key: str | None = None        # translatable form of `message`
    msg_args: dict | None = None
    started: float | None = None
    finished: float | None = None


@dataclass
class Job:
    id: str
    params: dict
    created: str
    status: str = "queued"            # queued | running | done | error | cancelled
    steps: list = field(default_factory=list)
    log: list = field(default_factory=list)
    error: str | None = None
    result: dict | None = None
    started: float | None = None
    finished: float | None = None

    # ---- runtime only (not persisted) ----
    def __post_init__(self):
        self._cancel = threading.Event()
        self._lock = threading.Lock()
        self._last_save = 0.0

    @property
    def dir(self) -> Path:
        return settings.jobs_dir / self.id

    def to_dict(self, log_tail: int | None = 200) -> dict:
        d = {k: v for k, v in asdict(self).items()}
        d["steps"] = [asdict(s) if isinstance(s, Step) else s for s in self.steps]
        if log_tail is not None:
            d["log"] = self.log[-log_tail:]
        params = dict(d["params"])
        if params.get("api_token"):
            params["api_token"] = "••••"
        d["params"] = params
        return d

    def save(self, force: bool = False):
        now = time.time()
        if not force and now - self._last_save < 1.0:
            return
        self._last_save = now
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.dir / "job.json.tmp"
        tmp.write_text(json.dumps(self.to_dict(log_tail=None), ensure_ascii=False, default=str),
                       encoding="utf-8")
        tmp.replace(self.dir / "job.json")

    # ---- helpers used by the pipeline ----
    def write(self, text: str):
        for line in str(text).splitlines():
            line = line.rstrip()
            if line:
                with self._lock:
                    self.log.append(f"{datetime.now().strftime('%H:%M:%S')}  {line}")
                    if len(self.log) > 5000:
                        self.log = self.log[-4000:]
        self.save()

    def step(self, key) -> Step:
        for s in self.steps:
            if s.key == key:
                return s
        raise KeyError(key)

    @property
    def lang(self) -> str:
        return (self.params or {}).get("lang", "pt")

    def t(self, key, **kw) -> str:
        return tr(key, self.lang, **kw)

    def _set_msg(self, s: Step, msg):
        """msg is None, plain text, or (key, args) for a translatable message."""
        if msg is None:
            return
        if isinstance(msg, tuple):
            key, args = msg
            s.msg_key, s.msg_args = key, args
            shown = {}
            for k, v in args.items():
                if k in ("eta", "elapsed"):
                    v = fmt_duration(v, self.lang)
                elif k in ("n", "done", "ok", "failed", "area") and isinstance(v, int):
                    v = fmt_int(v, self.lang)
                shown[k] = v
            s.message = tr(key, self.lang, **shown)
        else:
            s.msg_key, s.msg_args, s.message = None, None, str(msg)

    def start_step(self, key, msg=None):
        self.check_cancel()
        s = self.step(key)
        s.status, s.started, s.progress = "running", time.time(), None
        s.message, s.msg_key, s.msg_args = "", None, None
        self._set_msg(s, msg)
        self.write(f"▶ {step_label(key, self.lang)}{(': ' + s.message) if s.message else ''}")
        self.save(force=True)

    def progress(self, key, fraction=None, msg=None):
        s = self.step(key)
        if fraction is not None:
            s.progress = max(0.0, min(1.0, float(fraction)))
        self._set_msg(s, msg)
        self.save()

    def finish_step(self, key, status="done", msg=None):
        s = self.step(key)
        s.status, s.finished = status, time.time()
        if status == "done":
            s.progress = 1.0
        self._set_msg(s, msg)
        mark = "✓" if status == "done" else "·"
        self.write(f"{mark} {step_label(key, self.lang)}{(': ' + s.message) if s.message else ''}")
        self.save(force=True)

    def cancelled(self) -> bool:
        return self._cancel.is_set()

    def check_cancel(self):
        if self._cancel.is_set():
            raise Cancelled()


class JobManager:
    def __init__(self):
        self.jobs: dict[str, Job] = {}
        self.queue: "queue.Queue[str]" = queue.Queue()
        self._worker = threading.Thread(target=self._loop, name="geocrop-jobs", daemon=True)
        self._load_existing()
        self._worker.start()

    def _load_existing(self):
        for f in sorted(settings.jobs_dir.glob("*/job.json")):
            try:
                raw = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            job = Job(id=raw["id"], params=raw.get("params", {}), created=raw.get("created", ""))
            job.status = raw.get("status", "error")
            job.steps = [Step(**{k: v for k, v in s.items() if k in Step.__dataclass_fields__})
                         for s in raw.get("steps", [])]
            job.log = raw.get("log", [])
            job.error = raw.get("error")
            job.result = raw.get("result")
            job.started, job.finished = raw.get("started"), raw.get("finished")
            if job.status in ("queued", "running"):       # interrupted by a restart
                job.status = "error"
                job.error = tr("err.restart", job.params.get("lang"))
            self.jobs[job.id] = job

    def create(self, params: dict, step_keys: list[str]) -> Job:
        job_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        job = Job(id=job_id, params=params,
                  created=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        job.steps = [Step(k, step_label(k, params.get("lang", "pt"))) for k in step_keys]
        self.jobs[job_id] = job
        job.save(force=True)
        self.queue.put(job_id)
        return job

    def cancel(self, job_id: str) -> Job:
        job = self.jobs[job_id]
        job._cancel.set()
        if job.status == "queued":
            job.status = "cancelled"
            job.finished = time.time()
            job.save(force=True)
        return job

    def queue_position(self, job_id: str) -> int:
        waiting = [j for j in self.jobs.values() if j.status == "queued"]
        waiting.sort(key=lambda j: j.created)
        ids = [j.id for j in waiting]
        return ids.index(job_id) + 1 if job_id in ids else 0

    def _loop(self):
        from .pipeline import run_job

        while True:
            job_id = self.queue.get()
            job = self.jobs.get(job_id)
            if job is None or job.status != "queued":
                continue
            job.status, job.started = "running", time.time()
            job.save(force=True)
            try:
                run_job(job)
                job.status = "done"
            except Cancelled:
                job.status = "cancelled"
                job.write(job.t("log.cancelled"))
                for s in job.steps:
                    if s.status == "running":
                        s.status = "error"
                        job._set_msg(s, ("msg.cancelled", {}))
            except Exception as exc:  # noqa: BLE001 — report everything to the user
                job.status = "error"
                job.error = f"{type(exc).__name__}: {exc}"
                job.write(traceback.format_exc())
                for s in job.steps:
                    if s.status == "running":
                        s.status = "error"
                        s.message = str(exc)[:300]
            finally:
                job.finished = time.time()
                job.save(force=True)


manager: JobManager | None = None


def get_manager() -> JobManager:
    global manager
    if manager is None:
        manager = JobManager()
    return manager
