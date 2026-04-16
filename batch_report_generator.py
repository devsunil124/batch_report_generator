import pandas as pd
import NewareNDA
import os
import glob

def analyze_single_file(file_path):
    """
    Performs the calculations for a single .ndax file and returns a DataFrame.
    """
    try:
        df = NewareNDA.read(file_path)
        report_data = []

        # Get unique cycles (exclude cycle 0)
        cycles = sorted(df['Cycle'].unique())
        if 0 in cycles: cycles.remove(0)

        for cycle in cycles:
            cyc_df = df[df['Cycle'] == cycle]
            if cyc_df.empty: continue

            # Identify Steps
            chg_df = cyc_df[cyc_df['Status'] == 'CC_Chg']
            dchg_df = cyc_df[cyc_df['Status'].isin(['CC_DChg', 'CCCV_DChg'])]
            rest_df = cyc_df[cyc_df['Status'] == 'Rest']

            # 1. Time (Charging only)
            if not chg_df.empty:
                t_start = chg_df['Timestamp'].iloc[0]
                t_end = chg_df['Timestamp'].iloc[-1]
                time_hrs = (t_end - t_start).total_seconds() / 3600
            else:
                time_hrs = 0

            # 2. Current
            avg_current = chg_df['Current(mA)'].mean() if not chg_df.empty else 0

            # 3. Capacities
            chg_cap = chg_df['Charge_Capacity(mAh)'].max() / 1000 if not chg_df.empty else 0
            dchg_cap = dchg_df['Discharge_Capacity(mAh)'].max() / 1000 if not dchg_df.empty else 0

            # 4. Coulombic Efficiency
            c_eff = (dchg_cap / chg_cap * 100) if chg_cap > 0 else 0

            # 5. Energy
            chg_energy = chg_df['Charge_Energy(mWh)'].max() / 1000 if not chg_df.empty else 0
            dchg_energy = dchg_df['Discharge_Energy(mWh)'].max() / 1000 if not dchg_df.empty else 0
            
            # 6. Energy Efficiency
            eng_eff = (dchg_energy / chg_energy * 100) if chg_energy > 0 else 0

            # 7. Voltages
            v_end_chg = chg_df['Voltage'].iloc[-1] if not chg_df.empty else 0
            v_start_dchg = dchg_df['Voltage'].iloc[0] if not dchg_df.empty else 0

            # 8. OCV Logic
            def get_ocv(step_dataframe, current_cycle_num):
                if step_dataframe.empty: return "-"
                last_step_idx = step_dataframe['Step_Index'].iloc[-1]
                
                # Strategy A: Rest in CURRENT cycle AFTER action
                future_rests = df[
                    (df['Cycle'] == current_cycle_num) & 
                    (df['Status'] == 'Rest') & 
                    (df['Step_Index'] > last_step_idx)
                ]
                if not future_rests.empty:
                    next_rest_idx = future_rests['Step_Index'].min()
                    target_rest = future_rests[future_rests['Step_Index'] == next_rest_idx]
                    return target_rest['Voltage'].iloc[-1]
                
                # Strategy B: Rest at START of NEXT cycle
                next_cycle_rests = df[
                    (df['Cycle'] == current_cycle_num + 1) & 
                    (df['Status'] == 'Rest')
                ]
                if not next_cycle_rests.empty:
                    first_step_idx = next_cycle_rests['Step_Index'].min()
                    target_rest = next_cycle_rests[next_cycle_rests['Step_Index'] == first_step_idx]
                    return target_rest['Voltage'].iloc[-1]

                return "-"

            ocv_after_chg = get_ocv(chg_df, cycle)
            ocv_after_dchg = get_ocv(dchg_df, cycle)

            report_data.append({
                'Cycle no': int(cycle),
                'Time (hrs)': round(time_hrs, 2),
                'Current (mA)': round(avg_current, 1),
                'Chg Capacity (Ah)': round(chg_cap, 5),
                'DChg capacity (Ah)': round(dchg_cap, 5),
                'Coulombic Efficiency (%)': round(c_eff, 2),
                'Chg. Energy (Wh)': round(chg_energy, 5),
                'DChg. Energy (Wh)': round(dchg_energy, 5),
                'Energy Efficiency (%)': round(eng_eff, 2),
                'Voltage End of Chg': round(v_end_chg, 4),
                'Voltage Start of Dchg': round(v_start_dchg, 4),
                'OCV after Chg': round(ocv_after_chg, 4) if ocv_after_chg != "-" else "-",
                'OCV after DChg': round(ocv_after_dchg, 4) if ocv_after_dchg != "-" else "-"
            })

        return pd.DataFrame(report_data)

    except Exception as e:
        print("Error analyzing {0}: {1}".format(file_path, e))
        return None

def process_batch():
    # Find all .ndax files in the current directory
    current_folder = os.getcwd()
    files = glob.glob(os.path.join(current_folder, "*.ndax"))
    
    if not files:
        print("No .ndax files found in this folder!")
        return

    output_filename = "Master_Summary_Report.xlsx"
    
    print("Found {0} files. Starting batch process...".format(len(files)))
    print("-" * 40)

    # Create the Excel Writer
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        for file_path in files:
            # Get filename only (e.g., "S-36.ndax")
            base_name = os.path.basename(file_path)
            print("Processing: {0}...".format(base_name))
            
            # Get the data
            df_result = analyze_single_file(file_path)
            
            if df_result is not None and not df_result.empty:
                # Excel sheet names cannot be longer than 31 chars
                # We remove .ndax and truncate if necessary
                sheet_name = base_name.replace(".ndax", "")[:31]
                
                # Write to a specific sheet
                df_result.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                print("  -> Skipping {0} (Empty or Error)".format(base_name))

    print("-" * 40)
    print("Batch complete! All data saved to: {0}".format(output_filename))

if __name__ == "__main__":
    process_batch()