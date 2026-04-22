import streamlit as st
import pandas as pd
import NewareNDA
import os
import glob
import re
import time
import plotly.graph_objects as go
import plotly.express as px
import json

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ZnBr Battery Analysis",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── PREMIUM CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080f1e 0%, #0f1f3d 100%);
    border-right: 1px solid rgba(59,130,246,0.15);
}
[data-testid="stSidebar"] * { color: #CBD5E1; }

/* Hero banner */
.hero {
    background: linear-gradient(135deg, #0a1628 0%, #12294d 60%, #0a1628 100%);
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 16px;
    padding: 20px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 18px;
}
.hero-title { font-size: 1.55rem; font-weight: 800; color: #F1F5F9; letter-spacing: -0.03em; }
.hero-sub   { font-size: 0.82rem; color: #64748B; margin-top: 3px; }

/* Metrics */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(15,31,61,0.95), rgba(8,15,30,0.95));
    padding: 16px 20px;
    border-radius: 14px;
    border: 1px solid rgba(59,130,246,0.18);
    box-shadow: 0 4px 20px rgba(0,0,0,0.35);
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important; font-weight: 600 !important;
    color: #475569 !important; text-transform: uppercase; letter-spacing: 0.08em;
}
[data-testid="stMetricValue"] {
    font-size: 1.55rem !important; font-weight: 700 !important; color: #E2E8F0 !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.1rem !important;
}

/* Section labels in sidebar */
.sid-head {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #3B82F6;
    padding: 14px 0 6px 2px;
}

/* Divider */
.my-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 8px 0 12px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def natural_sort_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

def file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)

def chart_layout(xtitle, ytitle):
    return dict(
        xaxis_title=xtitle, yaxis_title=ytitle,
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=20),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Inter, sans-serif", size=12),
    )

def add_grid(fig):
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)')
    return fig

# ─── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_and_analyze(file_path):
    try:
        df = NewareNDA.read(file_path)
        report_data = []
        cycles = sorted(df['Cycle'].unique())
        if 0 in cycles: cycles.remove(0)

        for cycle in cycles:
            cyc_df = df[df['Cycle'] == cycle]
            if cyc_df.empty: continue
            chg_df  = cyc_df[cyc_df['Status'] == 'CC_Chg']
            dchg_df = cyc_df[cyc_df['Status'].isin(['CC_DChg', 'CCCV_DChg'])]

            time_hrs = 0
            if not chg_df.empty:
                time_hrs = (chg_df['Timestamp'].iloc[-1] - chg_df['Timestamp'].iloc[0]).total_seconds() / 3600

            chg_cap   = chg_df['Charge_Capacity(mAh)'].max()  / 1000 if not chg_df.empty  else 0
            dchg_cap  = dchg_df['Discharge_Capacity(mAh)'].max() / 1000 if not dchg_df.empty else 0
            c_eff     = (dchg_cap / chg_cap * 100) if chg_cap > 0 else 0
            if c_eff > 150 or c_eff < 0: c_eff = None
            chg_eng   = chg_df['Charge_Energy(mWh)'].max()    / 1000 if not chg_df.empty  else 0
            dchg_eng  = dchg_df['Discharge_Energy(mWh)'].max() / 1000 if not dchg_df.empty else 0
            eng_eff   = (dchg_eng / chg_eng * 100) if chg_eng > 0 else 0
            if eng_eff > 150 or eng_eff < 0: eng_eff = None
            avg_i     = chg_df['Current(mA)'].mean()      if not chg_df.empty  else 0
            avg_di    = dchg_df['Current(mA)'].mean()     if not dchg_df.empty else 0
            v_end_chg   = chg_df['Voltage'].iloc[-1]  if not chg_df.empty  else 0
            v_st_dchg   = dchg_df['Voltage'].iloc[0]  if not dchg_df.empty else 0

            def get_ocv(step_df, cyc_num):
                if step_df.empty: return None
                li = step_df['Step_Index'].iloc[-1]
                fr = df[(df['Cycle'] == cyc_num) & (df['Status'] == 'Rest') & (df['Step_Index'] > li)]
                if not fr.empty:
                    return fr[fr['Step_Index'] == fr['Step_Index'].min()]['Voltage'].iloc[-1]
                nr = df[(df['Cycle'] == cyc_num + 1) & (df['Status'] == 'Rest')]
                if not nr.empty:
                    return nr[nr['Step_Index'] == nr['Step_Index'].min()]['Voltage'].iloc[-1]
                return None

            ocv_c = get_ocv(chg_df,  cycle)
            ocv_d = get_ocv(dchg_df, cycle)

            report_data.append({
                'Cycle no': int(cycle),
                'Time (hrs)': round(time_hrs, 4),
                'Current (mA)': round(avg_i, 1),
                'DChg Current (mA)': round(abs(avg_di), 1),
                'Chg Capacity (Ah)': round(chg_cap, 4),
                'DChg capacity (Ah)': round(dchg_cap, 4),
                'Coulombic Efficiency (%)': round(c_eff, 4) if c_eff is not None else None,
                'Chg. Energy (Wh)': round(chg_eng, 4),
                'DChg. Energy (Wh)': round(dchg_eng, 4),
                'Energy Efficiency (%)': round(eng_eff, 4) if eng_eff is not None else None,
                'Voltage End of Chg': round(v_end_chg, 4),
                'Voltage Start of Dchg': round(v_st_dchg, 4),
                'OCV after Chg':  round(ocv_c, 4) if ocv_c  else None,
                'OCV after DChg': round(ocv_d, 4) if ocv_d else None,
            })
        return df, pd.DataFrame(report_data)
    except Exception as e:
        st.error(f"❌ Error loading {os.path.basename(file_path)}: {e}")
        return None, None

