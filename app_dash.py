import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import os
import glob
import pandas as pd
import plotly.graph_objects as go
import json
import diskcache
from dash import DiskcacheManager

cache = diskcache.Cache("./.diskcache")
background_callback_manager = DiskcacheManager(cache)

from data_loader import load_and_analyze, build_vc_traces
from config_manager import load_config, save_config
from ui_components import natural_sort_key, file_size_mb
from chart_helpers import chart_layout, add_grid, C1, C2

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True, background_callback_manager=background_callback_manager)
app.title = "ZnBr Battery Analysis"

# ─── LAYOUT ──────────────────────────────────────────────────────────────────
sidebar = html.Div(
    className="sidebar",
    children=[
        html.Div(
            className="sidebar-title-container",
            children=[
                html.Div("⚡", className="sidebar-icon"),
                html.Div("Cell Manager", className="sidebar-title"),
                html.Div("ZnBr Analysis Suite", className="sidebar-subtitle")
            ]
        ),
        html.Div("📂 Data Source", className="sid-head"),
        dbc.InputGroup([
            dbc.Input(id="folder-input", value=load_config(), placeholder="C:\\path\\to\\ndax"),
            dbc.Button("Load", id="btn-load-folder", color="primary", n_clicks=0)
        ], className="mb-3"),
        html.Div(id="folder-warning", className="text-warning mb-2", style={"fontSize": "0.8rem"}),
        
        html.Hr(className="my-divider"),
        html.Div("🗂 Primary Cell", className="sid-head"),
        dbc.Input(id="search-input", placeholder="Type S-20...", className="mb-2"),
        dbc.Select(id="primary-select", options=[], value=None, className="mb-2"),
        html.Div(id="primary-info", className="text-muted mb-2", style={"fontSize": "0.8rem"}),

        html.Hr(className="my-divider"),
        html.Div("⚖ Compare Cell (Optional)", className="sid-head"),
        dbc.Select(id="secondary-select", options=[], value=None, className="mb-2"),
        html.Div(id="secondary-info", className="text-muted mb-2", style={"fontSize": "0.8rem"}),
        
        dbc.Progress(id="progress-bar", value=0, max=100, striped=True, animated=True, className="mb-2", style={"display": "none", "height": "20px"}),

        html.Hr(className="my-divider"),
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    [
                        html.Div("Configuration & Changes", className="text-muted small mb-1"),
                        dbc.Textarea(id="meta-config", placeholder="Enter configuration...", className="mb-2", style={"fontSize": "0.8rem"}),
                        html.Div("Experimental Notes / Reason to Stop", className="text-muted small mb-1"),
                        dbc.Textarea(id="meta-notes", placeholder="Enter notes...", className="mb-2", style={"fontSize": "0.8rem"}),
                        dbc.Button("Save Metadata", id="btn-save-meta", color="success", size="sm", className="w-100"),
                        html.Div(id="meta-save-status", className="small mt-1 text-center")
                    ],
                    title="📝 Edit Cell Metadata",
                ),
            ],
            start_collapsed=True,
            flush=True,
            className="mb-3",
            style={"backgroundColor": "transparent"}
        ),


        html.Hr(className="my-divider"),
        html.Div("🔍 Cycle Range", className="sid-head"),
        html.Div(id="cycle-range-container"),
    ]
)

content = html.Div(
    className="main-content",
    children=[
        html.Div(
            className="hero",
            children=[
                html.Span("🔋", className="hero-icon"),
                html.Div([
                    html.Div("ZnBr Battery Analysis Dashboard", className="hero-title"),
                    html.Div("Zinc-Bromine Cell Telemetry · Professional Reporting Suite", className="hero-sub")
                ])
            ]
        ),
        dcc.Loading(
            id="loading-tabs",
            type="dot",
            children=html.Div([
                dbc.Tabs(
                    id="tabs",
                    active_tab="tab-summary",
                    children=[
                        dbc.Tab(label="📊 Summary", tab_id="tab-summary"),
                        dbc.Tab(label="📈 Trends", tab_id="tab-trends"),
                        dbc.Tab(label="🌈 Cycle Curves", tab_id="tab-curves"),
                        dbc.Tab(label="🎯 Interval Groups", tab_id="tab-intervals"),
                        dbc.Tab(label="🖥️ Full Screen Graph", tab_id="tab-full"),
                        dbc.Tab(label="📄 Raw Data", tab_id="tab-raw"),
                    ]
                ),
                html.Div(id="tab-trends-controls", style={"display": "none"}, children=[
                    html.Div("Comparison View:", className="text-muted mb-2 mt-3"),
                    dbc.RadioItems(id="trends-mode", options=[
                        {"label": "Overlay Mode", "value": "Overlay"},
                        {"label": "Side-by-Side Mode", "value": "Side-by-Side"}
                    ], value="Overlay", inline=True, className="mb-3")
                ]),
                html.Div(id="tab-curves-controls", style={"display": "none"}, children=[
                    html.Div("Select specific cycles to plot:", className="text-muted mb-2 mt-3"),
                    dbc.Row([
                        dbc.Col(dcc.Dropdown(id="curves-cycle-select", multi=True, placeholder="Select cycles...", style={"color": "black"}), width=9),
                        dbc.Col(dbc.Button("Select Outliers Only", id="btn-select-outliers", outline=True, color="warning", size="sm", className="w-100"), width=3)
                    ], className="mb-3")
                ]),
                html.Div(id="tab-interval-controls", style={"display": "none"}, children=[
                    html.Div("Each interval band uses its own color palette. 🔵 Blues = Every 5th | 🟠 Warm = Every 10th | 🟢 Greens = Every 25th", className="text-muted mb-3 mt-3"),
                    html.Div([
                        dbc.Checkbox(id="interval-5", label="Show every 5th cycle", value=True, className="d-inline-block me-3"),
                        dbc.Checkbox(id="interval-10", label="Show every 10th cycle", value=True, className="d-inline-block me-3"),
                        dbc.Checkbox(id="interval-25", label="Show every 25th cycle", value=True, className="d-inline-block me-3"),
                    ], className="mb-3")
                ]),
                html.Div(id="tab-content", className="mt-4")
            ])
        ),

        # Hidden stores
        dcc.Store(id="store-file-list"),
        dcc.Store(id="store-reports") # stores primary/secondary JSON report_df
    ]
)

