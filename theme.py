"""Light + dark theme with electric-blue accent for ZnBr Analytics.

Single source of truth for design tokens. All colors flow through CSS variables
on `body`, so flipping the `data-theme` attribute swaps the entire UI without
re-rendering. Plotly charts read the active theme tokens via `get_palette()`.
"""
from __future__ import annotations
from nicegui import ui

FONT_STACK = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
MONO_STACK = "'JetBrains Mono', 'Consolas', monospace"

# ─── Design tokens ────────────────────────────────────────────────────────────
LIGHT = dict(
    bg          = "#fafafa",
    surface     = "#ffffff",
    surface_2   = "#f5f5f7",
    surface_hi  = "#ffffff",
    border      = "#e5e7eb",
    border_hi   = "#d1d5db",
    text        = "#0a0a0a",
    text_dim    = "#525252",
    text_muted  = "#a1a1aa",
    accent      = "#2563eb",
    accent_hi   = "#1d4ed8",
    accent_soft = "#dbeafe",
    success     = "#059669",
    warn        = "#d97706",
    danger      = "#dc2626",
    chart_grid  = "#f1f5f9",
    chart_axis  = "#e2e8f0",
    shadow      = "0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 12px rgba(15, 23, 42, 0.06)",
)

DARK = dict(
    bg          = "#0a0a0a",
    surface     = "#121212",
    surface_2   = "#0f0f0f",
    surface_hi  = "#1a1a1a",
    border      = "#262626",
    border_hi   = "#3a3a3a",
    text        = "#f5f5f5",
    text_dim    = "#a1a1aa",
    text_muted  = "#71717a",
    accent      = "#60a5fa",
    accent_hi   = "#93c5fd",
    accent_soft = "#1e3a8a33",
    success     = "#34d399",
    warn        = "#fbbf24",
    danger      = "#f87171",
    chart_grid  = "#1f1f1f",
    chart_axis  = "#2a2a2a",
    shadow      = "0 1px 2px rgba(0,0,0,0.4), 0 4px 12px rgba(0,0,0,0.5)",
)


def _vars(d: dict) -> str:
    return "\n".join(f"    --{k.replace('_','-')}: {v};" for k, v in d.items())


# ─── Stylesheet ───────────────────────────────────────────────────────────────
_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root[data-theme="light"] {{
{_vars(LIGHT)}
}}
:root[data-theme="dark"] {{
{_vars(DARK)}
}}

* {{ box-sizing: border-box; }}
html, body {{
    background: var(--bg);
    color: var(--text);
    font-family: {FONT_STACK};
    font-size: 14px;
    -webkit-font-smoothing: antialiased;
    margin: 0;
    transition: background-color 200ms ease, color 200ms ease;
}}
.nicegui-content {{ padding: 0 !important; gap: 0 !important; background: var(--bg); }}
.q-page {{ padding: 0 !important; background: var(--bg); min-height: 100vh; }}

::selection {{ background: var(--accent-soft); color: var(--accent-hi); }}
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 5px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--border-hi); }}

/* ── Top nav ──────────────────────────────────────────────────────── */
.zn-nav {{
    position: sticky; top: 0; z-index: 50;
    background: color-mix(in srgb, var(--surface) 90%, transparent);
    backdrop-filter: saturate(180%) blur(12px);
    -webkit-backdrop-filter: saturate(180%) blur(12px);
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px;
    height: 60px;
}}
.zn-brand {{
    display: flex; align-items: center; gap: 12px;
    text-decoration: none; color: var(--text);
}}
.zn-brand .logo {{
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hi) 100%);
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 700; font-size: 16px;
    box-shadow: 0 2px 8px color-mix(in srgb, var(--accent) 40%, transparent);
}}
.zn-brand .name {{
    font-size: 16px; font-weight: 700; letter-spacing: -0.01em;
}}
.zn-brand .ver {{
    font-size: 11px; color: var(--text-muted); font-family: {MONO_STACK};
    border: 1px solid var(--border); padding: 1px 6px; border-radius: 4px;
}}

.zn-nav-tabs {{ display: flex; gap: 4px; }}
.zn-nav-tab {{
    color: var(--text-dim); padding: 8px 14px; border-radius: 8px;
    font-size: 13px; font-weight: 500; cursor: pointer; user-select: none;
    transition: all 120ms ease; text-decoration: none;
}}
.zn-nav-tab:hover {{ color: var(--text); background: var(--surface-2); }}
.zn-nav-tab.active {{ color: var(--accent); background: var(--accent-soft); }}

