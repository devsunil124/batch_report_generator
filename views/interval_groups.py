"""Interval Groups sub-view: every 5/10/25 cycle overlay."""
from __future__ import annotations
from nicegui import ui

from state import state
import charts


def render() -> None:
    cycles_list = state.cycles_list
    if not cycles_list:
        ui.html('<div class="zn-empty"><h3>No cycles in selected range</h3></div>')
        return

    flags = {'5': True, '10': True, '25': True}
    plot_holder: ui.element | None = None

    def rebuild():
        if plot_holder is None:
            return
        plot_holder.clear()
        theme = state.theme
        with plot_holder:
            traces = []
            if flags['5']:
                c5 = [c for i, c in enumerate(cycles_list) if i % 5 == 0]
                for tr in charts.vc_traces(state.dp, c5, "Blues"):
                    tr.name = tr.name + " /5"
                    traces.append(tr)
            if flags['10']:
                c10 = [c for i, c in enumerate(cycles_list) if i % 10 == 0]
                for tr in charts.vc_traces(state.dp, c10, "YlOrRd"):
                    tr.name = tr.name + " /10"
                    traces.append(tr)
            if flags['25']:
                c25 = [c for i, c in enumerate(cycles_list) if i % 25 == 0]
                for tr in charts.vc_traces(state.dp, c25, "Greens"):
                    tr.name = tr.name + " /25"
                    traces.append(tr)
            fig = charts.vc_figure(traces, theme,
                                   title=f"{state.primary_name} — multi-interval overlay",
                                   height=590)
            ui.plotly(fig).classes('w-full').style('height: 590px;')

    with ui.element('div').classes('zn-card'):
        ui.html('<div class="zn-card-header"><div class="zn-h2">Interval overlay</div>'
                '<span class="zn-chip">Blues = /5 · warm = /10 · greens = /25</span></div>')

        with ui.element('div').classes('zn-toolbar').style('margin-bottom: 14px;'):
            def make_cb(key: str, lbl: str):
                cb = ui.checkbox(lbl, value=flags[key]).props('dense dark')
                def _on(e):
                    flags[key] = bool(e.value)
                    rebuild()
                cb.on_value_change(_on)
            make_cb('5',  'Every 5th')
            make_cb('10', 'Every 10th')
            make_cb('25', 'Every 25th')
            ui.html(f'<span class="zn-chip">{len(cycles_list)} cycles</span>')

        plot_holder = ui.element('div')
        rebuild()
