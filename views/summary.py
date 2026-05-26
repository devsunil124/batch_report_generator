"""Summary view: headline metrics, protocol phases, cell metadata."""
import os
import pandas as pd
from nicegui import ui

from state import state
import theme
import charts


def _meta_for(folder: str, cell_name: str) -> tuple[str, str, str]:
    """Return (started_date, config, notes)."""
    started = "—"
    try:
        if state.df_prim is not None and 'Timestamp' in state.df_prim.columns:
            started = state.df_prim['Timestamp'].min().strftime("%Y-%m-%d")
    except Exception:
        pass

    cfg, nts = "—", "—"
    meta_path = os.path.join(folder, "cell_metadata.csv") if folder else None
    if meta_path and os.path.exists(meta_path):
        try:
            meta = pd.read_csv(meta_path)
            row = meta[meta['Cell Name'].astype(str).str.strip().str.lower() == cell_name.lower()]
            if not row.empty:
                _cfg = str(row.iloc[0].get('Configuration & Changes', '')).strip()
                _nts = str(row.iloc[0].get('Experimental Notes / Reason to Stop', '')).strip()
                if _cfg and _cfg.lower() != 'nan':
                    cfg = _cfg
                if _nts and _nts.lower() != 'nan':
                    nts = _nts
        except Exception:
            pass
    return started, cfg, nts


def _peak(rp, col: str):
    """(value, cycle_no) for the row of max `col` filtered by Chg Capacity > 0.0001."""
    clean = rp[rp['Chg Capacity (Ah)'] > 0.0001][col].dropna()
    if clean.empty:
        return None, None
    idx = clean.idxmax()
    return float(clean[idx]), int(rp.loc[idx, 'Cycle no'])


def render() -> None:
    if not state.ready():
        ui.html('<div class="term-empty">// SELECT A CELL FROM THE LEFT RAIL TO BEGIN //</div>')
        return

    rp = state.rp
    if rp is None or rp.empty:
        ui.html('<div class="term-empty">// NO DATA IN SELECTED CYCLE RANGE //</div>')
        return

    started, cfg, nts = _meta_for(state.folder_path, state.primary_name)
    max_dcap, cyc_dcap = _peak(rp, 'DChg capacity (Ah)')
    max_ceff, cyc_ceff = _peak(rp, 'Coulombic Efficiency (%)')
    max_eeff, cyc_eeff = _peak(rp, 'Energy Efficiency (%)')
    avg_i = float(rp['Current (mA)'].mean()) if 'Current (mA)' in rp else 0.0
    n_cyc = len(rp)

    # ── Cell identity strip ──────────────────────────────────────────────────
    with ui.element('div').classes('term-panel').style('margin: 14px;'):
        with ui.element('div').classes('term-panel-header'):
            ui.html(
                f'<span>CELL/{state.primary_name}</span>'
                f'<span class="meta">STARTED {started} '
                + (f'· COMPARE {state.secondary_name}' if state.secondary_name else '')
                + '</span>'
            )
        with ui.element('div').classes('term-panel-body'):
            theme.kv([
                ("Configuration", cfg),
                ("Notes / Status", nts),
                ("Cycle Range",  f"{state.cycle_start} → {state.cycle_end}   ({n_cyc} cycles in view)"),
            ])

    # ── Metric strip ─────────────────────────────────────────────────────────
    with ui.element('div').classes('term-panel').style('margin: 0 14px 14px 14px;'):
        with ui.element('div').classes('term-panel-header'):
            ui.html('<span>HEADLINE METRICS</span><span class="meta">RANGE FILTERED</span>')
        with ui.element('div').style(
            'display:grid; grid-template-columns: repeat(5, 1fr); gap: 1px; '
            'background: #1a1a1a; border-top: 1px solid #1a1a1a;'
        ):
            theme.metric("Cycles", f"{n_cyc}", "in range")
            theme.metric(
                "Peak Discharge", f"{max_dcap:.4f} Ah" if max_dcap is not None else "—",
                f"@ cycle {cyc_dcap}" if cyc_dcap is not None else "—", tone="amber",
            )
            theme.metric(
                "Max Coulombic Eff", f"{max_ceff:.2f}%" if max_ceff is not None else "—",
                f"@ cycle {cyc_ceff}" if cyc_ceff is not None else "—", tone="green",
            )
            theme.metric(
                "Max Energy Eff", f"{max_eeff:.2f}%" if max_eeff is not None else "—",
                f"@ cycle {cyc_eeff}" if cyc_eeff is not None else "—", tone="cyan",
            )
            theme.metric("Avg Chg Current", f"{avg_i:.1f} mA", "primary cell")

    # ── Peak preview + protocol phases ───────────────────────────────────────
    with ui.element('div').style(
        'display:grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 0 14px 14px 14px;'
    ):
        # Peak cycle V-Q preview
        with ui.element('div').classes('term-panel'):
            with ui.element('div').classes('term-panel-header'):
                ui.html(
                    f'<span>PEAK CYCLE PREVIEW</span>'
                    f'<span class="meta">{("C" + str(cyc_dcap).zfill(3)) if cyc_dcap is not None else "—"}</span>'
                )
            with ui.element('div').classes('term-panel-body').style('padding: 6px;'):
                if cyc_dcap is not None and state.dp is not None:
                    fig = charts.mini_preview(
                        charts.vc_traces(state.dp, [cyc_dcap], "turbo", single_color=charts.AMBER),
                        height=200,
                    )
                    ui.plotly(fig).classes('w-full').style('height: 200px;')
                else:
                    ui.html('<div class="term-empty" style="padding:30px;">// NO PEAK DATA //</div>')

        # Test protocol phases
        with ui.element('div').classes('term-panel'):
            with ui.element('div').classes('term-panel-header'):
                ui.html('<span>TEST PROTOCOL PHASES</span><span class="meta">CHG/DCHG CURRENT BANDS</span>')
            with ui.element('div').classes('term-panel-body').style('padding: 0; max-height: 220px; overflow: auto;'):
                _render_phases_table(rp)


