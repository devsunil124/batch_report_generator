"""In-app library: stores uploaded .ndax files and caches parsed metadata.

Files live in ./library/ndax/. A JSON catalog at ./library/catalog.json holds
per-cell metadata (cycle count, started date, sizes, parse status) so the home
page renders instantly without re-parsing every file.

Parsing runs in a background thread and updates the catalog on completion.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import threading
import time
import traceback
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Callable, Optional

from data_loader import load_and_analyze


LIB_DIR = os.path.abspath("library")
NDAX_DIR = os.path.join(LIB_DIR, "ndax")
CATALOG_PATH = os.path.join(LIB_DIR, "catalog.json")


def _ensure_dirs() -> None:
    os.makedirs(NDAX_DIR, exist_ok=True)


def _natural_key(s: str):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]


@dataclass
class CellEntry:
    name: str
    filename: str          # basename inside NDAX_DIR
    size_bytes: int
    uploaded_at: str       # iso
    status: str = "pending"   # pending | parsing | ready | error
    error: str = ""
    cycle_count: int = 0
    cycle_min: int = 0
    cycle_max: int = 0
    started_at: str = ""      # iso of earliest Timestamp
    peak_dchg_ah: float = 0.0
    peak_dchg_cycle: int = 0
    max_coulombic_eff: float = 0.0
    max_energy_eff: float = 0.0
    last_analyzed: str = ""   # iso

    @property
    def path(self) -> str:
        return os.path.join(NDAX_DIR, self.filename)


class Library:
    """Singleton in-memory catalog backed by catalog.json."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cells: dict[str, CellEntry] = {}
        self._listeners: list[Callable[[], None]] = []
        self._load()

    # ── persistence ─────────────────────────────────────────────────────────
    def _load(self) -> None:
        _ensure_dirs()
        if not os.path.exists(CATALOG_PATH):
            self._cells = {}
            return
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._cells = {
                name: CellEntry(**entry) for name, entry in data.items()
                if os.path.exists(os.path.join(NDAX_DIR, entry.get("filename", "")))
            }
        except Exception:
            self._cells = {}

    def _save_unlocked(self) -> None:
        _ensure_dirs()
        tmp = CATALOG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({k: asdict(v) for k, v in self._cells.items()}, f, indent=2)
        os.replace(tmp, CATALOG_PATH)

    # ── observers ───────────────────────────────────────────────────────────
    def subscribe(self, fn: Callable[[], None]) -> None:
        if fn not in self._listeners:
            self._listeners.append(fn)

    def unsubscribe(self, fn: Callable[[], None]) -> None:
        if fn in self._listeners:
            self._listeners.remove(fn)

    def _notify(self) -> None:
        for fn in list(self._listeners):
            try:
                fn()
            except Exception:
                traceback.print_exc()

    # ── queries ─────────────────────────────────────────────────────────────
    def list_cells(self) -> list[CellEntry]:
        with self._lock:
            cells = list(self._cells.values())
        cells.sort(key=lambda c: _natural_key(c.name))
        return cells

    def get(self, name: str) -> Optional[CellEntry]:
        with self._lock:
            return self._cells.get(name)

    def ready_cells(self) -> list[CellEntry]:
        return [c for c in self.list_cells() if c.status == "ready"]

    # ── ingest ──────────────────────────────────────────────────────────────
    def add_file(self, src_path: str, original_name: str | None = None) -> CellEntry:
        """Copy a file into the library and queue it for parsing."""
        _ensure_dirs()
        if not os.path.exists(src_path):
            raise FileNotFoundError(src_path)
        base = original_name or os.path.basename(src_path)
        if not base.lower().endswith(".ndax"):
            raise ValueError(f"Not an .ndax file: {base}")

        name = os.path.splitext(base)[0]
        target_base = base
        target_path = os.path.join(NDAX_DIR, target_base)
        n = 1
        while os.path.exists(target_path):
            n += 1
            target_base = f"{name}_{n}.ndax"
            target_path = os.path.join(NDAX_DIR, target_base)

        if os.path.abspath(src_path) != os.path.abspath(target_path):
            shutil.copy2(src_path, target_path)

        final_name = os.path.splitext(target_base)[0]
        entry = CellEntry(
            name=final_name,
            filename=target_base,
            size_bytes=os.path.getsize(target_path),
            uploaded_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            status="pending",
        )
        with self._lock:
            self._cells[final_name] = entry
            self._save_unlocked()
        self._notify()
        self._kick_parse(final_name)
        return entry

    def add_bytes(self, content: bytes, original_name: str) -> CellEntry:
        """Save uploaded bytes into the library and queue for parsing."""
        _ensure_dirs()
        if not original_name.lower().endswith(".ndax"):
            raise ValueError(f"Not an .ndax file: {original_name}")
        name = os.path.splitext(os.path.basename(original_name))[0]
        target_base = os.path.basename(original_name)
        target_path = os.path.join(NDAX_DIR, target_base)
        n = 1
        while os.path.exists(target_path):
            n += 1
            target_base = f"{name}_{n}.ndax"
            target_path = os.path.join(NDAX_DIR, target_base)

        with open(target_path, "wb") as f:
            f.write(content)

        final_name = os.path.splitext(target_base)[0]
        entry = CellEntry(
            name=final_name,
            filename=target_base,
            size_bytes=os.path.getsize(target_path),
            uploaded_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            status="pending",
        )
        with self._lock:
            self._cells[final_name] = entry
            self._save_unlocked()
        self._notify()
        self._kick_parse(final_name)
        return entry

    # ── parsing ─────────────────────────────────────────────────────────────
    def _kick_parse(self, name: str) -> None:
        t = threading.Thread(target=self._parse_worker, args=(name,), daemon=True)
        t.start()

    def reparse(self, name: str) -> None:
        """Force a re-parse — useful if joblib cache was wiped."""
        with self._lock:
            entry = self._cells.get(name)
            if not entry:
                return
            entry.status = "pending"
            entry.error = ""
            self._save_unlocked()
        self._notify()
        self._kick_parse(name)

    def _parse_worker(self, name: str) -> None:
        entry = self.get(name)
        if entry is None:
            return
        with self._lock:
            entry.status = "parsing"
            self._save_unlocked()
        self._notify()

        try:
            df, report, _ = load_and_analyze(entry.path)
            if df is None or report is None or report.empty:
                raise ValueError("Loader returned no data — file may be corrupt.")

            cycles = report['Cycle no']
            cycle_min = int(cycles.min())
            cycle_max = int(cycles.max())

            # Peak DChg + cycle
            clean = report[report['Chg Capacity (Ah)'] > 0.0001]['DChg capacity (Ah)'].dropna()
            if not clean.empty:
                idx = clean.idxmax()
                peak_dchg = float(clean[idx])
                peak_cycle = int(report.loc[idx, 'Cycle no'])
            else:
                peak_dchg, peak_cycle = 0.0, 0

            max_ce = float(report['Coulombic Efficiency (%)'].dropna().max() or 0.0)
            max_ee = float(report['Energy Efficiency (%)'].dropna().max() or 0.0)

            started = ""
            try:
                if 'Timestamp' in df.columns:
                    ts_min = df['Timestamp'].min()
                    if ts_min is not None:
                        started = ts_min.isoformat() if hasattr(ts_min, 'isoformat') else str(ts_min)
            except Exception:
                pass

            with self._lock:
                entry.status = "ready"
                entry.error = ""
                entry.cycle_count = int(len(report))
                entry.cycle_min = cycle_min
                entry.cycle_max = cycle_max
                entry.started_at = started
                entry.peak_dchg_ah = peak_dchg
                entry.peak_dchg_cycle = peak_cycle
                entry.max_coulombic_eff = max_ce
                entry.max_energy_eff = max_ee
                entry.last_analyzed = datetime.utcnow().isoformat(timespec="seconds") + "Z"
                self._save_unlocked()
        except Exception as e:
            traceback.print_exc()
            with self._lock:
                entry.status = "error"
                entry.error = str(e)[:200]
                self._save_unlocked()
        finally:
            self._notify()

    # ── removal ─────────────────────────────────────────────────────────────
    def remove(self, name: str) -> bool:
        with self._lock:
            entry = self._cells.pop(name, None)
            if entry is None:
                return False
            try:
                if os.path.exists(entry.path):
                    os.remove(entry.path)
            except OSError:
                pass
            self._save_unlocked()
        self._notify()
        return True

    # ── stats ───────────────────────────────────────────────────────────────
    def stats(self) -> dict:
        cells = self.list_cells()
        total_bytes = sum(c.size_bytes for c in cells)
        ready = sum(1 for c in cells if c.status == "ready")
        return dict(
            total=len(cells),
            ready=ready,
            parsing=sum(1 for c in cells if c.status == "parsing"),
            error=sum(1 for c in cells if c.status == "error"),
            total_bytes=total_bytes,
        )


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def human_time(iso: str) -> str:
    if not iso:
        return "—"
    try:
        iso = iso.rstrip("Z")
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso


# Module-level singleton
library = Library()
