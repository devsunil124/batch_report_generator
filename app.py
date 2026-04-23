import streamlit as st
import pandas as pd
import os
import time
import plotly.graph_objects as go
from data_loader import load_and_analyze, build_vc_traces
from config_manager import load_config
from chart_helpers import chart_layout, add_grid, C1, C2
from ui_components import render_premium_css, render_hero, render_sidebar

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ZnBr Battery Analysis",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── UI COMPONENTS ───────────────────────────────────────────────────────────
render_premium_css()
render_hero()

# ─── SIDEBAR & CONFIG ────────────────────────────────────────────────────────
saved_path = load_config()
folder_path, primary_name, primary_file, secondary_name, secondary_file, range_placeholder = render_sidebar(saved_path)

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
prog = st.progress(0, text=f"⏳ Loading {primary_name}…")
df_prim, report_prim = load_and_analyze(primary_file)
prog.progress(55, text=f"Loaded {primary_name}. Analyzing…")

df_sec, report_sec = None, None
if secondary_file:
    df_sec, report_sec = load_and_analyze(secondary_file)
prog.progress(100, text="✅ Ready!")
time.sleep(0.35); prog.empty()

if report_prim is None or report_prim.empty:
    st.error("Could not load the selected file. Check the file format.")
    st.stop()

# ─── CYCLE RANGE (sidebar, filled after load) ─────────────────────────────────
min_c = int(report_prim['Cycle no'].min())
max_c = int(report_prim['Cycle no'].max())
if report_sec is not None:
    min_c = min(min_c, int(report_sec['Cycle no'].min()))
    max_c = max(max_c, int(report_sec['Cycle no'].max()))

with range_placeholder.container():
    if min_c == max_c:
        st.caption(f"Single cycle: {min_c}")
        cycle_range = (min_c, max_c)
    else:
        rc1, rc2 = st.columns(2)
        c_start = rc1.number_input("Start", min_value=min_c, max_value=max_c, value=min_c, step=1)
        c_end   = rc2.number_input("End",   min_value=min_c, max_value=max_c, value=max_c, step=1)
        cycle_range = (min(c_start, c_end), max(c_start, c_end))

# ─── APPLY RANGE FILTER ──────────────────────────────────────────────────────
rp = report_prim[(report_prim['Cycle no'] >= cycle_range[0]) & (report_prim['Cycle no'] <= cycle_range[1])].copy()
dp = df_prim[(df_prim['Cycle'] >= cycle_range[0]) & (df_prim['Cycle'] <= cycle_range[1])].copy()

rs, ds = None, None
if report_sec is not None:
    rs = report_sec[(report_sec['Cycle no'] >= cycle_range[0]) & (report_sec['Cycle no'] <= cycle_range[1])].copy()
    ds = df_sec[(df_sec['Cycle'] >= cycle_range[0]) & (df_sec['Cycle'] <= cycle_range[1])].copy()

cycles_list = sorted([c for c in dp['Cycle'].unique() if c != 0])

# ─── TABS ────────────────────────────────────────────────────────────────────
t_sum, t_trends, t_curves, t_interval, t_full, t_raw = st.tabs([
    "📊  Summary",
    "📈  Trends",
    "🌈  Cycle Curves",
    "🎯  Interval Groups",
    "🖥️  Full Screen Graph",
    "📄  Raw Data",
])