.zn-nav-actions {{ display: flex; align-items: center; gap: 8px; }}
.zn-icon-btn {{
    width: 36px; height: 36px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    border: 1px solid var(--border); background: var(--surface);
    color: var(--text-dim); cursor: pointer; user-select: none;
    transition: all 120ms ease; font-size: 14px;
}}
.zn-icon-btn:hover {{ color: var(--text); border-color: var(--border-hi); background: var(--surface-2); }}

/* ── Layout containers ─────────────────────────────────────────────── */
.zn-page {{
    max-width: 1400px; margin: 0 auto; padding: 32px 24px 80px;
}}
.zn-page-narrow {{ max-width: 1100px; }}

/* ── Hero / page header ────────────────────────────────────────────── */
.zn-hero {{
    margin-bottom: 32px;
}}
.zn-eyebrow {{
    color: var(--accent); font-size: 12px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;
}}
.zn-h1 {{
    font-size: 32px; font-weight: 700; letter-spacing: -0.02em;
    color: var(--text); margin: 0 0 8px 0; line-height: 1.2;
}}
.zn-lead {{
    color: var(--text-dim); font-size: 15px; line-height: 1.55; max-width: 680px;
}}
.zn-h2 {{
    font-size: 18px; font-weight: 600; letter-spacing: -0.01em;
    color: var(--text); margin: 0; line-height: 1.3;
}}
.zn-h3 {{
    font-size: 13px; font-weight: 600; letter-spacing: 0.02em;
    color: var(--text-dim); text-transform: uppercase; margin: 0;
}}

/* ── Card ──────────────────────────────────────────────────────────── */
.zn-card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px;
    transition: border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
}}
.zn-card.elev {{ box-shadow: var(--shadow); }}
.zn-card.interactive {{ cursor: pointer; }}
.zn-card.interactive:hover {{
    border-color: var(--accent); box-shadow: var(--shadow);
    transform: translateY(-1px);
}}
.zn-card-header {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 16px; gap: 12px;
}}

/* ── Metric tile ───────────────────────────────────────────────────── */
.zn-metric {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 18px 20px;
    display: flex; flex-direction: column; gap: 6px;
    transition: border-color 120ms ease;
}}
.zn-metric .lbl {{
    font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; color: var(--text-muted);
}}
.zn-metric .val {{
    font-size: 26px; font-weight: 700; letter-spacing: -0.02em;
    color: var(--text); font-variant-numeric: tabular-nums; line-height: 1.1;
    font-family: {MONO_STACK};
}}
.zn-metric .val.accent {{ color: var(--accent); }}
.zn-metric .val.success {{ color: var(--success); }}
.zn-metric .val.warn {{ color: var(--warn); }}
.zn-metric .sub {{
    font-size: 12px; color: var(--text-muted); font-variant-numeric: tabular-nums;
}}

/* ── Buttons (q-btn overrides) ─────────────────────────────────────── */
.q-btn {{
    border-radius: 8px !important;
    font-family: {FONT_STACK} !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    box-shadow: none !important;
    min-height: 36px !important;
    padding: 0 14px !important;
    color: var(--text) !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
}}
.q-btn:hover {{ background: var(--surface-2) !important; border-color: var(--border-hi) !important; }}
.q-btn.zn-primary {{
    background: var(--accent) !important;
    color: #fff !important;
    border-color: var(--accent) !important;
}}
.q-btn.zn-primary:hover {{ background: var(--accent-hi) !important; border-color: var(--accent-hi) !important; }}
.q-btn.zn-ghost {{
    background: transparent !important;
    border-color: transparent !important;
    color: var(--text-dim) !important;
}}
.q-btn.zn-ghost:hover {{ color: var(--text) !important; background: var(--surface-2) !important; }}
.q-btn.zn-danger {{
    background: transparent !important;
    border-color: var(--border) !important;
    color: var(--danger) !important;
}}
.q-btn.zn-danger:hover {{ background: color-mix(in srgb, var(--danger) 10%, transparent) !important; }}

