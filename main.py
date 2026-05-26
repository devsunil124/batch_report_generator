"""ZnBr Terminal — battery analytics dashboard (NiceGUI, Bloomberg aesthetic)."""
from __future__ import annotations

from datetime import datetime
from nicegui import ui, app

import theme
from state import state
from views import summary, trends, cycle_curves, interval_groups, full_screen, raw_data


# ─── Route registry ───────────────────────────────────────────────────────────
ROUTES = [
    ('summary',   'F1', 'Summary',         summary.render),
    ('trends',    'F2', 'Trends',          trends.render),
    ('curves',    'F3', 'Cycle Curves',    cycle_curves.render),
    ('intervals', 'F4', 'Intervals',       interval_groups.render),
    ('full',      'F5', 'Full Screen',     full_screen.render),
    ('raw',       'F6', 'Raw Data',        raw_data.render),
]
ROUTE_INDEX = {r[0]: r for r in ROUTES}


# ─── Mutable shell handles (set up in main page) ──────────────────────────────
class Shell:
    current_route: str = 'summary'
    content_container: ui.element | None = None
    nav_items: dict = {}
    titlebar_cell: ui.html | None = None
    titlebar_time: ui.html | None = None
    status_msg: ui.html | None = None


shell = Shell()


# ─── Rendering ────────────────────────────────────────────────────────────────
def render_titlebar() -> None:
    with ui.element('div').classes('term-titlebar'):
        ui.html('<span class="brand">ZNBR/TERM</span>'
                '<span class="sep">│</span>'
                '<span class="field">v1.0</span>'
                '<span class="sep">│</span>')
        shell.titlebar_cell = ui.html(_cell_summary_html())
        ui.element('div').style('flex: 1;')   # spacer
        shell.titlebar_time = ui.html(_time_html())
        ui.html('<span class="sep">│</span><span class="blink">●</span><span class="field">LIVE</span>')


def render_statusbar() -> None:
    with ui.element('div').classes('term-statusbar'):
        for key, fk, label, _ in ROUTES:
            ui.html(f'<span class="field">{fk}:</span>'
                    f'<span style="color:#c8c8c8;">{label.upper()}</span>')
        ui.element('div').style('flex: 1;')
        shell.status_msg = ui.html(_status_html())


def render_sidebar() -> None:
    with ui.element('div').classes('term-nav'):
        ui.html('<div class="term-nav-section">VIEW</div>')
        for key, fk, label, _ in ROUTES:
            cls = 'term-nav-item' + (' active' if key == shell.current_route else '')
            item = ui.element('div').classes(cls)
            with item:
                ui.html(f'<span class="key">{fk}</span>'
                        f'<span>{label}</span>')
            item.on('click', lambda _, k=key: navigate(k))
            shell.nav_items[key] = item

        ui.html('<div class="term-nav-section">CELL MGR</div>')
        with ui.element('div').style('padding: 4px 14px 8px 14px;'):
            _render_cell_manager()


def _render_cell_manager() -> None:
    # Folder path
    ui.html('<div style="color:#5a5a5a; font-size:10px; letter-spacing:0.14em; '
            'text-transform:uppercase; margin-bottom:4px;">NDAX FOLDER</div>')
    folder_input = ui.input(value=state.folder_path).props(
        'dense outlined dark autogrow'
    ).style('width:100%; margin-bottom: 6px;')

    def apply_folder():
        new_path = (folder_input.value or "").strip()
        if new_path != state.folder_path:
            state.set_folder(new_path)
            redraw_sidebar_and_content()

    folder_input.on('blur', lambda _: apply_folder())
    folder_input.on('keydown.enter', lambda _: apply_folder())

    with ui.row().style('gap: 4px; margin-bottom: 10px;'):
        def browse():
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.attributes('-topmost', True)
                root.withdraw()
                selected = filedialog.askdirectory(
                    master=root,
                    initialdir=state.folder_path if state.folder_valid() else None,
                )
                root.destroy()
                if selected:
                    folder_input.set_value(selected)
                    state.set_folder(selected)
                    redraw_sidebar_and_content()
            except Exception as e:
                ui.notify(f"Browse failed: {e}", type='negative')

        ui.button("BROWSE", on_click=browse).props('flat dense').style('flex:1;')
        ui.button("LOAD", on_click=lambda: apply_folder()).props('flat dense').classes('term-btn-primary').style('flex:1;')

    cells = state.list_cells()
    if not cells:
        ui.html('<div style="color:#5a5a5a; font-size:11px; padding:4px 0;">'
                '// NO .NDAX FILES FOUND //</div>')
        return

    ui.html('<div style="color:#5a5a5a; font-size:10px; letter-spacing:0.14em; '
            'text-transform:uppercase; margin:6px 0 4px;">PRIMARY CELL</div>')
    prim = ui.select(
        cells, value=state.primary_name if state.primary_name in cells else None,
        with_input=True,
    ).props('dense outlined dark').style('width: 100%;')
    def on_prim(e):
        state.set_primary(e.value)
        redraw_sidebar_and_content()
    prim.on_value_change(on_prim)

    if state.primary_name:
        sz = state.file_size_mb(state.primary_name)
        ui.html(f'<div style="color:#5a5a5a; font-size:10px; margin-top:2px;">'
                f'{sz:.1f} MB</div>')

    sec_opts = ['— None —'] + [c for c in cells if c != state.primary_name]
    sec_val = state.secondary_name if state.secondary_name else '— None —'
    ui.html('<div style="color:#5a5a5a; font-size:10px; letter-spacing:0.14em; '
            'text-transform:uppercase; margin:10px 0 4px;">COMPARE CELL</div>')
    sec = ui.select(sec_opts, value=sec_val, with_input=True).props(
        'dense outlined dark'
    ).style('width: 100%;')
    def on_sec(e):
        val = None if (not e.value or e.value == '— None —') else e.value
        state.set_secondary(val)
        redraw_sidebar_and_content()
    sec.on_value_change(on_sec)

    # Cycle range (only when data loaded)
    if state.ready():
        ui.html('<div style="color:#5a5a5a; font-size:10px; letter-spacing:0.14em; '
                'text-transform:uppercase; margin:10px 0 4px;">CYCLE RANGE</div>')
        if state.cycle_min == state.cycle_max:
            ui.html(f'<div style="color:#c8c8c8; font-size:11px;">'
                    f'SINGLE CYCLE: {state.cycle_min}</div>')
        else:
            with ui.row().style('gap: 4px;'):
                c_start = ui.number(
                    label='START', value=state.cycle_start,
                    min=state.cycle_min, max=state.cycle_max, step=1,
                ).props('dense outlined dark').style('flex:1;')
                c_end = ui.number(
                    label='END', value=state.cycle_end,
                    min=state.cycle_min, max=state.cycle_max, step=1,
                ).props('dense outlined dark').style('flex:1;')

                def apply_range(_=None):
                    try:
                        s = int(c_start.value); e = int(c_end.value)
                    except (TypeError, ValueError):
                        return
                    if s == state.cycle_start and e == state.cycle_end:
                        return
                    state.set_range(s, e)
                    redraw_content()

                c_start.on('blur', apply_range)
                c_end.on('blur', apply_range)
                c_start.on('keydown.enter', apply_range)
                c_end.on('keydown.enter', apply_range)


