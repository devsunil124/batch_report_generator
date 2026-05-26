"""Cycle Curves sub-view: voltage vs capacity with step selector."""
from __future__ import annotations
from nicegui import ui

from state import state
import charts


def render() -> None:
    cycles_list = state.cycles_list
    if not cycles_list:
        ui.html('<div class="zn-empty"><h3>No cycles in selected range</h3></div>')
        return

    step_opt = {'value': 'Every 5th'}
    custom_n = {'value': 5}

    options = ['All', 'Every 5th', 'Every 10th', 'Every 25th', 'Custom']
    step_map = {'All': 1, 'Every 5th': 5, 'Every 10th': 10, 'Every 25th': 25}

    def step_value() -> int:
        if step_opt['value'] == 'Custom':
            return max(1, int(custom_n['value']))
        return step_map[step_opt['value']]

    plot_holder: ui.element | None = None

    def rebuild():
        if plot_holder is None:
            return
        plot_holder.clear()
        theme = state.theme
        with plot_holder:
            step = step_value()
            sel = [c for i, c in enumerate(cycles_list) if i % step == 0]
            if not sel and cycles_list:
                sel = [cycles_list[-1]]

            single = charts.primary_color(theme) if step_opt['value'] == 'All' else None
            traces = charts.vc_traces(state.dp, sel, "turbo", single_color=single)
            if state.ds is not None:
                primary_set = set(cycles_list)
                sec_all = sorted([int(c) for c in state.ds['Cycle'].unique() if c != 0])
                sec_sel = [c for c in sec_all if c in primary_set and cycles_list.index(c) % step == 0]
                single_sec = charts.compare_color(theme) if step_opt['value'] == 'All' else None
                traces += charts.vc_traces(
                    state.ds, sec_sel, "sunset",
                    label_suffix=f" [{state.secondary_name}]",
                    single_color=single_sec,
                )

            fig = charts.vc_figure(traces, theme,
                                   title=f"{state.primary_name} — every {step} cycle(s)",
                                   height=580)
            if step_opt['value'] != 'All' and len(sel) > 20:
                fig.update_layout(showlegend=False)
            ui.plotly(fig).classes('w-full').style('height: 580px;')

    with ui.element('div').classes('zn-card'):
        ui.html('<div class="zn-card-header"><div class="zn-h2">Voltage vs capacity</div>'
                '<span class="zn-chip">Solid = chg · dotted = dchg</span></div>')

        with ui.element('div').classes('zn-toolbar').style('margin-bottom: 14px;'):
            with ui.element('div').classes('group'):
                ui.html('<span class="lbl">Step</span>')
                step_select = ui.select(options, value=step_opt['value']).props('dense outlined dark').style('min-width: 160px;')
            with ui.element('div').classes('group'):
                ui.html('<span class="lbl">Custom</span>')
                custom_input = ui.number(value=custom_n['value'], min=1,
                                         max=max(len(cycles_list), 1), step=1
                                         ).props('dense outlined dark').style('width: 110px;')
                custom_input.set_enabled(step_opt['value'] == 'Custom')

            ui.html(f'<span class="zn-chip">{len(cycles_list)} cycles available</span>')

            def on_step(e):
                step_opt['value'] = e.value
                custom_input.set_enabled(step_opt['value'] == 'Custom')
                rebuild()

            def on_custom(e):
                custom_n['value'] = int(e.value) if e.value else 1
                if step_opt['value'] == 'Custom':
                    rebuild()

            step_select.on_value_change(on_step)
            custom_input.on_value_change(on_custom)

        plot_holder = ui.element('div')
        rebuild()