# ═══ TAB 1 — SUMMARY ═══════════════════════════════════════════════════════
with t_sum:
    comp_label = f"  —  comparing with **{secondary_name}**" if secondary_file else ""
    st.markdown(f"### Cell: `{primary_name}`{comp_label}")

    try:
        start_date = df_prim['Timestamp'].min().strftime("%B %d, %Y")
    except:
        start_date = "Unknown"

    meta_html = ""
    meta_path = os.path.join(folder_path, "cell_metadata.csv") if 'folder_path' in locals() and folder_path else "cell_metadata.csv"
    if os.path.exists(meta_path):
        try:
            meta_df = pd.read_csv(meta_path)
            meta_row = meta_df[meta_df['Cell Name'].astype(str).str.strip().str.lower() == primary_name.lower()]
            if not meta_row.empty:
                cfg = str(meta_row.iloc[0]['Configuration & Changes']).strip()
                nts = str(meta_row.iloc[0]['Experimental Notes / Reason to Stop']).strip()
                if cfg.lower() == 'nan': cfg = "No configuration data"
                if nts.lower() == 'nan': nts = "No notes provided"
                meta_html = f'''
                <div style="background-color:rgba(59,130,246,0.08); border-left:4px solid #3B82F6; padding:12px 16px; border-radius:4px; margin-bottom:20px;">
                    <div style="font-size:0.95em; margin-bottom:6px;"><span style="color:#93C5FD;">📅 Started Cycling:</span> <span style="color:#F1F5F9; font-weight:600;">{start_date}</span></div>
                    <div style="font-size:0.9em; margin-bottom:4px;"><span style="color:#94A3B8;">⚙️ Configuration:</span> <span style="color:#E2E8F0;">{cfg}</span></div>
                    <div style="font-size:0.9em;"><span style="color:#94A3B8;">📝 Notes / Status:</span> <span style="color:#E2E8F0;">{nts}</span></div>
                </div>
                '''
        except Exception as e:
            pass

    if not meta_html:
        meta_html = f'''
        <div style="background-color:rgba(59,130,246,0.08); border-left:4px solid #3B82F6; padding:10px 16px; border-radius:4px; margin-bottom:20px;">
            <div style="font-size:0.95em;"><span style="color:#93C5FD;">📅 Started Cycling:</span> <span style="color:#F1F5F9; font-weight:600;">{start_date}</span></div>
        </div>
        '''
    
    st.markdown(meta_html, unsafe_allow_html=True)

    if rp.empty:
        st.warning("No data in this cycle range.")
    else:
        def get_max_and_cyc(col):
            # Only consider cycles where charge capacity is significant (> 0.0001 Ah) to avoid noise in highlights
            clean_s = rp[rp['Chg Capacity (Ah)'] > 0.0001][col].dropna()
            if clean_s.empty: return 0.0, None
            idx = clean_s.idxmax()
            return clean_s[idx], int(rp.loc[idx, 'Cycle no'])

        max_dcap, cyc_dcap = get_max_and_cyc('DChg capacity (Ah)')
        max_ceff, cyc_ceff = get_max_and_cyc('Coulombic Efficiency (%)')
        max_eeff, cyc_eeff = get_max_and_cyc('Energy Efficiency (%)')

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Cycles in Range", f"{len(rp)}")
        m2.metric("Peak Discharge Cap.", f"{max_dcap:.4f} Ah", f"Cycle {cyc_dcap}" if cyc_dcap else None, delta_color="off")
        m3.metric("Max Coulombic Eff.", f"{max_ceff:.2f}%", f"Cycle {cyc_ceff}" if cyc_ceff else None, delta_color="off")
        m4.metric("Max Energy Eff.", f"{max_eeff:.2f}%", f"Cycle {cyc_eeff}" if cyc_eeff else None, delta_color="off")
        m5.metric("Avg Chg Current", f"{rp['Current (mA)'].mean():.1f} mA")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🎯 Test Protocol Phases")
        phases, df_s = [], rp.sort_values('Cycle no').reset_index(drop=True)
        cv, cdv = df_s.iloc[0]['Current (mA)'], df_s.iloc[0]['DChg Current (mA)']
        sc, lc  = int(df_s.iloc[0]['Cycle no']), int(df_s.iloc[0]['Cycle no'])
        for i in range(1, len(df_s)):
            v, dv, cyc = df_s.iloc[i]['Current (mA)'], df_s.iloc[i]['DChg Current (mA)'], int(df_s.iloc[i]['Cycle no'])
            if abs(v - cv) <= 1.0 and abs(dv - cdv) <= 1.0:
                lc = cyc
            else:
                phases.append({"Phase": f"Phase {len(phases)+1}", "Chg I (mA)": round(cv), "DChg I (mA)": round(cdv), "Start": sc, "End": lc, "Count": lc-sc+1})
                cv, cdv, sc, lc = v, dv, cyc, cyc
        phases.append({"Phase": f"Phase {len(phases)+1}", "Chg I (mA)": round(cv), "DChg I (mA)": round(cdv), "Start": sc, "End": lc, "Count": lc-sc+1})
        st.dataframe(pd.DataFrame(phases), width='stretch', hide_index=True)