app.layout = html.Div([sidebar, content])

# ─── CALLBACKS ───────────────────────────────────────────────────────────────

@app.callback(
    Output("store-file-list", "data"),
    Output("folder-warning", "children"),
    Input("btn-load-folder", "n_clicks"),
    State("folder-input", "value")
)
def load_folder(n_clicks, folder_path):
    if not folder_path or not os.path.exists(folder_path):
        return [], "Please enter a valid folder path."
    
    save_config(folder_path)
    files = glob.glob(os.path.join(folder_path, "*.ndax"))
    all_files = sorted(files, key=natural_sort_key)
    if not all_files:
        return [], "No .ndax files found in " + str(folder_path)
    
    names = [os.path.basename(os.path.splitext(f)[0]) for f in all_files]
    return names, ""
    return names, ""

@app.callback(
    Output("primary-select", "options"),
    Output("primary-select", "value"),
    Output("secondary-select", "options"),
    Input("store-file-list", "data"),
    Input("search-input", "value")
)
def update_dropdowns(file_list, search_text):
    if not file_list:
        return [], None, []
    
    filtered = file_list
    if search_text:
        filtered = [n for n in file_list if search_text.lower() in n.lower()]
    
    primary_opts = [{"label": n, "value": n} for n in filtered]
    primary_val = filtered[0] if filtered else None
    
    secondary_opts = [{"label": "— None —", "value": ""}] + [{"label": n, "value": n} for n in file_list]
    
    return primary_opts, primary_val, secondary_opts

@app.callback(
    Output("store-reports", "data"),
    Output("primary-info", "children"),
    Output("secondary-info", "children"),
    Output("cycle-range-container", "children"),
    Input("primary-select", "value"),
    Input("secondary-select", "value"),
    State("folder-input", "value"),
    background=True,
    progress=[
        Output("progress-bar", "value"),
        Output("progress-bar", "max"),
        Output("progress-bar", "style"),
        Output("progress-bar", "label")
    ],
    prevent_initial_call=True
)
def load_data(set_progress, primary_name, secondary_name, folder_path):
    if not primary_name or not folder_path:
        return no_update, "", "", ""
        
    set_progress((0, 100, {"display": "flex", "height": "20px"}, "Initializing..."))
    
    is_sec = secondary_name and secondary_name != "— None —"
    prim_weight = 50 if is_sec else 100

    def make_progress_cb(label, current_offset, weight):
        def cb(curr, total):
            ratio = curr / total if total > 0 else 0
            val = int(ratio * 100)
            pct = int(ratio * weight)
            set_progress((current_offset + pct, 100, {"display": "flex", "height": "20px"}, "{0} {1}%".format(label, val)))
        return cb
    
    prim_file = os.path.join(folder_path, "{0}.ndax".format(primary_name))
    sz_p = file_size_mb(prim_file)
    info_p = "📦 {0:.1f} MB".format(sz_p) + (" — large file" if sz_p > 10 else "")
    
    df_prim, report_prim, hit_p = load_and_analyze(prim_file, progress_callback=make_progress_cb("Prim:", 0, prim_weight))
    
    # Update info with cache status
    info_p += " | {0}".format('✅ Cache Hit' if hit_p else '🔄 Cache Miss')
    
    if report_prim is None or report_prim.empty:
        set_progress((0, 100, {"display": "none"}, ""))
        return None, info_p, "", html.Div("Error loading file.", className="text-danger")
    
    store_data = {"primary": report_prim.to_dict("records"), "primary_file": prim_file}
    
    min_c = int(report_prim['Cycle no'].min())
    max_c = int(report_prim['Cycle no'].max())
    info_s = ""
    
    if is_sec:
        sec_file = os.path.join(folder_path, "{0}.ndax".format(secondary_name))
        sz_s = file_size_mb(sec_file)
        info_s = "📦 {0:.1f} MB".format(sz_s)
        df_sec, report_sec, hit_s = load_and_analyze(sec_file, progress_callback=make_progress_cb("Sec:", 50, 50))
        
        info_s += " | {0}".format('✅ Cache Hit' if hit_s else '🔄 Cache Miss')
        
        if report_sec is not None and not report_sec.empty:
            store_data["secondary"] = report_sec.to_dict("records")
            store_data["secondary_file"] = sec_file
            min_c = min(min_c, int(report_sec['Cycle no'].min()))
            max_c = max(max_c, int(report_sec['Cycle no'].max()))

    range_ui = html.Div([
        dbc.Row([
            dbc.Col([html.Label("Start"), dbc.Input(type="number", id="cycle-start", value=min_c, min=min_c, max=max_c, step=1)]),
            dbc.Col([html.Label("End"), dbc.Input(type="number", id="cycle-end", value=max_c, min=min_c, max=max_c, step=1)])
        ])
    ])
    
    set_progress((100, 100, {"display": "none"}, ""))
    return store_data, info_p, info_s, range_ui

