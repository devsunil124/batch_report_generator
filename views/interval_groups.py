"""Interval Groups view: 5th/10th/25th overlay with separate palettes."""
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

    flags = {'5': True, '10': True, '25': True}

    container = ui.element('div').classes('term-panel').style('margin: 14px;')

    def rebuild():
        body.clear()
        with body:
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
            fig = charts.vc_figure(
                traces, title=f"{state.primary_name} — multi-interval overlay",
                height=580,
            )
            ui.plotly(fig).classes('w-full').style('height: 580px;')

    with container:
        with ui.element('div').classes('term-panel-header'):
            ui.html(
                f'<span>INTERVAL OVERLAY · {state.primary_name}</span>'
                f'<span class="meta">BLUES=/5 · WARM=/10 · GREENS=/25</span>'
            )
        with ui.element('div').classes('term-panel-body'):
            with ui.row().classes('items-center').style('gap: 22px; margin-bottom: 12px;'):
                def make_toggle(key: str, label: str):
                    cb = ui.checkbox(label, value=flags[key]).props('dense dark')
                    def _on(e):
                        flags[key] = bool(e.value)
                        rebuild()
                    cb.on_value_change(_on)
                make_toggle('5',  'EVERY 5TH')
                make_toggle('10', 'EVERY 10TH')
                make_toggle('25', 'EVERY 25TH')
                ui.html(f'<span class="term-tag">{len(cycles_list)} CYCLES</span>')

            body = ui.element('div')
            rebuild()