def _cell_summary_html() -> str:
    if not state.ready():
        return ('<span class="field">CELL:</span>'
                '<span class="val">—</span>')
    base = (f'<span class="field">CELL:</span>'
            f'<span class="val">{state.primary_name}</span>')
    if state.secondary_name:
        base += (f'<span class="sep">│</span>'
                 f'<span class="field">VS:</span>'
                 f'<span class="val" style="color:#00d9ff;">{state.secondary_name}</span>')
    base += (f'<span class="sep">│</span>'
             f'<span class="field">CYC:</span>'
             f'<span class="val">{state.cycle_start}–{state.cycle_end}</span>')
    return base


def _time_html() -> str:
    return (f'<span class="field">SYS:</span>'
            f'<span class="val">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>')


def _status_html() -> str:
    if not state.folder_valid():
        return '<span class="chip">NO FOLDER</span>'
    if not state.ready():
        return f'<span class="chip">READY · {state.folder_path}</span>'
    n_cyc = len(state.rp) if state.rp is not None else 0
    return (f'<span class="chip">LOADED · {n_cyc} CYCLES</span>'
            f'<span class="field">{state.folder_path}</span>')


def navigate(key: str) -> None:
    if key not in ROUTE_INDEX or key == shell.current_route:
        return
    shell.current_route = key
    for k, item in shell.nav_items.items():
        if k == key:
            item.classes(add='active')
        else:
            item.classes(remove='active')
    redraw_content()


def redraw_content() -> None:
    if shell.content_container is None:
        return
    shell.content_container.clear()
    with shell.content_container:
        ROUTE_INDEX[shell.current_route][3]()
    if shell.titlebar_cell is not None:
        shell.titlebar_cell.set_content(_cell_summary_html())
    if shell.status_msg is not None:
        shell.status_msg.set_content(_status_html())


def redraw_sidebar_and_content() -> None:
    # Re-render the entire sidebar (cell manager state changed)
    if _sidebar_container is None:
        return
    _sidebar_container.clear()
    with _sidebar_container:
        render_sidebar()
    redraw_content()


# Need to hold a reference to the side container so we can refresh it
_sidebar_container: ui.element | None = None


@ui.page('/')
def index() -> None:
    global _sidebar_container
    theme.apply_theme()

    # Top bar
    render_titlebar()

    # Main flex row: sidebar + content
    with ui.row().style(
        'flex: 1; gap: 0; margin: 0; padding: 0; width: 100%; '
        'flex-wrap: nowrap; min-height: 0;'
    ).classes('items-stretch'):
        _sidebar_container = ui.element('div')
        with _sidebar_container:
            render_sidebar()

        shell.content_container = ui.element('div').style(
            'flex: 1; overflow-y: auto; min-width: 0; background: #050505;'
        )
        with shell.content_container:
            ROUTE_INDEX[shell.current_route][3]()

    # Status bar
    render_statusbar()

    # Live clock
    def tick():
        if shell.titlebar_time is not None:
            shell.titlebar_time.set_content(_time_html())
    ui.timer(1.0, tick)


# ─── Bootstrap ────────────────────────────────────────────────────────────────
if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title="ZnBr/Term",
        favicon="🔋",
        dark=True,
        port=8765,
        reload=False,
        show=True,
        storage_secret='znbr-terminal-local',
    )
