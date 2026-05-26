"""Raw Data sub-view: report table + CSV download."""
from __future__ import annotations
import pandas as pd
from nicegui import ui

from state import state


def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return '<span style="color:var(--text-muted)">—</span>'
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _table(df: pd.DataFrame, cell_name: str) -> None:
    if df is None or df.empty:
        ui.html('<div class="zn-empty"><h3>No data</h3></div>')
        return

    csv = df.to_csv(index=False).encode('utf-8')
    cols = list(df.columns)

    with ui.row().style('gap: 12px; margin-bottom: 12px; align-items: center;'):
        ui.html(f'<span class="zn-chip">{len(df)} rows</span>'
                f'<span class="zn-chip">{len(cols)} cols</span>')
        ui.button(
            f"Download {cell_name}.csv",
            on_click=lambda: ui.download.content(csv, f"{cell_name}_report.csv"),
        ).classes('zn-primary')

    head = ''.join(f'<th class="num">{c}</th>' for c in cols)
    rows = []
    for _, row in df.iterrows():
        rows.append('<tr>' + ''.join(f'<td class="num">{_fmt(row[c])}</td>' for c in cols) + '</tr>')
    ui.html(
        '<div style="max-height: 65vh; overflow:auto; border: 1px solid var(--border); border-radius: 12px;">'
        f'<table class="zn-table"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def render() -> None:
    rp, rs = state.rp, state.rs

    if state.secondary_name and rs is not None:
        sel = {'value': 'primary'}
        with ui.element('div').classes('zn-card'):
            ui.html('<div class="zn-card-header"><div class="zn-h2">Raw report data</div>'
                    '<span class="zn-chip accent">Dual cell</span></div>')

            with ui.row().style('gap: 0; margin-bottom: 12px;'):
                btn_a = ui.button(state.primary_name).classes('zn-primary')
                btn_b = ui.button(state.secondary_name)

            body = ui.element('div')

            def show(which: str):
                sel['value'] = which
                btn_a.classes(remove='zn-primary')
                btn_b.classes(remove='zn-primary')
                (btn_a if which == 'primary' else btn_b).classes('zn-primary')
                body.clear()
                with body:
                    _table(
                        rp if which == 'primary' else rs,
                        state.primary_name if which == 'primary' else state.secondary_name,
                    )

            btn_a.on_click(lambda: show('primary'))
            btn_b.on_click(lambda: show('secondary'))
            show('primary')
    else:
        with ui.element('div').classes('zn-card'):
            ui.html(f'<div class="zn-card-header"><div class="zn-h2">Raw report data · {state.primary_name}</div></div>')
            _table(rp, state.primary_name or "")
