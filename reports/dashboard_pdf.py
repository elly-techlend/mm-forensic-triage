from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import os
from datetime import datetime

def generate_dashboard_pdf(case_id, case_dir, total_debits, total_credits, counterparties, telecoms):
    pdf_path = os.path.join(case_dir, f"{case_id}_Intel_Summary.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph(f"Intelligence Summary: {case_id}", styles['Heading1']))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Financial Summary
    elements.append(Paragraph("1. Financial Impact", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    fin_data = [
        ['Metric', 'Amount (UGX)'],
        ['Total Money Sent (Debits)', f"{total_debits:,}"],
        ['Total Money Received (Credits)', f"{total_credits:,}"],
        ['Net Flow', f"{total_credits - total_debits:,}"]
    ]
    fin_table = Table(fin_data, colWidths=[250, 150])
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 20))

    # Top Counterparties
    elements.append(Paragraph("2. Top Counterparties", styles['Heading2']))
    elements.append(Spacer(1, 10))
    cp_data = [['Name / Entity', 'Interactions']]
    for name, count in counterparties:
        cp_data.append([name, str(count)])
        
    cp_table = Table(cp_data, colWidths=[250, 100])
    cp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(cp_table)
    elements.append(Spacer(1, 20))

    # Telecom Distribution
    elements.append(Paragraph("3. Telecom Distribution", styles['Heading2']))
    elements.append(Spacer(1, 10))
    tel_data = [['Telecom Network', 'Message Count']]
    for t, count in telecoms:
        tel_data.append([t, str(count)])
        
    tel_table = Table(tel_data, colWidths=[250, 100])
    tel_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(tel_table)

    doc.build(elements)
    return pdf_path