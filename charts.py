"""Plotly chart factories — theme-aware (light or dark).

Each factory takes a `theme` arg ('light' or 'dark') and reads the matching
palette from theme.py. Callers regenerate the figure when the user toggles
themes.
"""
from __future__ import annotations
import plotly.graph_objects as go
import plotly.express as px

from theme import get_palette

PRIMARY = "primary"   # logical role → resolved to accent color
COMPARE = "compare"   # → cyan in light, sky-blue in dark

MONO = "JetBrains Mono, Consolas, monospace"
SANS = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"


def _colors(theme: str) -> dict:
    p = get_palette(theme)
    return dict(
        bg=p['surface'],
        paper=p['surface'],
        grid=p['chart_grid'],
        axis=p['chart_axis'],
        text=p['text'],
        text_dim=p['text_dim'],
        text_muted=p['text_muted'],
        primary=p['accent'],
        compare="#06b6d4" if theme == "light" else "#22d3ee",
        success=p['success'],
        warn=p['warn'],
    )


def base_layout(xtitle: str, ytitle: str, theme: str, height: int | None = None) -> dict:
    c = _colors(theme)
    return dict(
        xaxis=dict(
            title=dict(text=xtitle, font=dict(size=11, color=c['text_dim'], family=SANS)),
            showgrid=True, gridcolor=c['grid'], gridwidth=1,
            zeroline=False,
            tickfont=dict(size=11, color=c['text_dim'], family=MONO),
            linecolor=c['axis'], linewidth=1, mirror=False,
            ticks="outside", tickcolor=c['axis'], ticklen=4,
        ),
        yaxis=dict(
            title=dict(text=ytitle, font=dict(size=11, color=c['text_dim'], family=SANS)),
            showgrid=True, gridcolor=c['grid'], gridwidth=1,
            zeroline=False,
            tickfont=dict(size=11, color=c['text_dim'], family=MONO),
            linecolor=c['axis'], linewidth=1, mirror=False,
            ticks="outside", tickcolor=c['axis'], ticklen=4,
        ),
        plot_bgcolor=c['bg'],
        paper_bgcolor=c['paper'],
        font=dict(family=SANS, size=12, color=c['text']),
        margin=dict(l=58, r=20, t=22, b=48),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(size=11, color=c['text_dim'], family=SANS),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="closest",
        hoverlabel=dict(
            bgcolor=c['paper'], bordercolor=c['primary'],
            font=dict(family=SANS, size=12, color=c['text']),
        ),
        height=height,
    )


def line_chart(
    rp, col_prim: str, primary_name: str,
    theme: str,
    rs=None, col_sec: str | None = None, secondary_name: str = "",
    xtitle: str = "Cycle", ytitle: str = "Value",
    height: int = 280,
) -> go.Figure:
    c = _colors(theme)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rp['Cycle no'], y=rp[col_prim],
        mode='lines+markers', name=primary_name,
        line=dict(color=c['primary'], width=2),
        marker=dict(size=5, color=c['primary'], line=dict(width=0)),
        hovertemplate="cycle %{x}<br>%{y}<extra></extra>",
    ))
    if rs is not None and col_sec:
        fig.add_trace(go.Scatter(
            x=rs['Cycle no'], y=rs[col_sec],
            mode='lines+markers', name=secondary_name,
            line=dict(color=c['compare'], width=2, dash='solid'),
            marker=dict(size=5, color=c['compare'], line=dict(width=0)),
            hovertemplate="cycle %{x}<br>%{y}<extra></extra>",
        ))
    fig.update_layout(**base_layout(xtitle, ytitle, theme, height=height))
    return fig


def vc_traces(df_raw, cycle_list, colorscale: str,
              label_suffix: str = "", single_color: str | None = None) -> list:
    n = len(cycle_list)
    if not n:
        return []
    if single_color:
        colors = [single_color] * n
    else:
        colors = px.colors.sample_colorscale(colorscale, [i / max(n - 1, 1) for i in range(n)])
    out = []
    for idx, cyc in enumerate(cycle_list):
        cyc_df = df_raw[df_raw['Cycle'] == cyc]
        chg  = cyc_df[cyc_df['Status'].isin(['CC_Chg', 'CCCV_Chg', 'CV_Chg'])]
        dchg = cyc_df[cyc_df['Status'].isin(['CC_DChg', 'CCCV_DChg'])]
        col  = colors[idx]
        name = f"C{int(cyc):03d}{label_suffix}"
        is_first = (idx == 0)
        leg_group = f"All{label_suffix}" if single_color else f"g{cyc}{label_suffix}"
        show_leg = is_first if single_color else True

        if not chg.empty:
            out.append(go.Scatter(
                x=chg['Charge_Capacity(mAh)'], y=chg['Voltage'],
                mode='lines', line=dict(color=col, width=1.4),
                name=f"All{label_suffix}" if (single_color and is_first) else name,
                legendgroup=leg_group, showlegend=show_leg,
                hovertemplate=f"{name} chg<br>%{{x:.2f}} mAh<br>%{{y:.3f}} V<extra></extra>",
            ))
        if not dchg.empty:
            out.append(go.Scatter(
                x=dchg['Discharge_Capacity(mAh)'], y=dchg['Voltage'],
                mode='lines', line=dict(color=col, width=1.4, dash='dot'),
                name=name + " ↓",
                legendgroup=leg_group, showlegend=False,
                hovertemplate=f"{name} dchg<br>%{{x:.2f}} mAh<br>%{{y:.3f}} V<extra></extra>",
            ))
    return out


def vc_figure(traces: list, theme: str, title: str = "",
              height: int = 520, side_legend: bool = True) -> go.Figure:
    c = _colors(theme)
    fig = go.Figure()
    for tr in traces:
        fig.add_trace(tr)
    layout = base_layout("Capacity (mAh)", "Voltage (V)", theme, height=height)
    if title:
        layout['title'] = dict(
            text=title,
            font=dict(size=13, color=c['text'], family=SANS, weight=600),
            x=0.01, y=0.98, xanchor="left", yanchor="top",
        )
    fig.update_layout(**layout)
    if side_legend:
        fig.update_layout(legend=dict(
            orientation="v", yanchor="top", y=1, xanchor="left", x=1.02,
            font=dict(size=10, color=c['text_dim'], family=SANS),
        ))
    return fig


def mini_preview(traces: list, theme: str, height: int = 120) -> go.Figure:
    c = _colors(theme)
    fig = go.Figure()
    for tr in traces:
        fig.add_trace(tr)
    fig.update_layout(
        plot_bgcolor=c['bg'], paper_bgcolor=c['paper'],
        margin=dict(l=0, r=0, t=0, b=0),
        height=height, showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        font=dict(family=SANS, size=10, color=c['text_dim']),
    )
    return fig


def primary_color(theme: str) -> str:
    return _colors(theme)['primary']


def compare_color(theme: str) -> str:
    return _colors(theme)['compare']
