"""ZnBr Analytics — entrypoint, top nav, page router."""
from __future__ import annotations
from nicegui import ui, app

import theme
from state import state
from views import home, analysis


APP_NAME = "ZnBr Analytics"
APP_VER = "v2.0"


def _theme_toggle_button() -> None:
    """Sun/moon icon button — flips data-theme attribute and mirrors to python."""
    ui.html(
        '<button class="zn-icon-btn" id="zn-theme-btn" title="Toggle theme" '
        'aria-label="Toggle theme" onclick="'
        'var next = znToggleTheme();'
        'this.innerHTML = next === \'dark\' ? \'☀\' : \'☾\';'
        'fetch(\'/_zn_theme/\' + next, {method: \'POST\'});'
        '">☾</button>'
    )


def _top_nav(active: str) -> None:
    with ui.element('nav').classes('zn-nav'):
        # Brand
        ui.html(
            f'<a href="/" class="zn-brand">'
            f'  <span class="logo">Zn</span>'
            f'  <span class="name">{APP_NAME}</span>'
            f'  <span class="ver">{APP_VER}</span>'
            f'</a>'
        )
        # Tabs
        nav_links = [('home', '/', 'Home'), ('analysis', '/analysis', 'Analysis')]
        tabs_html = ''.join(
            f'<a href="{href}" class="zn-nav-tab{" active" if key == active else ""}">{label}</a>'
            for key, href, label in nav_links
        )
        ui.html(f'<div class="zn-nav-tabs">{tabs_html}</div>')

        # Right side actions
        with ui.element('div').classes('zn-nav-actions'):
            _theme_toggle_button()


def _footer() -> None:
    ui.html(
        '<footer class="zn-footer">'
        f'<span>{APP_NAME} {APP_VER}</span> · '
        '<span>Files stored locally in <code style="background:var(--surface-2); padding:1px 6px; border-radius:4px;">./library/</code></span>'
        '</footer>'
    )


# ─── Server-side theme mirror ────────────────────────────────────────────────
# The browser is the source of truth; we POST changes to /_zn_theme/<name> so
# Python knows which theme is active when generating Plotly figures.
@app.post('/_zn_theme/{name}')
def _set_theme(name: str) -> dict:
    if name in ('light', 'dark'):
        state.theme = name
    return {'ok': True, 'theme': state.theme}


def _theme_sync_script() -> None:
    """On page load: POST the current theme to the server (so Plotly figures
    use the right palette) and set the toggle button glyph (sun/moon)."""
    ui.add_body_html(
        '<script>'
        'window.addEventListener("DOMContentLoaded", function(){'
        '  var t = znCurrentTheme();'
        '  fetch("/_zn_theme/" + t, {method: "POST"});'
        '  var b = document.getElementById("zn-theme-btn");'
        '  if (b) b.innerHTML = t === "dark" ? "\\u2600" : "\\u263E";'
        '});'
        '</script>'
    )


# ─── Pages ────────────────────────────────────────────────────────────────────
@ui.page('/')
def page_home() -> None:
    theme.apply_theme()
    _theme_sync_script()
    _top_nav(active='home')

    def navigate_to_analysis(cell_name: str) -> None:
        ui.navigate.to(f'/analysis?cell={cell_name}')

    home.render(navigate_to_analysis)
    _footer()


@ui.page('/analysis')
def page_analysis(cell: str | None = None) -> None:
    theme.apply_theme()
    _theme_sync_script()
    _top_nav(active='analysis')

    def go_home() -> None:
        ui.navigate.to('/')

    analysis.render(initial_cell=cell, navigate_home=go_home)
    _footer()


# ─── Bootstrap ────────────────────────────────────────────────────────────────
if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title=APP_NAME,
        favicon="🔋",
        dark=None,           # follow system / data-theme; we manage it ourselves
        port=8765,
        reload=False,
        show=True,
        storage_secret='znbr-analytics-local',
    )