@app.callback(
    Output("tab-content", "children"),
    Output("tab-curves-controls", "style"),
    Output("tab-interval-controls", "style"),
    Output("tab-trends-controls", "style"),
    Input("tabs", "active_tab"),
    Input("store-reports", "data"),
    Input("cycle-start", "value"),
    Input("cycle-end", "value"),
    Input("primary-select", "value"),
    Input("secondary-select", "value"),
    Input("folder-input", "value"),
    Input("curves-cycle-select", "value"),
    Input("interval-5", "value"),
    Input("interval-10", "value"),
    Input("interval-25", "value"),
    Input("trends-mode", "value"),
    Input("btn-save-meta", "n_clicks"),
    prevent_initial_call=True
)
def render_tab_content(active_tab, store_data, c_start, c_end, p_name, s_name, folder_path, curves_selected_cycles, int5, int10, int25, trends_mode, n_clicks_meta):
    style_curves = {"display": "block"} if active_tab == "tab-curves" else {"display": "none"}
    style_interval = {"display": "block"} if active_tab == "tab-intervals" else {"display": "none"}
    style_trends = {"display": "block"} if active_tab == "tab-trends" and s_name else {"display": "none"}
    
    if not store_data or not p_name:
        return html.Div(), style_curves, style_interval, style_trends
    
    rp_all = pd.DataFrame(store_data["primary"])
    if c_start is None or c_end is None:
        c_start, c_end = rp_all['Cycle no'].min(), rp_all['Cycle no'].max()
        
    c_min, c_max = min(c_start, c_end), max(c_start, c_end)
    rp = rp_all[(rp_all['Cycle no'] >= c_min) & (rp_all['Cycle no'] <= c_max)]
    
    rs = None
    if "secondary" in store_data:
        rs_all = pd.DataFrame(store_data["secondary"])
        rs = rs_all[(rs_all['Cycle no'] >= c_min) & (rs_all['Cycle no'] <= c_max)]
        
    # Helpers for traces
    def get_dfs():
        df_prim, _, _ = load_and_analyze(store_data["primary_file"])
        dp = df_prim[(df_prim['Cycle'] >= c_min) & (df_prim['Cycle'] <= c_max)]
        ds = None
        if "secondary_file" in store_data:
            df_sec, _, _ = load_and_analyze(store_data["secondary_file"])
            ds = df_sec[(df_sec['Cycle'] >= c_min) & (df_sec['Cycle'] <= c_max)]
        return dp, ds

    if active_tab == "tab-summary":
        df_prim, _, _ = load_and_analyze(store_data["primary_file"])
        start_date = df_prim['Timestamp'].min().strftime("%B %d, %Y") if df_prim is not None and 'Timestamp' in df_prim else "Unknown"
        
        cfg, nts = "No configuration data", "No notes provided"
        meta_path = os.path.join(folder_path, "cell_metadata.csv")
        if os.path.exists(meta_path):
            try:
                meta_df = pd.read_csv(meta_path)
                meta_row = meta_df[meta_df['Cell Name'].astype(str).str.strip().str.lower() == p_name.lower()]
                if not meta_row.empty:
                    cfg = str(meta_row.iloc[0]['Configuration & Changes']).strip()
                    nts = str(meta_row.iloc[0]['Experimental Notes / Reason to Stop']).strip()
                    if cfg.lower() == 'nan': cfg = "No configuration data"
                    if nts.lower() == 'nan': nts = "No notes provided"
            except: pass
        
        meta_html = html.Div(className="metadata-box", children=[
            html.Div(className="meta-row-1", children=[html.Span("📅 Started Cycling: ", className="meta-lbl"), html.Span(start_date, className="meta-val-1")]),
            html.Div(className="meta-row-2", children=[html.Span("⚙️ Configuration: ", className="meta-lbl-2"), html.Span(cfg, className="meta-val-2")]),
            html.Div(className="meta-row-3", children=[html.Span("📝 Notes / Status: ", className="meta-lbl-2"), html.Span(nts, className="meta-val-2")]),
        ])
        
        if rp.empty:
            return html.Div([meta_html, html.Div("No data in this cycle range.", className="text-warning")])
        
        clean_s = rp[rp['Chg Capacity (Ah)'] > 0.0001]
        def get_max_cyc(col):
            s = clean_s[col].dropna()
            if s.empty: return 0.0, None
            idx = s.idxmax()
            return s[idx], int(rp.loc[idx, 'Cycle no'])

        max_dcap, cyc_dcap = get_max_cyc('DChg capacity (Ah)')
        max_ceff, cyc_ceff = get_max_cyc('Coulombic Efficiency (%)')
        max_eeff, cyc_eeff = get_max_cyc('Energy Efficiency (%)')
        avg_i = rp['Current (mA)'].mean()
        
        first_dcap = rp.iloc[0]['DChg capacity (Ah)'] if not rp.empty else 0
        last_dcap = rp.iloc[-1]['DChg capacity (Ah)'] if not rp.empty else 0
        fade_rate = (first_dcap - last_dcap) / len(rp) * 100 if not rp.empty else 0

        def make_sparkline(y_series, color="#3B82F6"):
            fig = go.Figure(go.Scatter(x=rp['Cycle no'], y=y_series, mode='lines', line=dict(color=color, width=2)))
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=60,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, visible=False, fixedrange=True),
                yaxis=dict(showgrid=False, zeroline=False, visible=False, fixedrange=True),
                showlegend=False,
                hovermode=False
            )
            return html.Div(dcc.Graph(figure=fig, config={'displayModeBar': False}, style={"height": "60px"}), style={"marginTop": "5px"})

        metrics = dbc.Row([
            dbc.Col(html.Div(className="metric-card", children=[
                html.Div("Cycles in Range", className="metric-label"), 
                html.Div("{0}".format(len(rp)), className="metric-value")
            ]), lg=2, md=4, sm=6, className="mb-2"),
            dbc.Col(html.Div(className="metric-card", children=[
                html.Div("Peak Discharge Cap.", className="metric-label"), 
                html.Div("{0:.4f} Ah".format(max_dcap), className="metric-value"), 
                html.Div("Cycle {0}".format(cyc_dcap) if cyc_dcap else "", className="metric-delta"),
                make_sparkline(rp['DChg capacity (Ah)'], "#10b981")
            ]), lg=2, md=4, sm=6, className="mb-2"),
            dbc.Col(html.Div(className="metric-card", children=[
                html.Div("Max Coulombic Eff.", className="metric-label"), 
                html.Div("{0:.2f}%".format(max_ceff), className="metric-value"), 
                html.Div("Cycle {0}".format(cyc_ceff) if cyc_ceff else "", className="metric-delta"),
                make_sparkline(rp['Coulombic Efficiency (%)'], "#3b82f6")
            ]), lg=2, md=4, sm=6, className="mb-2"),
            dbc.Col(html.Div(className="metric-card", children=[
                html.Div("Max Energy Eff.", className="metric-label"), 
                html.Div("{0:.2f}%".format(max_eeff), className="metric-value"), 
                html.Div("Cycle {0}".format(cyc_eeff) if cyc_eeff else "", className="metric-delta"),
                make_sparkline(rp['Energy Efficiency (%)'], "#f59e0b")
            ]), lg=2, md=4, sm=6, className="mb-2"),
            dbc.Col(html.Div(className="metric-card", children=[
                html.Div("Avg Chg Current", className="metric-label"), 
                html.Div("{0:.1f} mA".format(avg_i), className="metric-value"),
                make_sparkline(rp['Current (mA)'], "#8b5cf6")
            ]), lg=2, md=4, sm=6, className="mb-2"),
            dbc.Col(html.Div(className="metric-card", children=[
                html.Div("Capacity Fade Rate", className="metric-label"), 
                html.Div("{0:.4f}".format(fade_rate), className="metric-value"),
                html.Div("% / cycle", className="metric-delta")
            ]), lg=2, md=4, sm=6, className="mb-2"),
        ])

        phases, df_s = [], rp.sort_values('Cycle no').reset_index(drop=True)
        if not df_s.empty:
            cv, cdv = df_s.iloc[0]['Current (mA)'], df_s.iloc[0]['DChg Current (mA)']
            sc, lc  = int(df_s.iloc[0]['Cycle no']), int(df_s.iloc[0]['Cycle no'])
            for i in range(1, len(df_s)):
                v, dv, cyc = df_s.iloc[i]['Current (mA)'], df_s.iloc[i]['DChg Current (mA)'], int(df_s.iloc[i]['Cycle no'])
                if abs(v - cv) <= 1.0 and abs(dv - cdv) <= 1.0:
                    lc = cyc
                else:
                    phases.append({"Phase": "Phase {0}".format(len(phases)+1), "Chg I (mA)": round(cv), "DChg I (mA)": round(cdv), "Start": sc, "End": lc, "Count": lc-sc+1})
                    cv, cdv, sc, lc = v, dv, cyc, cyc
            phases.append({"Phase": "Phase {0}".format(len(phases)+1), "Chg I (mA)": round(cv), "DChg I (mA)": round(cdv), "Start": sc, "End": lc, "Count": lc-sc+1})
        
        phase_table = dag.AgGrid(
            rowData=phases,
            columnDefs=[{"field": c} for c in ["Phase", "Chg I (mA)", "DChg I (mA)", "Start", "End", "Count"]],
            className="ag-theme-alpine-dark",
            style={"height": "300px", "width": "100%"}
        )

        return html.Div([
            html.H3("Cell: {0}".format(p_name) + (" — comparing with {0}".format(s_name) if s_name else "")),
            meta_html,
            metrics,
            html.H4("🎯 Test Protocol Phases", className="mt-4"),
            phase_table
        ]), style_curves, style_interval, style_trends
        
    elif active_tab == "tab-trends":
        if rp.empty: return html.Div("No data in this cycle range.", className="text-warning"), style_curves, style_interval, style_trends
        
        from plotly.subplots import make_subplots
        
        def line_fig(xtitle, ytitle, col_prim, col_sec):
            if rs is None or trends_mode == "Overlay":
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=rp['Cycle no'], y=rp[col_prim], mode='lines+markers', name=p_name, marker=dict(color=C1, size=5), line=dict(color=C1, width=2)))
                if rs is not None:
                    fig.add_trace(go.Scatter(x=rs['Cycle no'], y=rs[col_sec], mode='lines+markers', name=s_name, marker=dict(color=C2, size=5), line=dict(color=C2, width=2)))
                fig.update_layout(**chart_layout(xtitle, ytitle))
                return add_grid(fig)
            else:
                fig = make_subplots(
                    rows=2, cols=2, 
                    shared_xaxes=True, shared_yaxes=True,
                    vertical_spacing=0.1,
                    row_heights=[0.7, 0.3],
                    subplot_titles=("{0}".format(p_name), "{0}".format(s_name), "Delta (Primary - Secondary)")
                )
                
                fig.add_trace(go.Scatter(x=rp['Cycle no'], y=rp[col_prim], mode='lines+markers', name=p_name, marker=dict(color=C1, size=5), line=dict(color=C1, width=2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=rs['Cycle no'], y=rs[col_sec], mode='lines+markers', name=s_name, marker=dict(color=C2, size=5), line=dict(color=C2, width=2)), row=1, col=2)
                
                df_merged = pd.merge(rp[['Cycle no', col_prim]], rs[['Cycle no', col_sec]], on='Cycle no', suffixes=('_p', '_s')).dropna()
                if not df_merged.empty:
                    delta = df_merged[col_prim + '_p'] - df_merged[col_sec + '_s']
                    fig.add_trace(go.Scatter(x=df_merged['Cycle no'], y=delta, mode='lines', name='Delta', line=dict(color="#94a3b8", width=2)), row=2, col=1)
                
                lay = chart_layout(xtitle, ytitle)
                lay.update(height=450, margin=dict(t=50, b=40, l=40, r=40))
                fig.update_layout(**lay)
                for annotation in fig['layout']['annotations']:
                    annotation['font'] = dict(size=12, color='#CBD5E1')
                add_grid(fig)
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', row=1, col=2)
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', row=1, col=2)
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', row=2, col=1)
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', row=2, col=1)
                return fig

        col_w = 12 if trends_mode == "Side-by-Side" and rs is not None else 6
        return html.Div([
            dbc.Row([
                dbc.Col([html.H5("🔋 Discharge Capacity"), dcc.Graph(figure=line_fig("Cycle", "DChg Capacity (Ah)", "DChg capacity (Ah)", "DChg capacity (Ah)"))], width=col_w),
                dbc.Col([html.H5("⚡ Coulombic Efficiency"), dcc.Graph(figure=line_fig("Cycle", "Efficiency (%)", "Coulombic Efficiency (%)", "Coulombic Efficiency (%)"))], width=col_w)
            ]),
            dbc.Row([
                dbc.Col([html.H5("🌡 Energy Efficiency"), dcc.Graph(figure=line_fig("Cycle", "Efficiency (%)", "Energy Efficiency (%)", "Energy Efficiency (%)"))], width=col_w),
                dbc.Col([html.H5("📈 Charge Capacity"), dcc.Graph(figure=line_fig("Cycle", "Chg Capacity (Ah)", "Chg Capacity (Ah)", "Chg Capacity (Ah)"))], width=col_w)
            ])
        ]), style_curves, style_interval, style_trends
        
    elif active_tab == "tab-curves":
        dp, ds = get_dfs()
        sel_cycles = curves_selected_cycles if curves_selected_cycles else []

        fig_vc = go.Figure()
        for tr in build_vc_traces(dp, sel_cycles, "turbo"):
            fig_vc.add_trace(tr)
        if ds is not None:
            sec_cycles = [c for c in sel_cycles if c in ds['Cycle'].unique()]
            for tr in build_vc_traces(ds, sec_cycles, "sunset", " [{0}]".format(s_name)):
                fig_vc.add_trace(tr)

        fig_vc.update_layout(height=520, title="{0} — Selected Cycles".format(p_name), **chart_layout("Capacity (mAh)", "Voltage (V)"))
        fig_vc.update_layout(legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02))
        if len(sel_cycles) > 20: fig_vc.update_layout(showlegend=False)
        add_grid(fig_vc)
        
        return html.Div([
            html.H4("🌈 Voltage vs Capacity — Colored by Cycle"),
            dcc.Graph(figure=fig_vc)
        ]), style_curves, style_interval, style_trends
        
    elif active_tab == "tab-intervals":
        dp, ds = get_dfs()
        cycles_list = sorted([c for c in dp['Cycle'].unique() if c != 0])
        
        s5 = int5 if int5 is not None else True
        s10 = int10 if int10 is not None else True
        s25 = int25 if int25 is not None else True
        
        # When Dash initializes, these inputs might be dicts or strings. We check boolean.
        if isinstance(int5, list): s5 = bool(int5)
        if isinstance(int10, list): s10 = bool(int10)
        if isinstance(int25, list): s25 = bool(int25)

        fig_iv = go.Figure()
        if s5:
            for tr in build_vc_traces(dp, [c for i, c in enumerate(cycles_list) if i % 5 == 0], "Blues"):
                tr.name += " [÷5]"; fig_iv.add_trace(tr)
        if s10:
            for tr in build_vc_traces(dp, [c for i, c in enumerate(cycles_list) if i % 10 == 0], "YlOrRd"):
                tr.name += " [÷10]"; fig_iv.add_trace(tr)
        if s25:
            for tr in build_vc_traces(dp, [c for i, c in enumerate(cycles_list) if i % 25 == 0], "Greens"):
                tr.name += " [÷25]"; fig_iv.add_trace(tr)

        fig_iv.update_layout(height=560, title="{0} — Multi-Interval Overlay".format(p_name), **chart_layout("Capacity (mAh)", "Voltage (V)"))
        add_grid(fig_iv)

        return html.Div([
            html.H4("🎯 Interval Groups — Every 5th / 10th / 25th Simultaneously"),
            dcc.Graph(figure=fig_iv)
        ]), style_curves, style_interval, style_trends
        
    elif active_tab == "tab-full":
        dp, ds = get_dfs()
        cycles_list = sorted([c for c in dp['Cycle'].unique() if c != 0])
        fig_full = go.Figure()
        for tr in build_vc_traces(dp, cycles_list, "turbo", single_color=C1):
            fig_full.add_trace(tr)
        if ds is not None:
            sec_cycles = sorted([x for x in ds['Cycle'].unique() if x != 0])
            for tr in build_vc_traces(ds, sec_cycles, "sunset", " [{0}]".format(s_name), single_color=C2):
                fig_full.add_trace(tr)
        fig_full.update_layout(height=850, title=dict(text="Cell: {0}".format(p_name), font=dict(size=24)), **chart_layout("Capacity (mAh)", "Voltage (V)"))
        fig_full.update_layout(legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02))
        add_grid(fig_full)
        return html.Div([html.H4("🖥️ Full Screen Graph"), dcc.Graph(figure=fig_full)]), style_curves, style_interval, style_trends
        
    elif active_tab == "tab-raw":
        def make_grid(df):
            return dag.AgGrid(
                rowData=df.to_dict("records"),
                columnDefs=[{"field": c} for c in df.columns],
                className="ag-theme-alpine-dark",
                style={"height": "600px", "width": "100%"},
                defaultColDef={"sortable": True, "filter": True, "resizable": True}
            )
        
        pdf_controls = html.Div([
            dbc.Button("📄 Generate PDF Report", id="btn-generate-pdf", color="success", className="mb-2"),
            dcc.Loading(html.Div(id="pdf-status-msg", className="text-info mt-2"))
        ], className="mb-3")
        
        tabs_raw = [
            dbc.Tab(make_grid(rp), label=" 📋 {0}".format(p_name)),
        ]
        if rs is not None:
            tabs_raw.append(dbc.Tab(make_grid(rs), label=" 📋 {0}".format(s_name)))
            
        return html.Div([
            pdf_controls,
            html.H4("📄 Raw Report Data"),
            dbc.Tabs(tabs_raw)
        ]), style_curves, style_interval, style_trends

