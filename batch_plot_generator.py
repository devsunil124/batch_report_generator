import NewareNDA
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

def plot_file(file_path, output_folder):
    filename = os.path.basename(file_path)
    save_path = os.path.join(output_folder, filename.replace(".ndax", ".png"))
    
    print(f"Plotting: {filename}...")

    try:
        # 1. Read Data
        df = NewareNDA.read(file_path)
        
        # 2. Setup the plot
        plt.figure(figsize=(10, 7))
        
        # Get unique cycles
        cycles = sorted(df['Cycle'].unique())
        
        # Filter out cycle 0 (usually setup/rest)
        if 0 in cycles: cycles.remove(0)

        # 3. Loop through cycles and plot
        for cycle in cycles:
            cyc_df = df[df['Cycle'] == cycle]
            
            # Plot Charge (Voltage vs Charge Capacity)
            # We filter for Charging status (CC_Chg)
            chg_data = cyc_df[cyc_df['Status'] == 'CC_Chg']
            if not chg_data.empty:
                plt.plot(chg_data['Charge_Capacity(mAh)'], chg_data['Voltage'], 
                         color='red', linewidth=0.8, alpha=0.6)

            # Plot Discharge (Voltage vs Discharge Capacity)
            # We filter for Discharging status (CC_DChg or CCCV_DChg)
            dchg_data = cyc_df[cyc_df['Status'].isin(['CC_DChg', 'CCCV_DChg'])]
            if not dchg_data.empty:
                plt.plot(dchg_data['Discharge_Capacity(mAh)'], dchg_data['Voltage'], 
                         color='red', linewidth=0.8, alpha=0.6)

        # 4. Formatting to match your image
        plt.title(f"Voltage vs. Capacity - {filename}", fontsize=14)
        plt.xlabel("Capacity (mAh)", fontsize=12)
        plt.ylabel("Voltage (V)", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.5)
        
        # Optional: Set axis limits if you want them fixed
        # plt.ylim(2.0, 4.5) 

        # 5. Save and Close
        plt.savefig(save_path, dpi=150)
        plt.close() # Close memory to prevent crashing on 30+ files
        
    except Exception as e:
        print(f"Error plotting {filename}: {e}")

def batch_plot():
    # Create output folder if it doesn't exist
    output_folder = "Graphs"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Find all .ndax files
    current_folder = os.getcwd()
    files = glob.glob(os.path.join(current_folder, "*.ndax"))

    if not files:
        print("No .ndax files found!")
        return

    print(f"Found {len(files)} files. Generating graphs...")
    print("-" * 40)

    for file_path in files:
        plot_file(file_path, output_folder)

    print("-" * 40)
    print(f"Done! Check the '{output_folder}' folder for your images.")

if __name__ == "__main__":
    batch_plot()