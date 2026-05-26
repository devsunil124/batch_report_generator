"""Summary sub-view: headline metrics, protocol phases, peak preview."""
from __future__ import annotations
import os
import pandas as pd
from nicegui import ui

from state import state
import charts


def _meta_for(folder: str, cell_name: str) -> tuple[str, str, str]:
    started = "—"
    try:
        if state.df_prim is not None and 'Timestamp' in state.df_prim.columns:
            ts = state.df_prim['Timestamp'].min()
            if ts is not None:
                started = ts.strftime("%Y-%m-%d")
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
                if _cfg and _cfg.lower() != 'nan': cfg = _cfg
                if _nts and _nts.lower() != 'nan': nts = _nts
        except Exception:
            pass
    return started, cfg, nts


def _peak(rp, col: str):
    clean = rp[rp['Chg Capacity (Ah)'] > 0.0001][col].dropna()
    if clean.empty:
        return None, None
    idx = clean.idxmax()
    return float(clean[idx]), int(rp.loc[idx, 'Cycle no'])


def render() -> None:
    rp = state.rp
    if rp is None or rp.empty:
        ui.html('<div class="zn-empty"><h3>No data in selected range</h3>'
                '<p>Adjust the cycle range above.</p></div>')
        return

    theme = state.theme
    started, cfg, nts = _meta_for("library/ndax", state.primary_name or "")

    max_dcap, cyc_dcap = _peak(rp, 'DChg capacity (Ah)')
    max_ceff, cyc_ceff = _peak(rp, 'Coulombic Efficiency (%)')
    max_eeff, cyc_eeff = _peak(rp, 'Energy Efficiency (%)')
    avg_i = float(rp['Current (mA)'].mean()) if 'Current (mA)' in rp else 0.0
    n_cyc = len(rp)

    # ── Metric strip ─────────────────────────────────────────────────────────
    with ui.element('div').style(
        'display:grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 20px;'
    ):
        _metric("Cycles in range", f"{n_cyc}", "")
        _metric(
            "Peak discharge",
            f"{max_dcap:.4f} Ah" if max_dcap is not None else "—",
            f"@ cycle {cyc_dcap}" if cyc_dcap is not None else "—",
            tone="accent",
        )
        _metric(
            "Max coulombic eff",
            f"{max_ceff:.2f}%" if max_ceff is not None else "—",
            f"@ cycle {cyc_ceff}" if cyc_ceff is not None else "—",
            tone="success",
        )
        _metric(
            "Max energy eff",
            f"{max_eeff:.2f}%" if max_eeff is not None else "—",
            f"@ cycle {cyc_eeff}" if cyc_eeff is not None else "—",
            tone="accent",
        )
        _metric("Avg chg current", f"{avg_i:.1f} mA", "primary cell")

    # ── Two-column: peak preview + cell info ─────────────────────────────────
    with ui.element('div').style(
        'display:grid; grid-template-columns: 1.2fr 1fr; gap: 16px; margin-bottom: 20px;'
    ):
        # Peak preview
        with ui.element('div').classes('zn-card'):
            ui.html('<div class="zn-card-header"><div class="zn-h2">Peak cycle preview</div>'
                    f'<span class="zn-chip accent">C{(cyc_dcap or 0):03d}</span></div>')
            if cyc_dcap is not None and state.dp is not None:
                fig = charts.mini_preview(
                    charts.vc_traces(
                        state.dp, [cyc_dcap], "turbo",
                        single_color=charts.primary_color(theme),
                    ),
                    theme, height=200,
                )
                ui.plotly(fig).classes('w-full').style('height: 200px;')
            else:
                ui.html('<div class="zn-empty"><p>No peak data.</p></div>')

        # Cell info
        with ui.element('div').classes('zn-card'):
            ui.html('<div class="zn-card-header"><div class="zn-h2">Cell info</div></div>')
            ui.html(
                f'<div class="zn-kv">'
                f'<div class="k">Started</div><div class="v">{started}</div>'
                f'<div class="k">Configuration</div><div class="v">{cfg}</div>'
                f'<div class="k">Notes / status</div><div class="v">{nts}</div>'
                f'<div class="k">Cycle range</div><div class="v">{state.cycle_start} → {state.cycle_end}</div>'
                f'</div>'
            )

    # ── Protocol phases ──────────────────────────────────────────────────────
    with ui.element('div').classes('zn-card'):
        ui.html('<div class="zn-card-header"><div class="zn-h2">Test protocol phases</div>'
                '<span class="zn-chip">Constant-current bands</span></div>')
        _render_phases(rp)


def _metric(lbl: str, val: str, sub: str, tone: str = "") -> None:
    val_cls = f"val {tone}".strip()
    ui.html(
        f'<div class="zn-metric">'
        f'<div class="lbl">{lbl}</div>'
        f'<div class="{val_cls}">{val}</div>'
        f'<div class="sub">{sub}</div>'
        f'</div>'
    )


def _render_phases(rp) -> None:
    df_s = rp.sort_values('Cycle no').reset_index(drop=True)
    if df_s.empty:
        ui.html('<div class="zn-empty"><p>No phases.</p></div>')
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
        '<div style="overflow-x:auto;"><table class="zn-table">'
        '<thead><tr>'
        '<th>#</th><th class="num">Chg (mA)</th><th class="num">DChg (mA)</th>'
        '<th class="num">Start</th><th class="num">End</th><th class="num">Count</th>'
        '</tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table></div>'
    )