# ─── VOLTAGE vs CAPACITY TRACES ──────────────────────────────────────────────
def build_vc_traces(df_raw, cycle_list, colorscale, label_suffix="", single_color=None):
    """Return Plotly traces for a list of cycles with a color per cycle."""
    n = len(cycle_list)
    if single_color:
        colors = [single_color] * n
    else:
        colors = px.colors.sample_colorscale(colorscale, [i / max(n - 1, 1) for i in range(n)])
    traces = []
    for idx, cyc in enumerate(cycle_list):
        cyc_df = df_raw[df_raw['Cycle'] == cyc]
        chg  = cyc_df[cyc_df['Status'] == 'CC_Chg']
        dchg = cyc_df[cyc_df['Status'].isin(['CC_DChg', 'CCCV_DChg'])]
        col  = colors[idx]
        name = f"Cyc {cyc}{label_suffix}"
        
        is_first = (idx == 0)
        leg_group = f"All{label_suffix}" if single_color else f"g{cyc}{label_suffix}"
        show_leg = is_first if single_color else True

        if not chg.empty:
            traces.append(go.Scatter(
                x=chg['Charge_Capacity(mAh)'], y=chg['Voltage'],
                mode='lines', line=dict(color=col, width=1.5),
                name=f"All Cycles{label_suffix}" if (single_color and is_first) else name + " ↑", 
                legendgroup=leg_group, showlegend=show_leg,
                hovertemplate=name + " ↑<br>Cap: %{x:.2f}<br>V: %{y:.3f}<extra></extra>"
            ))
        if not dchg.empty:
            traces.append(go.Scatter(
                x=dchg['Discharge_Capacity(mAh)'], y=dchg['Voltage'],
                mode='lines', line=dict(color=col, width=1.5, dash='dot'),
                name=name + " ↓", legendgroup=leg_group, showlegend=False,
                hovertemplate=name + " ↓<br>Cap: %{x:.2f}<br>V: %{y:.3f}<extra></extra>"
            ))
    return traces

# ─── CONFIGURATION MANAGER ───────────────────────────────────────────────────
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f).get("folder_path", "")
        except:
            pass
    return ""

def save_config(path):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"folder_path": path}, f)

