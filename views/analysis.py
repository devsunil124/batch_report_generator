"""Analysis page: toolbar (cell pickers + range) + horizontal tabs hosting sub-views."""
from __future__ import annotations
from nicegui import ui

from state import state
from library import library
from views import summary, trends, cycle_curves, interval_groups, full_screen, raw_data


TABS = [
    ('summary',   'Summary',         summary.render),
    ('trends',    'Trends',          trends.render),
    ('curves',    'Cycle Curves',    cycle_curves.render),
    ('intervals', 'Intervals',       interval_groups.render),
    ('full',      'Full Trajectory', full_screen.render),
    ('raw',       'Raw Data',        raw_data.render),
]
TAB_INDEX = {t[0]: t for t in TABS}


def render(initial_cell: str | None = None, navigate_home=None) -> None:
    """Render the analysis page. Loads `initial_cell` as primary if provided."""
    if initial_cell:
        # Only re-load if the selection actually changed; otherwise cached data
        # in state already has the right cell.
        if state.primary_name != initial_cell:
            state.set_primary(initial_cell)

    # Local UI state
    current_tab = {'value': 'summary'}
    content_holder: ui.element | None = None

    def render_tab():
        if content_holder is None:
            return
        content_holder.clear()
        with content_holder:
            TAB_INDEX[current_tab['value']][2]()

    # ── Toolbar ──────────────────────────────────────────────────────────────
    with ui.element('div').classes('zn-page'):
        # Breadcrumb + back to home
        with ui.row().style('align-items:center; gap:8px; margin-bottom:14px;'):
            ui.button("← Home", on_click=lambda: navigate_home() if navigate_home else None).classes('zn-ghost')
            ui.html(f'<span style="color:var(--text-muted); font-size:13px;">Analysis</span>'
                    f'<span style="color:var(--text-muted);">/</span>'
                    f'<span style="color:var(--text); font-size:13px; font-weight:600;">{state.primary_name or "—"}</span>')

        # Cell picker + compare + range
        ready_cells = [c.name for c in library.ready_cells()]
        with ui.element('div').classes('zn-toolbar').style('margin-bottom: 16px;'):
            with ui.element('div').classes('group'):
                ui.html('<span class="lbl">Primary</span>')
                prim_select = ui.select(
                    ready_cells,
                    value=state.primary_name if state.primary_name in ready_cells else None,
                    with_input=True,
                ).props('dense outlined dark').style('min-width: 200px;')

            with ui.element('div').classes('group'):
                ui.html('<span class="lbl">Compare</span>')
                compare_opts = ['— None —'] + [c for c in ready_cells if c != state.primary_name]
                sec_val = state.secondary_name if state.secondary_name in compare_opts else '— None —'
                sec_select = ui.select(
                    compare_opts, value=sec_val, with_input=True,
                ).props('dense outlined dark').style('min-width: 200px;')

            if state.ready():
                with ui.element('div').classes('group'):
                    ui.html('<span class="lbl">Cycle range</span>')
                    if state.cycle_min == state.cycle_max:
                        ui.html(f'<span class="zn-chip">single cycle: {state.cycle_min}</span>')
                    else:
                        c_start = ui.number(
                            value=state.cycle_start, min=state.cycle_min,
                            max=state.cycle_max, step=1,
                        ).props('dense outlined dark').style('width: 100px;')
                        c_end = ui.number(
                            value=state.cycle_end, min=state.cycle_min,
                            max=state.cycle_max, step=1,
                        ).props('dense outlined dark').style('width: 100px;')

                        def apply_range(_=None):
                            try:
                                s = int(c_start.value); e = int(c_end.value)
                            except (TypeError, ValueError):
                                return
                            if s == state.cycle_start and e == state.cycle_end:
                                return
                            state.set_range(s, e)
                            render_tab()
                        c_start.on('blur', apply_range)
                        c_end.on('blur', apply_range)
                        c_start.on('keydown.enter', apply_range)
                        c_end.on('keydown.enter', apply_range)

            def on_prim(e):
                if e.value and e.value != state.primary_name:
                    state.set_primary(e.value)
                    if navigate_home is not None:
                        ui.navigate.to(f'/analysis?cell={e.value}')
                    else:
                        render_tab()
            def on_sec(e):
                val = None if (not e.value or e.value == '— None —') else e.value
                state.set_secondary(val)
                render_tab()
            prim_select.on_value_change(on_prim)
            sec_select.on_value_change(on_sec)

        # ── Tabs ─────────────────────────────────────────────────────────────
        with ui.element('div').classes('zn-tabs').style('margin-bottom: 18px;'):
            tabs = ui.tabs().on_value_change(lambda e: (current_tab.update(value=e.value), render_tab()))
            with tabs:
                for key, label, _ in TABS:
                    ui.tab(name=key, label=label)
            tabs.value = current_tab['value']

        # ── Content ──────────────────────────────────────────────────────────
        if not state.ready():
            ui.html(
                '<div class="zn-empty">'
                '<h3>Pick a cell to begin</h3>'
                '<p>Use the primary dropdown above, or go back to Home and click a cell card.</p>'
                '</div>'
            )
        else:
            content_holder = ui.element('div')
            render_tab()
