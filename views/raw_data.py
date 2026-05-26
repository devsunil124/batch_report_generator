"""Raw Data view: report table with download."""
from nicegui import ui
import pandas as pd

from state import state


def _fmt_cell(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return '<span style="color:#3a3a3a">—</span>'
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _render_table(df: pd.DataFrame, cell_name: str) -> None:
    if df is None or df.empty:
        ui.html('<div class="term-empty">// NO DATA //</div>')
        return

    csv = df.to_csv(index=False).encode('utf-8')
    cols = list(df.columns)

    with ui.row().classes('items-center').style('gap: 14px; margin-bottom: 10px;'):
        ui.html(f'<span class="term-tag">{len(df)} ROWS</span>'
                f'<span class="term-tag dim">{len(cols)} COLS</span>')
        ui.button(
            f"DOWNLOAD {cell_name}.CSV",
            on_click=lambda: ui.download.content(csv, f"{cell_name}_report.csv"),
        ).props('flat').classes('term-btn-primary')

    head = ''.join(f'<th class="num">{c.upper()}</th>' for c in cols)
    rows_html = []
    for _, row in df.iterrows():
        tds = ''.join(f'<td class="num">{_fmt_cell(row[c])}</td>' for c in cols)
        rows_html.append(f'<tr>{tds}</tr>')
    table = (
        '<div style="max-height: 70vh; overflow:auto;">'
        f'<table class="term-table"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody></table>'
        '</div>'
    )
    ui.html(table)


def render() -> None:
    if not state.ready():
        ui.html('<div class="term-empty">// SELECT A CELL FROM THE LEFT RAIL TO BEGIN //</div>')
        return

    rp = state.rp
    rs = state.rs

    if state.secondary_name and rs is not None:
        sel = {'value': 'primary'}
        with ui.element('div').classes('term-panel').style('margin: 14px;'):
            with ui.element('div').classes('term-panel-header'):
                ui.html('<span>RAW REPORT DATA</span>'
                        '<span class="meta">DUAL CELL</span>')
            with ui.element('div').classes('term-panel-body'):
                with ui.row().style('gap: 0; margin-bottom: 12px;'):
                    btn_a = ui.button(state.primary_name).props('flat')
                    btn_b = ui.button(state.secondary_name).props('flat')

                body = ui.element('div')

                def show(which: str):
                    sel['value'] = which
                    btn_a.classes(remove='term-btn-primary')
                    btn_b.classes(remove='term-btn-primary')
                    (btn_a if which == 'primary' else btn_b).classes('term-btn-primary')
                    body.clear()
                    with body:
                        _render_table(
                            rp if which == 'primary' else rs,
                            state.primary_name if which == 'primary' else state.secondary_name,
                        )

                btn_a.on_click(lambda: show('primary'))
                btn_b.on_click(lambda: show('secondary'))
                show('primary')
    else:
        with ui.element('div').classes('term-panel').style('margin: 14px;'):
            with ui.element('div').classes('term-panel-header'):
                ui.html(f'<span>RAW REPORT DATA · {state.primary_name}</span>'
                        '<span class="meta">PRIMARY ONLY</span>')
            with ui.element('div').classes('term-panel-body'):
                _render_table(rp, state.primary_name)