# ─── HERO HEADER ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <span style="font-size:2.6rem;line-height:1;">🔋</span>
  <div>
    <div class="hero-title">ZnBr Battery Analysis Dashboard</div>
    <div class="hero-sub">Zinc-Bromine Cell Telemetry · Professional Reporting Suite</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:8px 0 18px;'>
      <div style='font-size:1.8rem;'>⚡</div>
      <div style='font-weight:800;font-size:0.95rem;color:#93C5FD;'>Cell Manager</div>
      <div style='font-size:0.72rem;color:#475569;margin-top:2px;'>ZnBr Analysis Suite</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Folder Selection ──
    st.markdown('<div class="sid-head">📂 Data Source</div>', unsafe_allow_html=True)
    saved_path = load_config()
    
    fc1, fc2 = st.columns([3, 1])
    with fc1:
        folder_path = st.text_input("NDAX Folder Path", value=saved_path, placeholder="C:\\path\\to\\ndax", label_visibility="collapsed")
    with fc2:
        if st.button("Browse"):
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.attributes('-topmost', True)
            root.withdraw()
            selected = filedialog.askdirectory(master=root, initialdir=saved_path if os.path.exists(saved_path) else None)
            root.destroy()
            if selected:
                save_config(selected)
                st.rerun()
    
    if folder_path != saved_path and folder_path:
        save_config(folder_path)
        st.rerun()
        
    if not folder_path or not os.path.exists(folder_path):
        st.warning("Please enter a valid folder path above.")
        st.stop()

    # ── Discover Files ──
    all_files = sorted(glob.glob(os.path.join(folder_path, "*.ndax")), key=natural_sort_key)
    all_names = [os.path.basename(os.path.splitext(f)[0]) for f in all_files]
    
    if not all_files:
        st.warning(f"No .ndax files found in {folder_path}")
        st.stop()

    st.markdown('<hr class="my-divider">', unsafe_allow_html=True)

    # ── Primary cell ──
    st.markdown('<div class="sid-head">🗂 Primary Cell</div>', unsafe_allow_html=True)
    search = st.text_input("Search", placeholder="Type S-20…", label_visibility="collapsed")
    filtered = [n for n in all_names if search.lower() in n.lower()] if search else all_names
    if not filtered:
        st.warning("No match found."); st.stop()

    primary_name = st.selectbox("Cell", filtered, label_visibility="collapsed")
    primary_file = os.path.join(folder_path, primary_name + ".ndax")
    sz = file_size_mb(primary_file)
    st.caption(f"📦 {sz:.1f} MB {'— large file, please wait' if sz > 10 else ''}")

    st.markdown('<hr class="my-divider">', unsafe_allow_html=True)

    # ── Comparison cell ──
    st.markdown('<div class="sid-head">⚖ Compare Cell (Optional)</div>', unsafe_allow_html=True)
    sec_opts = ["— None —"] + [n for n in all_names if n != primary_name]
    secondary_name = st.selectbox("Compare", sec_opts, label_visibility="collapsed")
    secondary_file = os.path.join(folder_path, secondary_name + ".ndax") if secondary_name != "— None —" else None
    if secondary_file:
        st.caption(f"📦 {file_size_mb(secondary_file):.1f} MB")

    st.markdown('<hr class="my-divider">', unsafe_allow_html=True)
    st.markdown('<div class="sid-head">🔍 Cycle Range</div>', unsafe_allow_html=True)
    range_placeholder = st.empty()   # filled after data loads

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

C1, C2 = "#3B82F6", "#F97316"   # primary blue / comparison orange

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

# ═══ TAB 3 — CYCLE CURVES (Option A: pick ONE step) ═════════════════════════
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
    for tr in build_vc_traces(dp, sel_cycles, "turbo", single_color="#3B82F6" if step_opt == "All" else None):
        fig_vc.add_trace(tr)
    if ds is not None:
        sec_cycles = [c for c in sorted([x for x in ds['Cycle'].unique() if x != 0]) if cycles_list.index(c) % step == 0
                      if c in cycles_list]
        for tr in build_vc_traces(ds, sec_cycles, "sunset", f" [{secondary_name}]", single_color="#F97316" if step_opt == "All" else None):
            fig_vc.add_trace(tr)

    fig_vc.update_layout(**chart_layout("Capacity (mAh)", "Voltage (V)"),
                         height=520, title=f"{primary_name} — Every {step} Cycle(s)")
    fig_vc.update_layout(legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02))
    if step_opt != "All" and len(sel_cycles) > 20:
        fig_vc.update_layout(showlegend=False)
        
    add_grid(fig_vc)
    st.plotly_chart(fig_vc, width='stretch')

# ═══ TAB 4 — INTERVAL GROUPS (Option B: 5 + 10 + 25 simultaneously) ════════
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
    for tr in build_vc_traces(dp, cycles_list, "turbo", single_color="#3B82F6"):
        fig_full.add_trace(tr)
    if ds is not None:
        sec_cycles = sorted([x for x in ds['Cycle'].unique() if x != 0])
        for tr in build_vc_traces(ds, sec_cycles, "sunset", f" [{secondary_name}]", single_color="#F97316"):
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
