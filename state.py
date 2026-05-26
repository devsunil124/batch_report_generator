"""Shared application state for the ZnBr terminal dashboard.

This is a single-user local dashboard, so module-level state is fine.
"""
import os
import glob
import re
import pandas as pd

from config_manager import load_config, save_config
from data_loader import load_and_analyze


def _natural_key(s: str):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]


class AppState:
    """Holds the user's current selection and loaded dataframes."""

    def __init__(self) -> None:
        self.folder_path: str = load_config() or ""
        self.primary_name: str | None = None
        self.secondary_name: str | None = None

        self.df_prim = None
        self.report_prim = None
        self.df_sec = None
        self.report_sec = None

        self.cycle_min: int = 0
        self.cycle_max: int = 0
        self.cycle_start: int = 0
        self.cycle_end: int = 0

        self._listeners: list = []

    # ── observers ────────────────────────────────────────────────────────────
    def subscribe(self, fn) -> None:
        if fn not in self._listeners:
            self._listeners.append(fn)

    def _notify(self) -> None:
        for fn in list(self._listeners):
            try:
                fn()
            except Exception as e:
                print(f"[state] listener error: {e}")

    # ── folder ───────────────────────────────────────────────────────────────
    def set_folder(self, path: str) -> None:
        path = (path or "").strip()
        if path and os.path.isdir(path):
            self.folder_path = path
            save_config(path)
            # Reset selection because file list changed
            self.primary_name = None
            self.secondary_name = None
            self.df_prim = self.report_prim = None
            self.df_sec = self.report_sec = None
            self._notify()

    def folder_valid(self) -> bool:
        return bool(self.folder_path) and os.path.isdir(self.folder_path)

    def list_cells(self) -> list[str]:
        if not self.folder_valid():
            return []
        files = sorted(
            glob.glob(os.path.join(self.folder_path, "*.ndax")),
            key=_natural_key,
        )
        return [os.path.basename(os.path.splitext(f)[0]) for f in files]

    def file_for(self, name: str) -> str:
        return os.path.join(self.folder_path, f"{name}.ndax")

    def file_size_mb(self, name: str) -> float:
        try:
            return os.path.getsize(self.file_for(name)) / (1024 * 1024)
        except OSError:
            return 0.0

    # ── cell selection ───────────────────────────────────────────────────────
    def set_primary(self, name: str | None) -> None:
        if not name:
            self.primary_name = None
            self.df_prim = self.report_prim = None
            self._recompute_range()
            self._notify()
            return
        self.primary_name = name
        df, rpt, _ = load_and_analyze(self.file_for(name))
        self.df_prim, self.report_prim = df, rpt
        self._recompute_range()
        self._notify()

    def set_secondary(self, name: str | None) -> None:
        if not name or name == self.primary_name:
            self.secondary_name = None
            self.df_sec = self.report_sec = None
            self._recompute_range()
            self._notify()
            return
        self.secondary_name = name
        df, rpt, _ = load_and_analyze(self.file_for(name))
        self.df_sec, self.report_sec = df, rpt
        self._recompute_range()
        self._notify()

    def _recompute_range(self) -> None:
        rp, rs = self.report_prim, self.report_sec
        if rp is None or rp.empty:
            self.cycle_min = self.cycle_max = 0
            self.cycle_start = self.cycle_end = 0
            return
        cmin = int(rp['Cycle no'].min())
        cmax = int(rp['Cycle no'].max())
        if rs is not None and not rs.empty:
            cmin = min(cmin, int(rs['Cycle no'].min()))
            cmax = max(cmax, int(rs['Cycle no'].max()))
        self.cycle_min, self.cycle_max = cmin, cmax
        self.cycle_start, self.cycle_end = cmin, cmax

    def set_range(self, start: int, end: int) -> None:
        lo, hi = min(start, end), max(start, end)
        lo = max(lo, self.cycle_min)
        hi = min(hi, self.cycle_max)
        self.cycle_start, self.cycle_end = lo, hi
        self._notify()

    # ── filtered views ───────────────────────────────────────────────────────
    @property
    def rp(self):
        """Filtered primary report dataframe (Cycle no in range)."""
        if self.report_prim is None or self.report_prim.empty:
            return None
        rp = self.report_prim
        return rp[(rp['Cycle no'] >= self.cycle_start) & (rp['Cycle no'] <= self.cycle_end)].copy()

    @property
    def dp(self):
        """Filtered primary raw dataframe."""
        if self.df_prim is None:
            return None
        dp = self.df_prim
        return dp[(dp['Cycle'] >= self.cycle_start) & (dp['Cycle'] <= self.cycle_end)].copy()

    @property
    def rs(self):
        if self.report_sec is None or self.report_sec.empty:
            return None
        rs = self.report_sec
        return rs[(rs['Cycle no'] >= self.cycle_start) & (rs['Cycle no'] <= self.cycle_end)].copy()

    @property
    def ds(self):
        if self.df_sec is None:
            return None
        ds = self.df_sec
        return ds[(ds['Cycle'] >= self.cycle_start) & (ds['Cycle'] <= self.cycle_end)].copy()

    @property
    def cycles_list(self) -> list[int]:
        dp = self.dp
        if dp is None or dp.empty:
            return []
        return sorted([int(c) for c in dp['Cycle'].unique() if c != 0])

    def ready(self) -> bool:
        return self.report_prim is not None and not self.report_prim.empty


# Global singleton
state = AppState()