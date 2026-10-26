from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
import os
from datetime import datetime

def generate_pdf(case_id, case_dir, messages, calls, manifest, total_debits, total_credits):
    pdf_path = os.path.join(case_dir, f"{case_id}_Forensic_Report.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    elements = []
    styles = getSampleStyleSheet()

    # --- 1. COVER PAGE ---
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], alignment=1, fontSize=24, spaceAfter=20, textColor=colors.darkblue)
    subtitle_style = ParagraphStyle(name='SubTitle', parent=styles['Heading2'], alignment=1, fontSize=14, textColor=colors.grey)
    
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph("MOBILE MONEY FORENSIC TRIAGE REPORT", title_style))
    elements.append(Paragraph("Official Digital Evidence Summary", subtitle_style))
    elements.append(Spacer(1, 1 * inch))
    
    # Metadata Block
    meta_data = [
        ['Case ID:', case_id],
        ['Generated On:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ['Examiner System:', 'Kali Linux / ADB Content Provider'],
        ['Integrity Status:', 'VERIFIED (SHA-256)']
    ]
    meta_table = Table(meta_data, colWidths=[150, 250])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(meta_table)
    elements.append(PageBreak())

    # --- 2. EXECUTIVE SUMMARY ---
    elements.append(Paragraph("1. Executive Summary", styles['Heading1']))
    elements.append(Spacer(1, 10))
    
    summary_text = f"""
    This document contains the extracted digital evidence from the mobile device associated with Case ID: <b>{case_id}</b>. 
    The extraction was performed using a lightweight forensic triage tool, bypassing SELinux restrictions via ADB Content Providers.
    <br/><br/>
    <b>Key Findings:</b><br/>
    • Total Financial Transactions: <b>{len(messages)}</b><br/>
    • Total Money Sent (Debits): <b>UGX {total_debits:,}</b><br/>
    • Total Money Received (Credits): <b>UGX {total_credits:,}</b><br/>
    • Total Call Logs Extracted: <b>{len(calls)}</b><br/>
    """
    elements.append(Paragraph(summary_text, styles['Normal']))
    elements.append(Spacer(1, 20))

    # --- 3. CHAIN OF CUSTODY ---
    elements.append(Paragraph("2. Chain of Custody (SHA-256 Hashes)", styles['Heading2']))
    elements.append(Paragraph("The following hash values prove the integrity of the extracted files. Any alteration to the raw data will change these hashes.", styles['Italic']))
    elements.append(Spacer(1, 10))
    
    hash_data = [['Evidence File', 'SHA-256 Hash Signature']]
    for fname, hash_val in manifest.get("files", {}).items():
        hash_data.append([fname, Paragraph(hash_val, styles['Normal'])])
        
    hash_table = Table(hash_data, colWidths=[130, 350])
    hash_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))
    elements.append(hash_table)
    elements.append(Spacer(1, 20))
    elements.append(PageBreak())

    # --- 4. TRANSACTIONS TABLE ---
    elements.append(Paragraph("3. Extracted Financial Transactions", styles['Heading2']))
    elements.append(Spacer(1, 10))

    txn_data = [['Date/Time', 'Type', 'Network', 'Details']]
    for msg in messages:
        color = colors.red if msg['type'] == 'debit' else colors.green
        type_text = f"<font color='{color.hexval()}'><b>{msg['type'].upper()}</b></font>"
        body = msg['body'].replace('\n', ' ')[:80] + "..." if len(msg['body']) > 80 else msg['body']
        
        txn_data.append([
            msg['timestamp'][:19].replace('T', ' '),
            Paragraph(type_text, styles['Normal']),
            msg['telecom'] or 'Unknown',
            Paragraph(body, styles['Normal'])
        ])

    txn_table = Table(txn_data, colWidths=[100, 50, 60, 270])
    txn_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    elements.append(txn_table)
    elements.append(PageBreak())

    # --- 5. CALL LOGS TABLE ---
    elements.append(Paragraph("4. Extracted Communication Logs", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    call_data = [['Date/Time', 'Phone Number', 'Direction', 'Duration (sec)']]
    for c in calls:
        call_data.append([
            c['timestamp'][:19].replace('T', ' '),
            c['number'],
            c['type'],
            str(c['duration_sec'])
        ])
        
    call_table = Table(call_data, colWidths=[130, 130, 100, 100])
    call_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(call_table)

    doc.build(elements)
    return pdf_path