# ═══ TAB 2 — TRENDS ════════════════════════════════════════════════════════
with t_trends:
    if rp.empty:
        st.warning("No data in this cycle range.")
    else:
        def line_fig(xtitle, ytitle, col_prim, col_sec=None):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=rp['Cycle no'], y=rp[col_prim], mode='lines+markers', name=primary_name,
                                     marker=dict(color=C1, size=5), line=dict(color=C1, width=2)))
            if rs is not None and col_sec:
                fig.add_trace(go.Scatter(x=rs['Cycle no'], y=rs[col_sec], mode='lines+markers', name=secondary_name,
                                         marker=dict(color=C2, size=5), line=dict(color=C2, width=2)))
            fig.update_layout(**chart_layout(xtitle, ytitle))
            return add_grid(fig)

        ca, cb = st.columns(2)
        with ca:
            st.markdown("##### 🔋 Discharge Capacity")
            st.plotly_chart(line_fig("Cycle", "DChg Capacity (Ah)", "DChg capacity (Ah)"), width='stretch')
        with cb:
            st.markdown("##### ⚡ Coulombic Efficiency")
            st.plotly_chart(line_fig("Cycle", "Efficiency (%)", "Coulombic Efficiency (%)", "Coulombic Efficiency (%)"), width='stretch')

        cc, cd = st.columns(2)
        with cc:
            st.markdown("##### 🌡 Energy Efficiency")
            st.plotly_chart(line_fig("Cycle", "Efficiency (%)", "Energy Efficiency (%)", "Energy Efficiency (%)"), width='stretch')
        with cd:
            st.markdown("##### 📈 Charge Capacity")
            st.plotly_chart(line_fig("Cycle", "Chg Capacity (Ah)", "Chg Capacity (Ah)", "Chg Capacity (Ah)"), width='stretch')

# ═══ TAB 3 — CYCLE CURVES ═══════════════════════════════════════════════════
with t_curves:
    st.markdown("#### 🌈 Voltage vs Capacity — Colored by Cycle")
    st.caption("Pick a step interval — each shown cycle gets its own color. Solid = Charge, Dotted = Discharge.")

    ctrl1, ctrl2, _ = st.columns([1.8, 1.2, 2])
    with ctrl1:
        step_opt = st.radio("Show:", ["All", "Every 5th", "Every 10th", "Every 25th", "Custom"],
                            horizontal=True, label_visibility="collapsed")
    with ctrl2:
        custom_n = st.number_input("Custom step", min_value=1, max_value=max(len(cycles_list), 1), value=5, step=1,
                                   disabled=(step_opt != "Custom"))

    step_map = {"All": 1, "Every 5th": 5, "Every 10th": 10, "Every 25th": 25, "Custom": int(custom_n)}
    step = step_map[step_opt]

    sel_cycles = [c for i, c in enumerate(cycles_list) if i % step == 0]
    if not sel_cycles and cycles_list:
        sel_cycles = [cycles_list[-1]]

    fig_vc = go.Figure()
    for tr in build_vc_traces(dp, sel_cycles, "turbo", single_color=C1 if step_opt == "All" else None):
        fig_vc.add_trace(tr)
    if ds is not None:
        sec_cycles = [c for c in sorted([x for x in ds['Cycle'].unique() if x != 0]) if cycles_list.index(c) % step == 0
                      if c in cycles_list]
        for tr in build_vc_traces(ds, sec_cycles, "sunset", f" [{secondary_name}]", single_color=C2 if step_opt == "All" else None):
            fig_vc.add_trace(tr)

    fig_vc.update_layout(**chart_layout("Capacity (mAh)", "Voltage (V)"),
                         height=520, title=f"{primary_name} — Every {step} Cycle(s)")
    fig_vc.update_layout(legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02))
    if step_opt != "All" and len(sel_cycles) > 20:
        fig_vc.update_layout(showlegend=False)
        
    add_grid(fig_vc)
    st.plotly_chart(fig_vc, width='stretch')

