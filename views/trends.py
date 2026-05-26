"""Trends sub-view: 2x2 line chart grid."""
from __future__ import annotations
from nicegui import ui

from state import state
import charts


def render() -> None:
    rp, rs = state.rp, state.rs
    if rp is None or rp.empty:
        ui.html('<div class="zn-empty"><h3>No data in selected range</h3></div>')
        return

    primary = state.primary_name or "Primary"
    secondary = state.secondary_name or ""
    theme = state.theme

    specs = [
        ("Discharge capacity", "Cycle", "DChg cap (Ah)",  "DChg capacity (Ah)"),
        ("Coulombic efficiency", "Cycle", "Efficiency (%)", "Coulombic Efficiency (%)"),
        ("Energy efficiency", "Cycle", "Efficiency (%)", "Energy Efficiency (%)"),
        ("Charge capacity", "Cycle", "Chg cap (Ah)",  "Chg Capacity (Ah)"),
    ]

    with ui.element('div').style(
        'display:grid; grid-template-columns: 1fr 1fr; gap: 16px;'
    ):
        for title, xt, yt, col in specs:
            with ui.element('div').classes('zn-card'):
                ui.html(f'<div class="zn-card-header"><div class="zn-h2">{title}</div>'
                        f'<span class="zn-chip">cyc {state.cycle_start}–{state.cycle_end}</span></div>')
                fig = charts.line_chart(
                    rp, col, primary, theme=theme,
                    rs=rs, col_sec=col, secondary_name=secondary,
                    xtitle=xt, ytitle=yt, height=290,
                )
                ui.plotly(fig).classes('w-full').style('height: 290px;')
