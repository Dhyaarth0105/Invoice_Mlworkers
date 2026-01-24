"""PDF generation utilities for invoices"""
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from decimal import Decimal
import os


def generate_invoice_pdf(invoice, items, company, client):
    """Generate PDF for tax invoice using ReportLab"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=15*mm, leftMargin=15*mm,
                           topMargin=15*mm, bottomMargin=15*mm)
    
    # Container for the 'Flowable' objects
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#000000'),
        alignment=1,  # TA_CENTER
        spaceAfter=5,
        fontName='Helvetica-Bold',
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#000000'),
        alignment=0,  # TA_LEFT
        fontName='Helvetica',
    )
    
    # Title
    elements.append(Paragraph("TAX INVOICE", title_style))
    elements.append(Paragraph("ORIGINAL", normal_style))
    elements.append(Spacer(1, 8*mm))
    
    # Company and Client details in two columns
    company_data = []
    
    # Seller column
    seller_data = [
        "<b>SELLER</b>",
        company.name or "",
        company.address or "",
    ]
    if company.cin:
        seller_data.append(f"CIN NO.: {company.cin}")
    if company.email:
        seller_data.append(f"Email: {company.email}")
    if company.gstin:
        seller_data.append(f"GSTIN: {company.gstin}")
    if company.phone:
        seller_data.append(f"Contact: {company.phone}")
    if company.pan:
        seller_data.append(f"PAN: {company.pan}")
    
    # Buyer column
    buyer_data = [
        "<b>BUYER</b>",
        client.name or "",
        client.address or "" if hasattr(client, 'address') and client.address else "",
    ]
    if client.email:
        buyer_data.append(f"Email: {client.email}")
    if client.phone:
        buyer_data.append(f"Phone: {client.phone}")
    
    # Make both columns same length
    max_len = max(len(seller_data), len(buyer_data))
    while len(seller_data) < max_len:
        seller_data.append("")
    while len(buyer_data) < max_len:
        buyer_data.append("")
    
    # Combine into table
    company_table_data = [[Paragraph(s, normal_style), Paragraph(b, normal_style)] 
                          for s, b in zip(seller_data, buyer_data)]
    
    company_table = Table(company_table_data, colWidths=[90*mm, 90*mm])
    company_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.grey),
        ('BACKGROUND', (1, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 5*mm))
    
    # Invoice details in grid format
    details_data = [
        ["Place of Supply (Seller's):", company.address[:60] if company.address else "-", 
         "Vendor Code:", invoice.vendor_code or "-"],
        ["Seller's GSTIN NO:", company.gstin or "-", 
         "Seller's PAN:", company.pan or "-"],
        ["INVOICE NO:", invoice.invoice_number, 
         "INVOICE DATE:", invoice.invoice_date.strftime("%d/%m/%Y")],
    ]
    
    if invoice.po_number:
        po_date_str = invoice.po_date.strftime("%d/%m/%Y") if invoice.po_date else "-"
        details_data.append(["P.O.No:", invoice.po_number, 
                           "P.O. Date:", po_date_str])
    
    details_data.append(["Place of Supply (Buyer's):", invoice.place_of_supply or "-", 
                        "State Code:", invoice.state_code or "-"])
    
    details_table_data = []
    for row in details_data:
        details_table_data.append([
            Paragraph(f"<b>{row[0]}</b>", normal_style),
            Paragraph(row[1], normal_style),
            Paragraph(f"<b>{row[2]}</b>", normal_style),
            Paragraph(row[3], normal_style),
        ])
    
    details_table = Table(details_table_data, colWidths=[45*mm, 45*mm, 45*mm, 45*mm])
    details_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 5*mm))
    
    # Items table
    items_data = [["Sr. No.", "Service Description", "SAC Code", "TOTAL UNIT\n(NOS)", "RATE/UNIT\n(NOS).", "Bill Amount Rs."]]
    
    for idx, item in enumerate(items, 1):
        items_data.append([
            str(idx),
            item.description,
            item.sac_code or "-",
            f"{item.quantity:.2f}",
            f"{item.rate:.2f}",
            f"{item.total:.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[15*mm, 55*mm, 25*mm, 25*mm, 25*mm, 30*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))
    
    # Summary
    summary_data = [
        ["Sub Total", f"{invoice.subtotal:.2f}"],
        [f"Tax: GST: CGST ({invoice.cgst_rate:.2f}%):", f"{invoice.cgst_amount:.2f}"],
        [f"Tax: GST: SGST ({invoice.sgst_rate:.2f}%):", f"{invoice.sgst_amount:.2f}"],
        ["<b>Total</b>", f"<b>{invoice.total:.2f}</b>"],
        ["Amount of Tax subject to Reverse charge:", f"{invoice.reverse_charge_amount:.2f}"],
        ["Reverse Charge (Yes/No):", "YES" if invoice.reverse_charge else "NO"],
    ]
    
    summary_table_data = []
    for row in summary_data:
        summary_table_data.append([
            Paragraph(row[0], normal_style),
            Paragraph(row[1], normal_style),
        ])
    
    summary_table = Table(summary_table_data, colWidths=[120*mm, 60*mm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('LINEBELOW', (0, 2), (-1, 2), 2, colors.black),
        ('LINEABOVE', (0, 3), (-1, 3), 2, colors.black),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 5*mm))
    
    # Amount in words
    amount_words = invoice.get_amount_in_words()
    elements.append(Paragraph(f"<b>Total Amount in Words:</b><br/>{amount_words}", normal_style))
    elements.append(Spacer(1, 10*mm))
    
    # Signature and Stamp - left aligned
    signature_elements = []
    
    # Add company name
    signature_elements.append(Paragraph(f"<b>For, {company.name}</b>", normal_style))
    signature_elements.append(Spacer(1, 5*mm))
    
    # Add stamp if available
    if company.stamp:
        try:
            stamp_path = company.stamp.path
            if os.path.exists(stamp_path):
                # Create stamp image (circular stamp typically 40-50mm)
                stamp_img = Image(stamp_path, width=45*mm, height=45*mm, kind='proportional')
                signature_elements.append(stamp_img)
                signature_elements.append(Spacer(1, 5*mm))
        except Exception as e:
            # If stamp path doesn't exist or error, skip stamp
            pass
    
    # Add authorized signatory text
    signature_elements.append(Paragraph("AUTHORIZED SIGNATORY", normal_style))
    
    # Add all signature elements
    for elem in signature_elements:
        elements.append(elem)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
    return response
