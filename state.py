"""Per-analysis state: which cell, optional compare cell, range filter.

Backed by the library — pulls dataframes via load_and_analyze on demand.
Joblib caches make repeat loads instant; the library's catalog gives O(1)
metadata for the home page so the user never waits on a full parse just to
see what they have.
"""
from __future__ import annotations
from typing import Optional

from data_loader import load_and_analyze
from library import library


class AnalysisState:
    """One instance lives in memory; the analysis page reads it."""

    def __init__(self) -> None:
        self.primary_name: Optional[str] = None
        self.secondary_name: Optional[str] = None

        self.df_prim = None
        self.report_prim = None
        self.df_sec = None
        self.report_sec = None

        self.cycle_min: int = 0
        self.cycle_max: int = 0
        self.cycle_start: int = 0
        self.cycle_end: int = 0

        self.theme: str = "light"  # 'light' | 'dark' — mirrored from browser

    # ── selection ───────────────────────────────────────────────────────────
    def set_primary(self, name: Optional[str]) -> None:
        if not name:
            self.primary_name = None
            self.df_prim = self.report_prim = None
            self._recompute_range()
            return
        entry = library.get(name)
        if entry is None:
            self.primary_name = None
            self.df_prim = self.report_prim = None
            return
        self.primary_name = name
        df, rpt, _ = load_and_analyze(entry.path)
        self.df_prim, self.report_prim = df, rpt
        self._recompute_range()

    def set_secondary(self, name: Optional[str]) -> None:
        if not name or name == self.primary_name:
            self.secondary_name = None
            self.df_sec = self.report_sec = None
            self._recompute_range()
            return
        entry = library.get(name)
        if entry is None:
            self.secondary_name = None
            self.df_sec = self.report_sec = None
            return
        self.secondary_name = name
        df, rpt, _ = load_and_analyze(entry.path)
        self.df_sec, self.report_sec = df, rpt
        self._recompute_range()

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

    # ── filtered views ──────────────────────────────────────────────────────
    @property
    def rp(self):
        if self.report_prim is None or self.report_prim.empty:
            return None
        rp = self.report_prim
        return rp[(rp['Cycle no'] >= self.cycle_start) & (rp['Cycle no'] <= self.cycle_end)].copy()

    @property
    def dp(self):
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


state = AnalysisState()
