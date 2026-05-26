"""Trends view: four core line charts in a 2x2 grid."""
from nicegui import ui

from state import state
import charts


def render() -> None:
    if not state.ready():
        ui.html('<div class="term-empty">// SELECT A CELL FROM THE LEFT RAIL TO BEGIN //</div>')
        return

    rp, rs = state.rp, state.rs
    if rp is None or rp.empty:
        ui.html('<div class="term-empty">// NO DATA IN SELECTED CYCLE RANGE //</div>')
        return

    primary = state.primary_name or "PRIMARY"
    secondary = state.secondary_name or ""

    specs = [
        ("DISCHARGE CAPACITY", "Cycle", "DChg Cap (Ah)", "DChg capacity (Ah)"),
        ("COULOMBIC EFFICIENCY", "Cycle", "Eff (%)", "Coulombic Efficiency (%)"),
        ("ENERGY EFFICIENCY", "Cycle", "Eff (%)", "Energy Efficiency (%)"),
        ("CHARGE CAPACITY", "Cycle", "Chg Cap (Ah)", "Chg Capacity (Ah)"),
    ]

    with ui.element('div').style(
        'display:grid; grid-template-columns: 1fr 1fr; gap: 14px; padding: 14px;'
    ):
        for title, xt, yt, col in specs:
            with ui.element('div').classes('term-panel'):
                with ui.element('div').classes('term-panel-header'):
                    ui.html(f'<span>{title}</span>'
                            f'<span class="meta">CYC {state.cycle_start}–{state.cycle_end}</span>')
                with ui.element('div').classes('term-panel-body').style('padding: 4px;'):
                    fig = charts.line_chart(
                        rp, col, primary,
                        rs=rs, col_sec=col, secondary_name=secondary,
                        xtitle=xt, ytitle=yt, height=280,
                    )
                    ui.plotly(fig).classes('w-full').style('height: 280px;')
