"""Bloomberg-terminal aesthetic for NiceGUI.

Color tokens, typography, and reusable UI primitives. Importing this module
applies the global theme to the running NiceGUI app.
"""
from nicegui import ui

# ─── Color tokens ─────────────────────────────────────────────────────────────
BG          = "#050505"
BG_PANEL    = "#0a0a0a"
BG_ELEV     = "#0f0f0f"
BORDER      = "#1a1a1a"
BORDER_HI   = "#2a2a2a"

TEXT        = "#e6e6e6"
TEXT_DIM    = "#8a8a8a"
TEXT_MUTED  = "#5a5a5a"

AMBER       = "#ffb000"   # primary accent (active state, headlines)
AMBER_DIM   = "#8a5f00"
CYAN        = "#00d9ff"   # secondary data / compare cell
GREEN       = "#00ff7f"   # positive
RED         = "#ff4d4d"   # negative
MAGENTA     = "#ff5dff"   # tertiary

MONO_FONT   = "'JetBrains Mono', 'IBM Plex Mono', 'Consolas', monospace"

# ─── Global stylesheet ────────────────────────────────────────────────────────
_GLOBAL_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

:root {{
    --bg: {BG};
    --bg-panel: {BG_PANEL};
    --bg-elev: {BG_ELEV};
    --border: {BORDER};
    --border-hi: {BORDER_HI};
    --text: {TEXT};
    --text-dim: {TEXT_DIM};
    --text-muted: {TEXT_MUTED};
    --amber: {AMBER};
    --cyan: {CYAN};
    --green: {GREEN};
    --red: {RED};
}}

html, body, .nicegui-content, .q-page {{
    background: {BG} !important;
    color: {TEXT};
    font-family: {MONO_FONT};
    font-size: 13px;
    letter-spacing: 0.01em;
    -webkit-font-smoothing: antialiased;
}}

.q-page {{ padding: 0 !important; }}
.nicegui-content {{ padding: 0 !important; gap: 0 !important; }}

/* Selection */
::selection {{ background: {AMBER}; color: {BG}; }}

/* Scrollbars */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER_HI}; border-radius: 0; }}
::-webkit-scrollbar-thumb:hover {{ background: {AMBER_DIM}; }}

/* Title bar */
.term-titlebar {{
    background: {BG};
    border-bottom: 1px solid {BORDER_HI};
    color: {TEXT_DIM};
    padding: 8px 16px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 18px;
    height: 36px;
    min-height: 36px;
}}
.term-titlebar .brand {{
    color: {AMBER};
    font-weight: 700;
    letter-spacing: 0.12em;
}}
.term-titlebar .sep {{
    color: {BORDER_HI};
}}
.term-titlebar .field {{
    color: {TEXT_DIM};
}}
.term-titlebar .val {{
    color: {TEXT};
    font-weight: 500;
}}
.term-titlebar .blink {{
    color: {GREEN};
    animation: blink 1.4s infinite;
}}
@keyframes blink {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.25; }}
}}

/* Sidebar nav rail */
.term-nav {{
    background: {BG_PANEL};
    border-right: 1px solid {BORDER_HI};
    width: 200px;
    min-width: 200px;
    padding: 14px 0;
    overflow-y: auto;
}}
.term-nav-section {{
    color: {TEXT_MUTED};
    font-size: 10px;
    letter-spacing: 0.14em;
    padding: 14px 16px 6px 16px;
    text-transform: uppercase;
}}
.term-nav-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 7px 16px;
    color: {TEXT_DIM};
    cursor: pointer;
    border-left: 2px solid transparent;
    font-size: 12px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    user-select: none;
    transition: background 80ms;
}}
.term-nav-item:hover {{
    background: {BG_ELEV};
    color: {TEXT};
}}
.term-nav-item.active {{
    background: {BG_ELEV};
    color: {AMBER};
    border-left-color: {AMBER};
}}
.term-nav-item .key {{
    color: {TEXT_MUTED};
    font-size: 10px;
    width: 22px;
}}
.term-nav-item.active .key {{ color: {AMBER_DIM}; }}

/* Status bar */
.term-statusbar {{
    background: {BG};
    border-top: 1px solid {BORDER_HI};
    color: {TEXT_MUTED};
    padding: 6px 14px;
    font-size: 11px;
    letter-spacing: 0.06em;
    display: flex;
    align-items: center;
    gap: 18px;
    height: 28px;
    min-height: 28px;
}}
.term-statusbar .chip {{
    color: {AMBER};
    border: 1px solid {BORDER_HI};
    padding: 1px 6px;
    text-transform: uppercase;
    font-size: 10px;
}}

