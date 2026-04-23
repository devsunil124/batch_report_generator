import streamlit as st
import os
import glob
import re
from config_manager import save_config

def natural_sort_key(s):
    """
    Generate a key for natural sorting of strings containing numbers.

    Parameters
    ----------
    s : str
        The string to generate a key for.

    Returns
    -------
    list
        A list of string and integer parts for sorting.
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

def file_size_mb(path):
    """
    Calculate the file size in megabytes.

    Parameters
    ----------
    path : str
        The path to the file.

    Returns
    -------
    float
        The file size in MB.
    """
    return os.path.getsize(path) / (1024 * 1024)

def render_premium_css():
    """
    Inject premium CSS styling into the Streamlit application.
    """
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

def render_hero():
    """
    Render the hero banner at the top of the main page.
    """
    st.markdown("""
<div class="hero">
  <span style="font-size:2.6rem;line-height:1;">🔋</span>
  <div>
    <div class="hero-title">ZnBr Battery Analysis Dashboard</div>
    <div class="hero-sub">Zinc-Bromine Cell Telemetry · Professional Reporting Suite</div>
  </div>
</div>
""", unsafe_allow_html=True)

def render_sidebar(saved_path):
    """
    Render the sidebar for folder selection and file picking.

    Parameters
    ----------
    saved_path : str
        The default folder path loaded from configuration.

    Returns
    -------
    folder_path : str
        The selected folder path.
    primary_name : str
        The selected primary cell name.
    primary_file : str
        The absolute path to the primary ndax file.
    secondary_name : str
        The selected secondary cell name, or None if none selected.
    secondary_file : str
        The absolute path to the secondary ndax file, or None.
    """
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center;padding:8px 0 18px;'>
          <div style='font-size:1.8rem;'>⚡</div>
          <div style='font-weight:800;font-size:0.95rem;color:#93C5FD;'>Cell Manager</div>
          <div style='font-size:0.72rem;color:#475569;margin-top:2px;'>ZnBr Analysis Suite</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sid-head">📂 Data Source</div>', unsafe_allow_html=True)
        
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

        all_files = sorted(glob.glob(os.path.join(folder_path, "*.ndax")), key=natural_sort_key)
        all_names = [os.path.basename(os.path.splitext(f)[0]) for f in all_files]
        
        if not all_files:
            st.warning(f"No .ndax files found in {folder_path}")
            st.stop()

        st.markdown('<hr class="my-divider">', unsafe_allow_html=True)

        st.markdown('<div class="sid-head">🗂 Primary Cell</div>', unsafe_allow_html=True)
        search = st.text_input("Search", placeholder="Type S-20…", label_visibility="collapsed")
        filtered = [n for n in all_names if search.lower() in n.lower()] if search else all_names
        if not filtered:
            st.warning("No match found.")
            st.stop()

        primary_name = st.selectbox("Cell", filtered, label_visibility="collapsed")
        primary_file = os.path.join(folder_path, primary_name + ".ndax")
        sz = file_size_mb(primary_file)
        st.caption(f"📦 {sz:.1f} MB {'— large file, please wait' if sz > 10 else ''}")

        st.markdown('<hr class="my-divider">', unsafe_allow_html=True)

        st.markdown('<div class="sid-head">⚖ Compare Cell (Optional)</div>', unsafe_allow_html=True)
        sec_opts = ["— None —"] + [n for n in all_names if n != primary_name]
        secondary_name = st.selectbox("Compare", sec_opts, label_visibility="collapsed")
        
        secondary_file = os.path.join(folder_path, secondary_name + ".ndax") if secondary_name != "— None —" else None
        if secondary_file:
            st.caption(f"📦 {file_size_mb(secondary_file):.1f} MB")

        st.markdown('<hr class="my-divider">', unsafe_allow_html=True)
        st.markdown('<div class="sid-head">🔍 Cycle Range</div>', unsafe_allow_html=True)
        range_placeholder = st.empty()
        
        return folder_path, primary_name, primary_file, secondary_name, secondary_file, range_placeholder
