"""Cycle curves view: voltage vs capacity, step-sampled."""
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

    # Local UI state
    step_opt = {'value': 'Every 5th'}
    custom_n = {'value': 5}

    options = ['All', 'Every 5th', 'Every 10th', 'Every 25th', 'Custom']
    step_map = {'All': 1, 'Every 5th': 5, 'Every 10th': 10, 'Every 25th': 25}

    container = ui.element('div').classes('term-panel').style('margin: 14px;')

    def step_value() -> int:
        if step_opt['value'] == 'Custom':
            return max(1, int(custom_n['value']))
        return step_map[step_opt['value']]

    def rebuild():
        body.clear()
        with body:
            step = step_value()
            sel = [c for i, c in enumerate(cycles_list) if i % step == 0]
            if not sel and cycles_list:
                sel = [cycles_list[-1]]

            single = charts.AMBER if step_opt['value'] == 'All' else None
            traces = charts.vc_traces(state.dp, sel, "turbo", single_color=single)
            if state.ds is not None:
                primary_set = set(cycles_list)
                sec_all = sorted([int(c) for c in state.ds['Cycle'].unique() if c != 0])
                sec_sel = [c for c in sec_all if c in primary_set and cycles_list.index(c) % step == 0]
                single_sec = charts.CYAN if step_opt['value'] == 'All' else None
                traces += charts.vc_traces(
                    state.ds, sec_sel, "sunset",
                    label_suffix=f" [{state.secondary_name}]",
                    single_color=single_sec,
                )

            fig = charts.vc_figure(
                traces,
                title=f"{state.primary_name} — every {step} cycle(s)",
                height=560,
            )
            if step_opt['value'] != 'All' and len(sel) > 20:
                fig.update_layout(showlegend=False)
            ui.plotly(fig).classes('w-full').style('height: 560px;')

    with container:
        with ui.element('div').classes('term-panel-header'):
            ui.html(
                f'<span>VOLTAGE / CAPACITY · {state.primary_name}</span>'
                f'<span class="meta">SOLID = CHG · DOTTED = DCHG</span>'
            )
        with ui.element('div').classes('term-panel-body'):
            # Controls row
            with ui.row().classes('items-center').style('gap: 18px; margin-bottom: 12px;'):
                step_select = ui.select(
                    options, value=step_opt['value'], label='STEP',
                ).props('dense outlined dark').style('min-width: 160px;')

                custom_input = ui.number(
                    label='CUSTOM',
                    value=custom_n['value'], min=1, max=max(len(cycles_list), 1), step=1,
                ).props('dense outlined dark').style('width: 110px;')
                custom_input.set_enabled(step_opt['value'] == 'Custom')

                def on_step_change(e):
                    step_opt['value'] = e.value
                    custom_input.set_enabled(step_opt['value'] == 'Custom')
                    rebuild()

                def on_custom_change(e):
                    custom_n['value'] = int(e.value) if e.value else 1
                    if step_opt['value'] == 'Custom':
                        rebuild()

                step_select.on_value_change(on_step_change)
                custom_input.on_value_change(on_custom_change)

                ui.html(
                    f'<span class="term-tag">{len(cycles_list)} CYCLES AVAILABLE</span>'
                )

            body = ui.element('div')
            rebuild()
