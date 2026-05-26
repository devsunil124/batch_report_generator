"""Full Screen view: every cycle, both cells, side legend."""
from nicegui import ui

from state import state
import charts


def render() -> None:
    if not state.ready():
        ui.html('<div class="term-empty">// SELECT A CELL FROM THE LEFT RAIL TO BEGIN //</div>')
        return

    cycles_list = state.cycles_list
    if not cycles_list:
        ui.html('<div class="term-empty">// NO CYCLES IN SELECTED RANGE //</div>')
        return

    traces = charts.vc_traces(state.dp, cycles_list, "turbo", single_color=charts.AMBER)
    if state.ds is not None:
        sec_cycles = sorted([int(c) for c in state.ds['Cycle'].unique() if c != 0])
        traces += charts.vc_traces(
            state.ds, sec_cycles, "sunset",
            label_suffix=f" [{state.secondary_name}]",
            single_color=charts.CYAN,
        )

    fig = charts.vc_figure(
        traces,
        title=f"FULL · {state.primary_name}"
              + (f" vs {state.secondary_name}" if state.secondary_name else ""),
        height=820,
        side_legend=True,
    )

    with ui.element('div').classes('term-panel').style('margin: 14px;'):
        with ui.element('div').classes('term-panel-header'):
            ui.html(
                f'<span>FULL TRAJECTORY</span>'
                f'<span class="meta">{len(cycles_list)} CYCLES · '
                + (f'COMPARING {state.secondary_name}' if state.secondary_name else 'PRIMARY ONLY')
                + '</span>'
            )
        with ui.element('div').classes('term-panel-body').style('padding: 4px;'):
            ui.plotly(fig).classes('w-full').style('height: 820px;')
