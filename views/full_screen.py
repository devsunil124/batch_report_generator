"""Full Screen sub-view: every cycle, both cells."""
from __future__ import annotations
from nicegui import ui

from state import state
import charts


def render() -> None:
    cycles_list = state.cycles_list
    if not cycles_list:
        ui.html('<div class="zn-empty"><h3>No cycles in selected range</h3></div>')
        return

    theme = state.theme
    traces = charts.vc_traces(state.dp, cycles_list, "turbo",
                              single_color=charts.primary_color(theme))
    if state.ds is not None:
        sec_cycles = sorted([int(c) for c in state.ds['Cycle'].unique() if c != 0])
        traces += charts.vc_traces(
            state.ds, sec_cycles, "sunset",
            label_suffix=f" [{state.secondary_name}]",
            single_color=charts.compare_color(theme),
        )

    fig = charts.vc_figure(
        traces, theme,
        title=f"{state.primary_name}" + (f"  vs  {state.secondary_name}" if state.secondary_name else ""),
        height=820, side_legend=True,
    )

    with ui.element('div').classes('zn-card'):
        ui.html('<div class="zn-card-header"><div class="zn-h2">Full trajectory</div>'
                f'<span class="zn-chip">{len(cycles_list)} cycles</span></div>')
        ui.plotly(fig).classes('w-full').style('height: 820px;')