@app.callback(
    Output("pdf-status-msg", "children"),
    Input("btn-generate-pdf", "n_clicks"),
    State("store-reports", "data"),
    State("primary-select", "value"),
    State("folder-input", "value"),
    prevent_initial_call=True
)
def generate_pdf(n_clicks, store_data, p_name, folder_path):
    if not n_clicks or not store_data or not p_name or not folder_path:
        return ""
        
    try:
        from pdf_generator import generate_pdf
        import datetime
        
        p_name = p_name.strip()
        df_prim, _, _ = load_and_analyze(os.path.join(folder_path, "{0}.ndax".format(p_name)))
        
        start_date = df_prim['Timestamp'].min().strftime("%B %d, %Y") if df_prim is not None and 'Timestamp' in df_prim else "Unknown"
        rp = pd.DataFrame(store_data["primary"])
        
        clean_s = rp[rp['Chg Capacity (Ah)'] > 0.0001]
        def get_max_cyc(col):
            s = clean_s[col].dropna()
            return s.max() if not s.empty else 0.0
            
        first_dcap = rp.iloc[0]['DChg capacity (Ah)'] if not rp.empty else 0
        last_dcap = rp.iloc[-1]['DChg capacity (Ah)'] if not rp.empty else 0
        fade_rate = (first_dcap - last_dcap) / len(rp) * 100 if not rp.empty else 0

        meta_data = {
            "Cell Name": p_name,
            "Test Start Date": start_date,
            "Cycles in Range": "{0}".format(len(rp)),
            "Peak Discharge Cap.": "{0:.4f} Ah".format(get_max_cyc('DChg capacity (Ah)')),
            "Max Coulombic Eff.": "{0:.2f} %".format(get_max_cyc('Coulombic Efficiency (%)')),
            "Max Energy Eff.": "{0:.2f} %".format(get_max_cyc('Energy Efficiency (%)')),
            "Avg Chg Current": "{0:.1f} mA".format(rp['Current (mA)'].mean()),
            "Capacity Fade Rate": "{0:.4f} %/cycle".format(fade_rate),
        }
        
        phases, df_s = [], rp.sort_values('Cycle no').reset_index(drop=True)
        if not df_s.empty:
            cv, cdv = df_s.iloc[0]['Current (mA)'], df_s.iloc[0]['DChg Current (mA)']
            sc, lc  = int(df_s.iloc[0]['Cycle no']), int(df_s.iloc[0]['Cycle no'])
            for i in range(1, len(df_s)):
                v, dv, cyc = df_s.iloc[i]['Current (mA)'], df_s.iloc[i]['DChg Current (mA)'], int(df_s.iloc[i]['Cycle no'])
                if abs(v - cv) <= 1.0 and abs(dv - cdv) <= 1.0:
                    lc = cyc
                else:
                    phases.append({"Phase": "Phase {0}".format(len(phases)+1), "Chg I (mA)": round(cv), "DChg I (mA)": round(cdv), "Start": sc, "End": lc, "Count": lc-sc+1})
                    cv, cdv, sc, lc = v, dv, cyc, cyc
            phases.append({"Phase": "Phase {0}".format(len(phases)+1), "Chg I (mA)": round(cv), "DChg I (mA)": round(cdv), "Start": sc, "End": lc, "Count": lc-sc+1})
        phases_df = pd.DataFrame(phases)

        fig1 = go.Figure(go.Scatter(x=rp['Cycle no'], y=rp['DChg capacity (Ah)'], mode='lines+markers', marker=dict(color=C1, size=5), line=dict(color=C1, width=2)))
        fig1.update_layout(title="Discharge Capacity (Ah)", height=400, plot_bgcolor='white', paper_bgcolor='white', font=dict(color='black'))
        fig2 = go.Figure(go.Scatter(x=rp['Cycle no'], y=rp['Coulombic Efficiency (%)'], mode='lines+markers', marker=dict(color=C1, size=5), line=dict(color=C1, width=2)))
        fig2.update_layout(title="Coulombic Efficiency (%)", height=400, plot_bgcolor='white', paper_bgcolor='white', font=dict(color='black'))

        out_name = "{0}_Report_{1}.pdf".format(p_name, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        generate_pdf(os.path.join(folder_path, out_name), meta_data, phases_df, rp, [fig1, fig2])
        
        return "✅ Successfully saved report to: {0}".format(out_name)
    except Exception as e:
        return html.Div("❌ Error generating PDF: {0}".format(str(e)), className="text-danger")

@app.callback(
    Output("meta-config", "value"),
    Output("meta-notes", "value"),
    Output("meta-save-status", "children"),
    Input("primary-select", "value"),
    State("folder-input", "value")
)
def load_metadata_to_editor(p_name, folder_path):
    if not p_name or not folder_path:
        return "", "", ""
    
    meta_path = os.path.join(folder_path, "cell_metadata.csv")
    if not os.path.exists(meta_path):
        return "", "", ""
        
    try:
        df = pd.read_csv(meta_path)
        row = df[df['Cell Name'].astype(str).str.strip().str.lower() == p_name.lower()]
        if not row.empty:
            cfg = str(row.iloc[0]['Configuration & Changes'])
            nts = str(row.iloc[0]['Experimental Notes / Reason to Stop'])
            return (cfg if cfg.lower() != 'nan' else ""), (nts if nts.lower() != 'nan' else ""), ""
    except:
        pass
    return "", "", ""

@app.callback(
    Output("meta-save-status", "children", allow_duplicate=True),
    Input("btn-save-meta", "n_clicks"),
    State("primary-select", "value"),
    State("folder-input", "value"),
    State("meta-config", "value"),
    State("meta-notes", "value"),
    prevent_initial_call=True
)
def save_metadata(n_clicks, p_name, folder_path, cfg, nts):
    if not n_clicks or not p_name or not folder_path:
        return ""
        
    meta_path = os.path.join(folder_path, "cell_metadata.csv")
    
    try:
        if os.path.exists(meta_path):
            df = pd.read_csv(meta_path)
        else:
            df = pd.DataFrame(columns=['Cell Name', 'Configuration & Changes', 'Experimental Notes / Reason to Stop'])
            
        mask = df['Cell Name'].astype(str).str.strip().str.lower() == p_name.lower()
        if any(mask):
            df.loc[mask, 'Configuration & Changes'] = cfg
            df.loc[mask, 'Experimental Notes / Reason to Stop'] = nts
        else:
            new_row = pd.DataFrame([{
                'Cell Name': p_name,
                'Configuration & Changes': cfg,
                'Experimental Notes / Reason to Stop': nts
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            
        df.to_csv(meta_path, index=False)
        return html.Span("✅ Saved!", className="text-success")
    except Exception as e:
        return html.Span("❌ Error: {0}".format(str(e)), className="text-danger")




@app.callback(
    Output("curves-cycle-select", "options"),
    Output("curves-cycle-select", "value"),
    Input("store-reports", "data"),
    Input("cycle-start", "value"),
    Input("cycle-end", "value"),
    Input("btn-select-outliers", "n_clicks"),
    prevent_initial_call=True
)
def update_curves_selector(store_data, c_start, c_end, n_clicks):
    if not store_data or "primary" not in store_data:
        return [], []
    
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ""
    
    rp_all = pd.DataFrame(store_data["primary"])
    if c_start is None or c_end is None:
        c_start, c_end = rp_all['Cycle no'].min(), rp_all['Cycle no'].max()
    c_min, c_max = min(c_start, c_end), max(c_start, c_end)
    rp = rp_all[(rp_all['Cycle no'] >= c_min) & (rp_all['Cycle no'] <= c_max)]
    
    if rp.empty:
        return [], []
        
    cycles_list = sorted([int(c) for c in rp['Cycle no'].tolist() if c > 0])
    if not cycles_list:
        return [], []
        
    options = [{"label": "Cycle {0}".format(c), "value": c} for c in cycles_list]
    
    if trigger == "btn-select-outliers":
        mean_ce = rp['Coulombic Efficiency (%)'].mean()
        std_ce = rp['Coulombic Efficiency (%)'].std()
        outliers = rp[abs(rp['Coulombic Efficiency (%)'] - mean_ce) > 2 * std_ce]['Cycle no'].tolist()
        return options, sorted([int(x) for x in outliers])
        
    # Smart Defaults: First, Last, Peak Capacity, Worst Efficiency
    first_cyc = cycles_list[0]
    last_cyc = cycles_list[-1]
    
    clean_dcap = rp[rp['DChg capacity (Ah)'] > 0.0001]
    peak_cyc = int(clean_dcap.loc[clean_dcap['DChg capacity (Ah)'].idxmax()]['Cycle no']) if not clean_dcap.empty else first_cyc
    
    clean_ce = rp[rp['Coulombic Efficiency (%)'] > 0]
    worst_cyc = int(clean_ce.loc[clean_ce['Coulombic Efficiency (%)'].idxmin()]['Cycle no']) if not clean_ce.empty else first_cyc
    
    smart_defaults = list(set([first_cyc, last_cyc, peak_cyc, worst_cyc]))
    return options, sorted(smart_defaults)

if __name__ == "__main__":
    app.run(debug=True)
