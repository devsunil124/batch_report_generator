import streamlit as st
import pandas as pd
import NewareNDA
import os
import plotly.graph_objects as go
import plotly.express as px

@st.cache_data(show_spinner=False)
def load_and_analyze(file_path):
    """
    Load an NDAX file using NewareNDA and extract step-level metrics into a summary DataFrame.

    Parameters
    ----------
    file_path : str
        The absolute or relative path to the .ndax file.

    Returns
    -------
    df : pandas.DataFrame or None
        The raw dataframe extracted directly from NewareNDA.
    report_df : pandas.DataFrame or None
        A summarized report containing cycle-by-cycle metrics. 
        Returns (None, None) if loading fails.
    """
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

def build_vc_traces(df_raw, cycle_list, colorscale, label_suffix="", single_color=None):
    """
    Return a list of Plotly trace objects (go.Scatter) for a given list of cycles.

    Parameters
    ----------
    df_raw : pandas.DataFrame
        The raw dataframe extracted from the ndax file containing Voltage and Capacity columns.
    cycle_list : list of int
        A list of cycle numbers to plot.
    colorscale : str
        The name of a Plotly express continuous colorscale (e.g., 'turbo', 'sunset').
    label_suffix : str, optional
        A string appended to the trace name in the legend (default is "").
    single_color : str or None, optional
        If provided, all traces will be colored uniformly using this color (default is None).

    Returns
    -------
    list of go.Scatter
        A list of configured Scatter traces for charge and discharge curves.
    """
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