# ═══ TAB 4 — INTERVAL GROUPS ═══════════════════════════════════════════════
with t_interval:
    st.markdown("#### 🎯 Interval Groups — Every 5th / 10th / 25th Simultaneously")
    st.caption(
        "Each interval band uses its own **color palette**. "
        "🔵 Blues = Every 5th &nbsp;|&nbsp; 🟠 Warm = Every 10th &nbsp;|&nbsp; 🟢 Greens = Every 25th"
    )

    show5  = st.checkbox("Show every 5th cycle",  value=True)
    show10 = st.checkbox("Show every 10th cycle", value=True)
    show25 = st.checkbox("Show every 25th cycle", value=True)

    fig_iv = go.Figure()
    if show5:
        cycs5 = [c for i, c in enumerate(cycles_list) if i % 5 == 0]
        for tr in build_vc_traces(dp, cycs5, "Blues"):
            tr.name = tr.name + " [÷5]"
            fig_iv.add_trace(tr)
    if show10:
        cycs10 = [c for i, c in enumerate(cycles_list) if i % 10 == 0]
        for tr in build_vc_traces(dp, cycs10, "YlOrRd"):
            tr.name = tr.name + " [÷10]"
            fig_iv.add_trace(tr)
    if show25:
        cycs25 = [c for i, c in enumerate(cycles_list) if i % 25 == 0]
        for tr in build_vc_traces(dp, cycs25, "Greens"):
            tr.name = tr.name + " [÷25]"
            fig_iv.add_trace(tr)

    fig_iv.update_layout(**chart_layout("Capacity (mAh)", "Voltage (V)"),
                         height=560, title=f"{primary_name} — Multi-Interval Overlay")
    add_grid(fig_iv)
    st.plotly_chart(fig_iv, width='stretch')

# ═══ TAB 5 — FULL SCREEN GRAPH ═════════════════════════════════════════════
with t_full:
    st.markdown("#### 🖥️ Full Screen Graph")
    fig_full = go.Figure()
    for tr in build_vc_traces(dp, cycles_list, "turbo", single_color=C1):
        fig_full.add_trace(tr)
    if ds is not None:
        sec_cycles = sorted([x for x in ds['Cycle'].unique() if x != 0])
        for tr in build_vc_traces(ds, sec_cycles, "sunset", f" [{secondary_name}]", single_color=C2):
            fig_full.add_trace(tr)
            
    fig_full.update_layout(**chart_layout("Capacity (mAh)", "Voltage (V)"),
                           height=850, title=dict(text=f"Cell: {primary_name}", font=dict(size=24)))
    fig_full.update_layout(legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02))

    add_grid(fig_full)
    st.plotly_chart(fig_full, width='stretch')

# ═══ TAB 6 — RAW DATA ══════════════════════════════════════════════════════
with t_raw:
    st.markdown("#### 📄 Raw Report Data")
    if secondary_file and rs is not None:
        rt1, rt2 = st.tabs([f"📋 {primary_name}", f"📋 {secondary_name}"])
        with rt1:
            st.dataframe(rp.style.format(precision=4), width='stretch')
            st.download_button("⬇ Download CSV", rp.to_csv(index=False), file_name=f"{primary_name}_report.csv")
        with rt2:
            st.dataframe(rs.style.format(precision=4), width='stretch')
            st.download_button("⬇ Download CSV", rs.to_csv(index=False), file_name=f"{secondary_name}_report.csv")
    else:
        st.dataframe(rp.style.format(precision=4), width='stretch')
        st.download_button("⬇ Download CSV", rp.to_csv(index=False), file_name=f"{primary_name}_report.csv")
