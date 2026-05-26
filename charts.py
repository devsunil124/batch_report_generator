"""Plotly chart factories themed for the terminal aesthetic.

All charts return go.Figure objects with the dark/amber/cyan palette.
"""
import plotly.graph_objects as go
import plotly.express as px

# Terminal palette (mirrors theme.py)
BG          = "#050505"
PANEL       = "#0a0a0a"
GRID        = "#161616"
AXIS        = "#2a2a2a"
TEXT        = "#c8c8c8"
TEXT_DIM    = "#7a7a7a"
AMBER       = "#ffb000"
CYAN        = "#00d9ff"
GREEN       = "#00ff7f"
RED         = "#ff4d4d"
MAGENTA     = "#ff5dff"

PRIMARY = AMBER
COMPARE = CYAN

MONO = "JetBrains Mono, IBM Plex Mono, Consolas, monospace"


def base_layout(xtitle: str, ytitle: str, height: int | None = None) -> dict:
    """Standard terminal layout — dark, monospace, dim axis labels."""
    return dict(
        xaxis=dict(
            title=dict(text=xtitle.upper(), font=dict(size=10, color=TEXT_DIM, family=MONO)),
            showgrid=True, gridcolor=GRID, gridwidth=1,
            zeroline=False,
            tickfont=dict(size=10, color=TEXT_DIM, family=MONO),
            linecolor=AXIS, linewidth=1, mirror=False,
            ticks="outside", tickcolor=AXIS, ticklen=4,
        ),
        yaxis=dict(
            title=dict(text=ytitle.upper(), font=dict(size=10, color=TEXT_DIM, family=MONO)),
            showgrid=True, gridcolor=GRID, gridwidth=1,
            zeroline=False,
            tickfont=dict(size=10, color=TEXT_DIM, family=MONO),
            linecolor=AXIS, linewidth=1, mirror=False,
            ticks="outside", tickcolor=AXIS, ticklen=4,
        ),
        plot_bgcolor=PANEL,
        paper_bgcolor=PANEL,
        font=dict(family=MONO, size=11, color=TEXT),
        margin=dict(l=58, r=20, t=22, b=44),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(size=10, color=TEXT_DIM, family=MONO),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="closest",
        hoverlabel=dict(
            bgcolor=BG, bordercolor=AMBER,
            font=dict(family=MONO, size=11, color=TEXT),
        ),
        height=height,
    )


def line_chart(
    rp, col_prim: str, primary_name: str,
    rs=None, col_sec: str | None = None, secondary_name: str = "",
    xtitle: str = "Cycle", ytitle: str = "Value",
    height: int = 280,
) -> go.Figure:
    """Two-series line chart for trends."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rp['Cycle no'], y=rp[col_prim],
        mode='lines+markers', name=primary_name,
        line=dict(color=PRIMARY, width=1.4),
        marker=dict(size=4, color=PRIMARY, line=dict(width=0)),
        hovertemplate="cyc %{x}<br>%{y}<extra></extra>",
    ))
    if rs is not None and col_sec:
        fig.add_trace(go.Scatter(
            x=rs['Cycle no'], y=rs[col_sec],
            mode='lines+markers', name=secondary_name,
            line=dict(color=COMPARE, width=1.4),
            marker=dict(size=4, color=COMPARE, line=dict(width=0)),
            hovertemplate="cyc %{x}<br>%{y}<extra></extra>",
        ))
    fig.update_layout(**base_layout(xtitle, ytitle, height=height))
    return fig


def vc_traces(df_raw, cycle_list, colorscale: str, label_suffix: str = "",
              single_color: str | None = None) -> list:
    """Voltage vs capacity traces (charge solid, discharge dotted)."""
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
                mode='lines', line=dict(color=col, width=1.1),
                name=f"All{label_suffix}" if (single_color and is_first) else name,
                legendgroup=leg_group, showlegend=show_leg,
                hovertemplate=f"{name} chg<br>%{{x:.2f}} mAh<br>%{{y:.3f}} V<extra></extra>",
            ))
        if not dchg.empty:
            out.append(go.Scatter(
                x=dchg['Discharge_Capacity(mAh)'], y=dchg['Voltage'],
                mode='lines', line=dict(color=col, width=1.1, dash='dot'),
                name=name + " v",
                legendgroup=leg_group, showlegend=False,
                hovertemplate=f"{name} dchg<br>%{{x:.2f}} mAh<br>%{{y:.3f}} V<extra></extra>",
            ))
    return out


def vc_figure(traces: list, title: str = "", height: int = 520, side_legend: bool = True) -> go.Figure:
    """Wrap traces into a Voltage-vs-Capacity figure with terminal layout."""
    fig = go.Figure()
    for tr in traces:
        fig.add_trace(tr)
    layout = base_layout("Capacity (mAh)", "Voltage (V)", height=height)
    if title:
        layout['title'] = dict(
            text=title.upper(),
            font=dict(size=11, color=AMBER, family=MONO),
            x=0.01, y=0.98, xanchor="left", yanchor="top",
        )
    fig.update_layout(**layout)
    if side_legend:
        fig.update_layout(legend=dict(
            orientation="v", yanchor="top", y=1, xanchor="left", x=1.02,
            font=dict(size=9, color=TEXT_DIM, family=MONO),
        ))
    return fig


def mini_preview(traces: list, height: int = 160) -> go.Figure:
    """Compact preview figure: no axes, no legend, just the line."""
    fig = go.Figure()
    for tr in traces:
        fig.add_trace(tr)
    fig.update_layout(
        plot_bgcolor=PANEL, paper_bgcolor=PANEL,
        margin=dict(l=0, r=0, t=0, b=0),
        height=height, showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        font=dict(family=MONO, size=10, color=TEXT_DIM),
    )
    return fig