def _render_phases_table(rp) -> None:
    """Detect constant-current phases by sequential Cycle no and render a tight table."""
    df_s = rp.sort_values('Cycle no').reset_index(drop=True)
    if df_s.empty:
        ui.html('<div class="term-empty">// NO PHASES //</div>')
        return

    phases = []
    cv  = df_s.iloc[0]['Current (mA)']
    cdv = df_s.iloc[0]['DChg Current (mA)']
    sc  = int(df_s.iloc[0]['Cycle no'])
    lc  = sc
    for i in range(1, len(df_s)):
        v   = df_s.iloc[i]['Current (mA)']
        dv  = df_s.iloc[i]['DChg Current (mA)']
        cyc = int(df_s.iloc[i]['Cycle no'])
        if abs(v - cv) <= 1.0 and abs(dv - cdv) <= 1.0:
            lc = cyc
        else:
            phases.append((len(phases) + 1, round(cv), round(cdv), sc, lc, lc - sc + 1))
            cv, cdv, sc, lc = v, dv, cyc, cyc
    phases.append((len(phases) + 1, round(cv), round(cdv), sc, lc, lc - sc + 1))

    rows = ''.join(
        f'<tr>'
        f'<td>{p[0]:02d}</td>'
        f'<td class="num">{p[1]}</td>'
        f'<td class="num">{p[2]}</td>'
        f'<td class="num">{p[3]}</td>'
        f'<td class="num">{p[4]}</td>'
        f'<td class="num">{p[5]}</td>'
        f'</tr>'
        for p in phases
    )
    ui.html(
        '<table class="term-table">'
        '<thead><tr>'
        '<th>#</th><th class="num">CHG (mA)</th><th class="num">DCHG (mA)</th>'
        '<th class="num">START</th><th class="num">END</th><th class="num">COUNT</th>'
        '</tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table>'
    )