/* Panel */
.term-panel {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    margin: 0;
}}
.term-panel-header {{
    border-bottom: 1px solid {BORDER};
    padding: 6px 12px;
    color: {AMBER};
    font-size: 10px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: {BG};
}}
.term-panel-header .meta {{
    color: {TEXT_MUTED};
    font-weight: 400;
    letter-spacing: 0.08em;
}}
.term-panel-body {{
    padding: 12px;
}}

/* Metric card */
.term-metric {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}}
.term-metric .lbl {{
    color: {TEXT_MUTED};
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}}
.term-metric .val {{
    color: {TEXT};
    font-size: 22px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
}}
.term-metric .val.amber {{ color: {AMBER}; }}
.term-metric .val.cyan {{ color: {CYAN}; }}
.term-metric .val.green {{ color: {GREEN}; }}
.term-metric .sub {{
    color: {TEXT_MUTED};
    font-size: 10px;
    letter-spacing: 0.08em;
}}

/* Form controls — make NiceGUI's quasar inputs look terminal */
.q-field__control {{
    background: {BG} !important;
    border-radius: 0 !important;
    color: {TEXT} !important;
    min-height: 32px !important;
    font-family: {MONO_FONT} !important;
    font-size: 12px !important;
}}
.q-field__control:before {{ border: 1px solid {BORDER_HI} !important; border-radius: 0 !important; }}
.q-field__control:after {{ border-bottom: 2px solid {AMBER} !important; }}
.q-field__native, .q-field__input {{ color: {TEXT} !important; font-family: {MONO_FONT} !important; }}
.q-field__label {{ color: {TEXT_MUTED} !important; font-size: 11px !important; letter-spacing: 0.06em; text-transform: uppercase; }}

.q-btn {{
    border-radius: 0 !important;
    font-family: {MONO_FONT} !important;
    font-size: 11px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    font-weight: 600 !important;
    border: 1px solid {BORDER_HI};
    color: {TEXT} !important;
    background: {BG_PANEL} !important;
    min-height: 28px !important;
    padding: 4px 12px !important;
    box-shadow: none !important;
}}
.q-btn:hover {{ background: {BG_ELEV} !important; border-color: {AMBER_DIM}; color: {AMBER} !important; }}
.q-btn.term-btn-primary {{ background: {AMBER_DIM} !important; color: {BG} !important; border-color: {AMBER}; }}
.q-btn.term-btn-primary:hover {{ background: {AMBER} !important; color: {BG} !important; }}

/* Checkboxes */
.q-checkbox__bg {{ border-radius: 0 !important; border: 1px solid {BORDER_HI} !important; }}
.q-checkbox__inner--truthy .q-checkbox__bg {{ background: {AMBER} !important; border-color: {AMBER} !important; }}
.q-checkbox__label {{ color: {TEXT_DIM} !important; font-size: 12px !important; }}

/* Select dropdown */
.q-menu {{
    background: {BG_PANEL} !important;
    border: 1px solid {BORDER_HI} !important;
    border-radius: 0 !important;
    color: {TEXT} !important;
    font-family: {MONO_FONT} !important;
}}
.q-item {{ color: {TEXT_DIM} !important; font-size: 12px !important; min-height: 30px !important; }}
.q-item:hover {{ background: {BG_ELEV} !important; color: {AMBER} !important; }}
.q-item--active {{ color: {AMBER} !important; background: {BG_ELEV} !important; }}

/* Radio */
.q-radio__label {{ color: {TEXT_DIM} !important; font-size: 12px !important; }}
.q-radio__inner {{ color: {AMBER} !important; }}

/* Toggle bar (radio buttons rendered horizontally) */
.term-toggle .q-btn {{ border-radius: 0 !important; }}
.term-toggle .q-btn--active {{ background: {AMBER_DIM} !important; color: {BG} !important; }}

/* Tables */
.term-table {{
    width: 100%;
    border-collapse: collapse;
    font-variant-numeric: tabular-nums;
    font-size: 12px;
}}
.term-table th {{
    text-align: left;
    color: {TEXT_MUTED};
    font-weight: 600;
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    padding: 8px 12px;
    border-bottom: 1px solid {BORDER_HI};
    background: {BG};
    position: sticky;
    top: 0;
    z-index: 1;
}}
.term-table td {{
    padding: 6px 12px;
    border-bottom: 1px solid {BORDER};
    color: {TEXT};
}}
.term-table tr:hover td {{ background: {BG_ELEV}; }}
.term-table td.num {{ text-align: right; }}

