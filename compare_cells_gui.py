import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, ttk
import os

# File to load
FILE_NAME = "Master_Summary_Report.xlsx"

def load_sheet_names():
    """Loads sheet names from the Excel file."""
    if not os.path.exists(FILE_NAME):
        messagebox.showerror("Error", f"File not found:\n{FILE_NAME}\n\nPlease make sure the Excel file is in the same folder as this script.")
        root.destroy()
        return []
    
    try:
        xls = pd.ExcelFile(FILE_NAME)
        return xls.sheet_names
    except Exception as e:
        messagebox.showerror("Error", f"Could not read Excel file:\n{e}")
        root.destroy()
        return []

def plot_data():
    """Gets selected sheets and plots comparisons."""
    # Get selected indices from the listbox
    selected_indices = list_box.curselection()
    
    if not selected_indices:
        messagebox.showwarning("No Selection", "Please select at least one cell to compare.")
        return

    selected_sheets = [list_box.get(i) for i in selected_indices]
    
    print(f"Plotting: {', '.join(selected_sheets)}...")

    try:
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
        
        # Define a list of markers to cycle through for distinction
        markers = ['o', 's', '^', 'v', 'D', 'x', '*']

        for i, sheet in enumerate(selected_sheets):
            # Read specific sheet
            df = pd.read_excel(FILE_NAME, sheet_name=sheet)
            
            # Pick a marker
            marker = markers[i % len(markers)]
            
            # Plot 1: Discharge Capacity
            ax1.plot(df['Cycle no'], df['DChg capacity (Ah)'], 
                     marker=marker, markersize=4, linewidth=1.5, label=sheet)
            
            # Plot 2: Coulombic Efficiency
            ax2.plot(df['Cycle no'], df['Coulombic Efficiency (%)'], 
                     marker=marker, markersize=4, linewidth=1.5, label=sheet)

        # Formatting Top Graph
        ax1.set_ylabel('Discharge Capacity (Ah)', fontsize=12, fontweight='bold')
        ax1.set_title('Comparison: Cycle Life', fontsize=14)
        ax1.grid(True, linestyle='--', alpha=0.6)
        ax1.legend()

        # Formatting Bottom Graph
        ax2.set_ylabel('Coulombic Efficiency (%)', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Cycle Number', fontsize=12, fontweight='bold')
        ax2.set_title('Comparison: Efficiency', fontsize=14)
        ax2.grid(True, linestyle='--', alpha=0.6)
        
        # Adjust layout and show
        plt.tight_layout()
        plt.show()

    except Exception as e:
        messagebox.showerror("Plotting Error", f"An error occurred while plotting:\n{e}")

# --- GUI Setup ---
root = tk.Tk()
root.title("Neware Data Comparator")
root.geometry("400x500")

# Title Label
lbl_title = tk.Label(root, text="Select Cells to Compare", font=("Arial", 14, "bold"), pady=10)
lbl_title.pack()

# Instructions
lbl_instr = tk.Label(root, text="Hold 'Ctrl' or 'Shift' to select multiple items", font=("Arial", 10), fg="gray")
lbl_instr.pack()

# Frame for Listbox and Scrollbar
frame = tk.Frame(root)
frame.pack(fill="both", expand=True, padx=20, pady=10)

# Scrollbar
scrollbar = tk.Scrollbar(frame)
scrollbar.pack(side="right", fill="y")

# Listbox (List of Sheets)
list_box = tk.Listbox(frame, selectmode=tk.EXTENDED, font=("Arial", 11), yscrollcommand=scrollbar.set)
list_box.pack(side="left", fill="both", expand=True)
scrollbar.config(command=list_box.yview)

# Load Data
sheets = load_sheet_names()
for sheet in sheets:
    list_box.insert(tk.END, sheet)

# Plot Button
btn_plot = tk.Button(root, text="Compare Selected Graphs", font=("Arial", 12, "bold"), 
                     bg="#4CAF50", fg="white", height=2, command=plot_data)
btn_plot.pack(fill="x", padx=20, pady=20)

# Run the App
if sheets: # Only run if sheets loaded successfully
    root.mainloop()