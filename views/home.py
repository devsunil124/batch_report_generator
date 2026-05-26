"""Home page: branded landing, library upload, cell card grid."""
from __future__ import annotations
from nicegui import ui, events

from library import library, human_size, human_time


def _stats_html() -> str:
    s = library.stats()
    parts = [
        ('Cells', str(s['total'])),
        ('Ready', str(s['ready'])),
        ('Storage', human_size(s['total_bytes'])),
    ]
    if s['parsing']:
        parts.append(('Parsing', str(s['parsing'])))
    if s['error']:
        parts.append(('Errors', str(s['error'])))
    chips = ''.join(
        f'<span class="zn-chip">'
        f'<span style="color:var(--text-muted)">{k}</span>'
        f'<span style="color:var(--text);font-weight:600">{v}</span>'
        f'</span>'
        for k, v in parts
    )
    return chips


def render(navigate_to_analysis) -> None:
    """Build the home page. `navigate_to_analysis(cell_name)` opens analysis."""

    container = ui.element('div').classes('zn-page')
    body_holder: ui.element | None = None
    stats_holder: ui.html | None = None

    def refresh():
        if stats_holder is not None:
            stats_holder.set_content(_stats_html())
        _render_library(body_holder, navigate_to_analysis)

    library.subscribe(refresh)
    # NiceGUI will tear down the page on disconnect; safe to leak this listener
    # because Library lives for the process lifetime.

    with container:
        # Hero
        with ui.element('div').classes('zn-hero'):
            ui.html('<div class="zn-eyebrow">Zinc-Bromine Cell Analytics</div>')
            ui.html('<h1 class="zn-h1">Your cell library at a glance.</h1>')
            ui.html(
                '<p class="zn-lead">'
                'Drop your <code style="background:var(--surface-2); '
                'padding:1px 6px; border-radius:4px; font-size:12px;">.ndax</code> files into the app and '
                'they\'re parsed once, cached forever, and ready to compare. '
                'No folders to point at, no waiting.</p>'
            )
            with ui.row().style('gap:8px; margin-top:14px; align-items:center;'):
                stats_holder = ui.html(_stats_html())

        # Upload zone
        _render_upload()

        # Library
        ui.html('<div style="margin-top: 40px; display: flex; align-items: center; '
                'justify-content: space-between; margin-bottom: 16px;">'
                '<div class="zn-h2">Library</div>'
                '<div style="color: var(--text-muted); font-size: 12px;">'
                'Click a cell to open analysis</div></div>')

        body_holder = ui.element('div')
        _render_library(body_holder, navigate_to_analysis)


def _render_upload() -> None:
    """Drag-drop zone backed by ui.upload (hidden, programmatically triggered)."""
    upload_id = "zn-upload-input"

    def handle_upload(e: events.UploadEventArguments) -> None:
        try:
            content = e.content.read()
            library.add_bytes(content, e.name)
            ui.notify(f"Added {e.name}", type='positive')
        except Exception as ex:
            ui.notify(f"Upload failed: {ex}", type='negative')

    # The actual upload widget, hidden — we trigger its file input from our pretty drop.
    upload = ui.upload(
        on_upload=handle_upload,
        multiple=True,
        max_file_size=500 * 1024 * 1024,
        auto_upload=True,
        label='',
    ).props('accept=".ndax" flat')
    upload.classes('zn-hidden-upload').props(f'id="{upload_id}"')

    drop_html = f'''
    <div class="zn-drop" id="zn-drop"
         onclick="document.querySelector('#{upload_id} input[type=file]').click()"
         ondragover="event.preventDefault(); this.classList.add('dragover');"
         ondragleave="this.classList.remove('dragover');"
         ondrop="event.preventDefault(); this.classList.remove('dragover');
                 var dt = event.dataTransfer;
                 var input = document.querySelector('#{upload_id} input[type=file]');
                 input.files = dt.files;
                 input.dispatchEvent(new Event('change', {{ bubbles: true }}));">
        <div class="icon">↑</div>
        <h3>Drop your .ndax files here</h3>
        <p>or click to browse — they\'ll be copied into the app and parsed in the background.</p>
    </div>
    '''
    ui.html(drop_html)


def _status_class(s: str) -> str:
    if s == 'ready':   return ''
    if s == 'parsing': return ' parsing'
    if s == 'error':   return ' error'
    return ' parsing'  # pending


def _status_label(s: str) -> str:
    return {
        'ready':   'READY',
        'parsing': 'PARSING…',
        'pending': 'QUEUED',
        'error':   'ERROR',
    }.get(s, s.upper())


def _render_library(holder: ui.element | None, navigate_to_analysis) -> None:
    if holder is None:
        return
    holder.clear()
    cells = library.list_cells()
    with holder:
        if not cells:
            ui.html(
                '<div class="zn-empty">'
                '<h3>No cells yet</h3>'
                '<p>Upload a .ndax file above to get started.</p>'
                '</div>'
            )
            return

        with ui.element('div').style(
            'display:grid; gap:14px; '
            'grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));'
        ):
            for cell in cells:
                _render_card(cell, navigate_to_analysis)


def _render_card(cell, navigate_to_analysis) -> None:
    is_ready = (cell.status == 'ready')
    status_cls = _status_class(cell.status)
    status_lbl = _status_label(cell.status)

    cycle_range = (f"{cell.cycle_min}–{cell.cycle_max}" if is_ready and cell.cycle_count else "—")
    peak = (f"{cell.peak_dchg_ah:.3f} Ah" if is_ready and cell.peak_dchg_ah else "—")
    coul = (f"{cell.max_coulombic_eff:.1f}%" if is_ready and cell.max_coulombic_eff else "—")
    started = human_time(cell.started_at) if is_ready and cell.started_at else "—"

    card = ui.element('div').classes('zn-cell-card')
    with card:
        ui.html(
            f'<div class="cc-top">'
            f'<div class="cc-name" title="{cell.name}">{cell.name}</div>'
            f'<span class="cc-badge">{human_size(cell.size_bytes)}</span>'
            f'</div>'
            f'<div class="cc-stats">'
            f'<div class="cc-stat"><div class="k">Cycles</div><div class="v">{cell.cycle_count or "—"}</div></div>'
            f'<div class="cc-stat"><div class="k">Range</div><div class="v">{cycle_range}</div></div>'
            f'<div class="cc-stat"><div class="k">Peak DChg</div><div class="v">{peak}</div></div>'
            f'<div class="cc-stat"><div class="k">Max CE</div><div class="v">{coul}</div></div>'
            f'</div>'
            f'<div class="cc-footer">'
            f'<div class="cc-status{status_cls}"><span class="dot"></span><span>{status_lbl}</span></div>'
            f'<span>Started {started}</span>'
            f'</div>'
        )
        if cell.status == 'error' and cell.error:
            ui.html(
                f'<div style="color: var(--danger); font-size: 11px; '
                f'background: color-mix(in srgb, var(--danger) 8%, transparent); '
                f'padding: 6px 10px; border-radius: 6px; margin-top: -4px;">'
                f'{cell.error}</div>'
            )

    def open_card():
        if cell.status == 'ready':
            navigate_to_analysis(cell.name)
        elif cell.status == 'error':
            ui.notify(f"{cell.name}: {cell.error or 'parse failed'}", type='negative')
        else:
            ui.notify(f"{cell.name} is still parsing", type='info')

    card.on('click', lambda _: open_card())