/* NiceGUI ag-grid overrides */
.ag-theme-balham-dark, .ag-theme-balham {{
    --ag-background-color: {BG_PANEL};
    --ag-header-background-color: {BG};
    --ag-odd-row-background-color: {BG_PANEL};
    --ag-row-hover-color: {BG_ELEV};
    --ag-border-color: {BORDER};
    --ag-secondary-border-color: {BORDER};
    --ag-foreground-color: {TEXT};
    --ag-header-foreground-color: {TEXT_MUTED};
    --ag-font-family: {MONO_FONT};
    --ag-font-size: 12px;
    --ag-header-column-separator-color: {BORDER};
}}

/* Plotly modebar */
.modebar {{ background: transparent !important; }}
.modebar-btn path {{ fill: {TEXT_MUTED} !important; }}
.modebar-btn:hover path {{ fill: {AMBER} !important; }}

/* Welcome screen / empty state */
.term-empty {{
    color: {TEXT_MUTED};
    font-size: 12px;
    letter-spacing: 0.06em;
    padding: 80px 40px;
    text-align: center;
}}
.term-empty .ascii {{
    color: {AMBER};
    font-size: 11px;
    line-height: 1.3;
    white-space: pre;
    margin-bottom: 24px;
}}

/* Headings */
.term-h2 {{
    color: {AMBER};
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    padding-bottom: 8px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 14px;
}}

/* Inline KV display */
.term-kv {{
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 4px 18px;
    font-size: 12px;
}}
.term-kv .k {{
    color: {TEXT_MUTED};
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 10px;
    padding-top: 2px;
}}
.term-kv .v {{ color: {TEXT}; }}

/* Tag */
.term-tag {{
    display: inline-block;
    border: 1px solid {BORDER_HI};
    color: {AMBER};
    padding: 1px 6px;
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}
.term-tag.cyan {{ color: {CYAN}; border-color: {CYAN}; }}
.term-tag.dim  {{ color: {TEXT_MUTED}; }}

/* Loading overlay */
.term-loading {{
    background: {BG};
    color: {AMBER};
    text-align: center;
    padding: 24px;
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border: 1px dashed {BORDER_HI};
}}
"""


def apply_theme() -> None:
    """Install global CSS + favicon. Call once at app startup."""
    ui.add_head_html(f"<style>{_GLOBAL_CSS}</style>")
    ui.add_head_html(
        '<link rel="icon" href="data:image/svg+xml,'
        '<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 64%22>'
        '<rect width=%2264%22 height=%2264%22 fill=%22%23050505%22/>'
        '<text x=%2232%22 y=%2244%22 font-family=%22monospace%22 font-size=%2244%22 '
        f'font-weight=%22700%22 text-anchor=%22middle%22 fill=%22%23ffb000%22>Z</text>'
        '</svg>">'
    )


def panel(title: str, meta: str = "") -> ui.element:
    """Bordered panel with a terminal-style header bar. Returns the body container."""
    outer = ui.element('div').classes('term-panel')
    with outer:
        with ui.element('div').classes('term-panel-header'):
            ui.html(f'<span>{title}</span>'
                    f'<span class="meta">{meta}</span>')
        body = ui.element('div').classes('term-panel-body')
    return body


def metric(label: str, value: str, sub: str = "", tone: str = "") -> None:
    """Single metric card. tone in {'', 'amber', 'cyan', 'green'}."""
    klass = f"val {tone}".strip()
    ui.html(
        f'<div class="term-metric">'
        f'<div class="lbl">{label}</div>'
        f'<div class="{klass}">{value}</div>'
        f'<div class="sub">{sub}</div>'
        f'</div>'
    )


def kv(pairs: list[tuple[str, str]]) -> None:
    """Inline key-value list (terminal style)."""
    rows = ''.join(f'<div class="k">{k}</div><div class="v">{v}</div>' for k, v in pairs)
    ui.html(f'<div class="term-kv">{rows}</div>')


def h2(text: str) -> None:
    """Terminal-styled section heading."""
    ui.html(f'<div class="term-h2">// {text}</div>')


def tag(text: str, tone: str = "") -> str:
    """Return HTML for an inline tag chip."""
    return f'<span class="term-tag {tone}">{text}</span>'
