import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import tempfile

def generate_pdf_report(cell_name, start_date, metrics, phases, fig_dcap, fig_ce, df_raw, output_path):
    """
    Generate a professional PDF report containing metadata, KPIs, test phases, charts, and raw data.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    elements = []
    
    # 1. Title & Header
    elements.append(Paragraph("ZnBr Battery Analysis Report", title_style))
    elements.append(Spacer(1, 12))
    
    header_data = [
        ["Cell Name:", cell_name, "Test Start Date:", start_date]
    ]
    header_table = Table(header_data, colWidths=[80, 150, 100, 150])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.darkblue),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # 2. KPI Metrics
    elements.append(Paragraph("Key Performance Indicators (KPIs)", heading_style))
    kpi_data = [["Metric", "Value"]]
    for k, v in metrics.items():
        kpi_data.append([k, v])
        
    kpi_table = Table(kpi_data, colWidths=[200, 200])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f1f3d")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 20))
    
    # 3. Protocol Phases
    elements.append(Paragraph("Test Protocol Phases", heading_style))
    if phases:
        phase_headers = ["Phase", "Chg I (mA)", "DChg I (mA)", "Start", "End", "Count"]
        phase_data = [phase_headers]
        for p in phases:
            phase_data.append([p[h] for h in phase_headers])
            
        phase_table = Table(phase_data, colWidths=[80, 80, 80, 60, 60, 60])
        phase_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#080f1e")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ]))
        elements.append(phase_table)
    else:
        elements.append(Paragraph("No phase data available.", normal_style))
    elements.append(Spacer(1, 20))
    
    # 4. Trend Charts
    elements.append(Paragraph("Performance Trends", heading_style))
    
    # Generate temp images for Plotly figures
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f_dcap, \
         tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f_ce:
        temp_dcap = f_dcap.name
        temp_ce = f_ce.name
        
    try:
        # Increase scale slightly for crispness
        fig_dcap.write_image(temp_dcap, width=700, height=350, scale=2)
        fig_ce.write_image(temp_ce, width=700, height=350, scale=2)
        
        # In ReportLab, we scale images to fit the page width (letter is 612x792)
        # Margins are 40 left, 40 right -> 532 available width
        img_w = 500
        img_h = 250
        elements.append(Image(temp_dcap, width=img_w, height=img_h))
        elements.append(Spacer(1, 10))
        elements.append(Image(temp_ce, width=img_w, height=img_h))
    finally:
        pass # Will delete later to ensure they are available during build
        
    # 5. Raw Data Table
    elements.append(PageBreak())
    elements.append(Paragraph("Raw Cycle Data", heading_style))
    
    if df_raw is not None and not df_raw.empty:
        # To avoid making the PDF hundreds of pages with huge columns, 
        # we will select key columns if there are too many.
        cols_to_print = [
            'Cycle no', 'Time (hrs)', 'Current (mA)', 'DChg Current (mA)',
            'Chg Capacity (Ah)', 'DChg capacity (Ah)', 'Coulombic Efficiency (%)',
            'Energy Efficiency (%)', 'Voltage End of Chg', 'Voltage Start of Dchg'
        ]
        cols = [c for c in cols_to_print if c in df_raw.columns]
        
        # Round the dataframe for printing
        df_print = df_raw[cols].copy()
        
        # Convert to list of lists
        raw_data = [cols] + df_print.fillna("").values.tolist()
        
        raw_table = Table(raw_data, repeatRows=1) # Auto column widths
        raw_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        elements.append(raw_table)
        
    doc.build(elements)
    
    # Cleanup temp files
    try:
        os.remove(temp_dcap)
        os.remove(temp_ce)
    except:
        pass
        
    return output_path