/* ── Form controls (quasar overrides) ──────────────────────────────── */
.q-field__control {{
    background: var(--surface) !important;
    border-radius: 8px !important;
    min-height: 38px !important;
    font-family: {FONT_STACK} !important;
    color: var(--text) !important;
}}
.q-field__control:before {{ border: 1px solid var(--border) !important; border-radius: 8px !important; }}
.q-field__control:hover:before {{ border-color: var(--border-hi) !important; }}
.q-field__control:after {{ border-bottom: 2px solid var(--accent) !important; border-radius: 0 0 8px 8px !important; }}
.q-field__native, .q-field__input {{ color: var(--text) !important; }}
.q-field__label {{ color: var(--text-muted) !important; font-size: 13px !important; font-family: {FONT_STACK} !important; }}

.q-menu {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    box-shadow: var(--shadow) !important;
    font-family: {FONT_STACK} !important;
}}
.q-item {{ color: var(--text-dim) !important; min-height: 36px !important; }}
.q-item:hover, .q-item--active {{ background: var(--surface-2) !important; color: var(--accent) !important; }}
.q-checkbox__bg {{ border-radius: 4px !important; border: 1px solid var(--border-hi) !important; }}
.q-checkbox__inner--truthy .q-checkbox__bg {{ background: var(--accent) !important; border-color: var(--accent) !important; }}
.q-checkbox__label, .q-radio__label {{ color: var(--text-dim) !important; }}

/* ── Tabs (Quasar QTabs override) ──────────────────────────────────── */
.zn-tabs .q-tab {{
    color: var(--text-dim) !important;
    font-family: {FONT_STACK} !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    padding: 0 18px !important;
    min-height: 44px !important;
}}
.zn-tabs .q-tab--active {{ color: var(--accent) !important; }}
.zn-tabs .q-tab__indicator {{ background: var(--accent) !important; height: 2px !important; }}
.zn-tabs .q-tabs__content {{ border-bottom: 1px solid var(--border); }}

/* ── Upload dropzone ───────────────────────────────────────────────── */
.zn-drop {{
    border: 2px dashed var(--border-hi);
    border-radius: 14px;
    padding: 48px 32px;
    text-align: center;
    background: var(--surface);
    transition: all 160ms ease;
}}
.zn-drop:hover, .zn-drop.dragover {{
    border-color: var(--accent);
    background: color-mix(in srgb, var(--accent-soft) 50%, var(--surface));
}}
.zn-drop .icon {{
    width: 56px; height: 56px; border-radius: 14px; margin: 0 auto 16px;
    background: var(--accent-soft); color: var(--accent);
    display: flex; align-items: center; justify-content: center;
    font-size: 24px;
}}
.zn-drop h3 {{ margin: 0 0 6px; font-size: 16px; font-weight: 600; color: var(--text); }}
.zn-drop p {{ margin: 0; color: var(--text-dim); font-size: 13px; }}

/* Hide NiceGUI upload native control; we trigger it programmatically */
.zn-hidden-upload {{ display: none !important; }}

/* ── Cell card ─────────────────────────────────────────────────────── */
.zn-cell-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
    cursor: pointer;
    transition: all 140ms ease;
    display: flex; flex-direction: column; gap: 12px;
}}
.zn-cell-card:hover {{
    border-color: var(--accent);
    box-shadow: var(--shadow);
    transform: translateY(-2px);
}}
.zn-cell-card .cc-top {{
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
}}
.zn-cell-card .cc-name {{
    font-size: 15px; font-weight: 600; color: var(--text);
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-family: {MONO_STACK};
}}
.zn-cell-card .cc-badge {{
    font-size: 10px; padding: 2px 8px; border-radius: 999px;
    background: var(--accent-soft); color: var(--accent);
    font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
    white-space: nowrap;
}}
.zn-cell-card .cc-stats {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 8px 14px;
    font-size: 12px;
}}
.zn-cell-card .cc-stat .k {{ color: var(--text-muted); font-size: 11px; }}
.zn-cell-card .cc-stat .v {{ color: var(--text); font-weight: 500; font-variant-numeric: tabular-nums; }}
.zn-cell-card .cc-footer {{
    display: flex; align-items: center; justify-content: space-between;
    color: var(--text-muted); font-size: 11px;
    border-top: 1px solid var(--border); padding-top: 10px;
}}
.zn-cell-card .cc-status {{ display: flex; align-items: center; gap: 6px; }}
.zn-cell-card .cc-status .dot {{
    width: 6px; height: 6px; border-radius: 50%; background: var(--success);
}}
.zn-cell-card .cc-status.parsing .dot {{ background: var(--warn); animation: pulse 1.4s infinite; }}
.zn-cell-card .cc-status.error .dot {{ background: var(--danger); }}
@keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}

