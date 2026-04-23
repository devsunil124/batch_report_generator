# ZnBr Battery Analysis Dashboard

Welcome to the **ZnBr Battery Analysis Dashboard**, a premium, interactive web-based analytics suite built with Streamlit and Plotly. This tool is designed to process, analyze, and visualize Zinc-Bromine (ZnBr) cell telemetry data stored in `.ndax` files.

## 🌟 Features

* **Folder-based Data Loading:** Easily browse and select the directory containing your `.ndax` telemetry files through an intuitive UI.
* **Side-by-Side Comparison:** Compare a primary battery cell against a secondary cell with overlapping metrics and visualizations.
* **Cycle Range Filtering:** Filter your data by specific cycle ranges for targeted analysis.
* **Automated Data Processing:** Seamlessly processes `.ndax` files using the `NewareNDA` library to extract capacities, efficiencies, energies, and voltage points.
* **Comprehensive Visualizations:** 
    * **Summary Metrics:** High-level KPIs and test protocol phase breakdowns.
    * **Trend Analysis:** Line graphs tracking capacity and efficiency metrics over multiple cycles.
    * **Cycle Curves:** Voltage vs. Capacity traces with customizable cycle selection (e.g., all, every 5th, 10th, etc.).
    * **Interval Groups:** Multi-interval overlay with distinct color palettes.
    * **Full-Screen Interactive Graphs:** Expandable plots for detailed data inspection.
* **Raw Data Export:** View raw processed reports and download them as CSVs.

## 🛠 Prerequisites

Before running the dashboard, ensure you have Python installed on your system. You will also need to install the required dependencies.

The main dependencies include:
* `streamlit`
* `pandas`
* `plotly`
* `NewareNDA`

You can install them via pip:

```bash
pip install streamlit pandas plotly NewareNDA
```

## 🚀 How to Run the App

1. Open your terminal or command prompt.
2. Navigate to the directory containing `app.py`.
3. Run the following Streamlit command:

```bash
streamlit run app.py
```

4. The dashboard will automatically open in your default web browser (typically at `http://localhost:8501`).

## 📁 Using the Dashboard

1. **Select Data Source:** Once the app is running, use the sidebar to click the **Browse** button and select the folder where your `.ndax` files are stored. The app will remember your last selected folder.
2. **Choose Cells:** Select your **Primary Cell** from the dropdown. Optionally, select a **Compare Cell** to view two datasets side-by-side.
3. **Analyze:** Navigate through the different tabs (Summary, Trends, Cycle Curves, Interval Groups, Full Screen Graph, Raw Data) to explore your battery telemetry. Adjust the **Cycle Range** slider in the sidebar to narrow down your analysis.

## 📝 Notes

* **Cell Metadata:** You can include a `cell_metadata.csv` file in your data folder to automatically display experimental notes and configuration details for your cells. It should have columns like `Cell Name`, `Configuration & Changes`, and `Experimental Notes / Reason to Stop`.
* **Performance:** Very large `.ndax` files may take a few moments to load and process. The app displays file sizes in the sidebar to help you gauge expected loading times.