/* ── Empty state ───────────────────────────────────────────────────── */
.zn-empty {{
    text-align: center; padding: 64px 24px; color: var(--text-muted);
}}
.zn-empty h3 {{ color: var(--text-dim); margin: 0 0 6px; font-size: 16px; font-weight: 600; }}
.zn-empty p {{ margin: 0; font-size: 13px; }}

/* ── Tables ────────────────────────────────────────────────────────── */
.zn-table {{
    width: 100%; border-collapse: collapse;
    font-size: 13px; font-variant-numeric: tabular-nums;
}}
.zn-table th {{
    text-align: left; padding: 12px 14px;
    font-size: 11px; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.04em;
    border-bottom: 1px solid var(--border);
    background: var(--surface-2); position: sticky; top: 0; z-index: 1;
}}
.zn-table td {{
    padding: 10px 14px; color: var(--text);
    border-bottom: 1px solid var(--border);
}}
.zn-table tr:last-child td {{ border-bottom: none; }}
.zn-table tr:hover td {{ background: var(--surface-2); }}
.zn-table td.num, .zn-table th.num {{ text-align: right; font-family: {MONO_STACK}; }}

/* ── KV list ──────────────────────────────────────────────────────── */
.zn-kv {{ display: grid; grid-template-columns: max-content 1fr; gap: 8px 20px; font-size: 13px; }}
.zn-kv .k {{ color: var(--text-muted); font-size: 12px; }}
.zn-kv .v {{ color: var(--text); }}

/* ── Pill / chip ───────────────────────────────────────────────────── */
.zn-chip {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 3px 9px; border-radius: 999px;
    background: var(--surface-2); border: 1px solid var(--border);
    font-size: 11px; color: var(--text-dim);
}}
.zn-chip.accent {{ background: var(--accent-soft); border-color: transparent; color: var(--accent); }}
.zn-chip.success {{ background: color-mix(in srgb, var(--success) 12%, transparent); border-color: transparent; color: var(--success); }}

/* ── Toolbar (for analysis page top) ───────────────────────────────── */
.zn-toolbar {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 12px 16px;
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
}}
.zn-toolbar .group {{ display: flex; align-items: center; gap: 8px; }}
.zn-toolbar .group .lbl {{
    font-size: 11px; color: var(--text-muted); text-transform: uppercase;
    letter-spacing: 0.05em; font-weight: 600;
}}

/* ── Footer ────────────────────────────────────────────────────────── */
.zn-footer {{
    border-top: 1px solid var(--border); padding: 20px 24px;
    text-align: center; color: var(--text-muted); font-size: 12px;
    background: var(--surface);
}}

/* ── Plotly modebar polish ─────────────────────────────────────────── */
.modebar {{ background: transparent !important; }}
.modebar-btn path {{ fill: var(--text-muted) !important; }}
.modebar-btn:hover path {{ fill: var(--accent) !important; }}

/* ── Theme transition smoother (only for trip-up cases) ─────────────── */
.no-transition, .no-transition * {{ transition: none !important; }}
"""

# Theme bootstrap script — runs early, reads localStorage, applies theme.
_BOOTSTRAP_JS = """
(function() {
    var saved = localStorage.getItem('zn-theme');
    var pref = (saved === 'light' || saved === 'dark')
        ? saved
        : (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', pref);
})();
"""

# Toggle function: flips theme and notifies python via a custom event.
_TOGGLE_JS = """
function znToggleTheme() {
    var cur = document.documentElement.getAttribute('data-theme') || 'light';
    var next = (cur === 'light') ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('zn-theme', next);
    document.dispatchEvent(new CustomEvent('zn-theme-changed', { detail: next }));
    return next;
}
function znCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'light';
}
"""


def apply_theme() -> None:
    """Install CSS + theme bootstrap. Call once per page."""
    ui.add_head_html(f"<style>{_CSS}</style>")
    ui.add_head_html(f"<script>{_BOOTSTRAP_JS}</script>")
    ui.add_body_html(f"<script>{_TOGGLE_JS}</script>")


def get_palette(theme: str) -> dict:
    """Return the color dict for the named theme — used by charts."""
    return DARK if theme == "dark" else LIGHT
