"""PDF generation utilities for invoices"""
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from decimal import Decimal
import os


def generate_invoice_pdf(invoice, items, company, client):
    """Generate PDF for tax invoice using ReportLab - matching exact format from image"""
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
        alignment=TA_CENTER,
        spaceAfter=5,
        fontName='Helvetica-Bold',
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#000000'),
        alignment=TA_LEFT,
        fontName='Helvetica',
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=normal_style,
        fontName='Helvetica-Bold',
    )
    
    # Title: TAX INVOICE
    elements.append(Paragraph("TAX INVOICE", title_style))
    elements.append(Spacer(1, 3*mm))
    
    # Invoice Type Checkboxes (ORIGINAL/DUPLICATE/TRIPLICATE)
    invoice_type_data = [
        ["☑ ORIGINAL", "☐ DUPLICATE", "☐ TRIPLICATE"]
    ]
    invoice_type_table = Table(invoice_type_data, colWidths=[60*mm, 60*mm, 60*mm])
    invoice_type_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), TA_LEFT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(invoice_type_table)
    elements.append(Spacer(1, 5*mm))
    
    # Company Details (Top Section - Full Width)
    company_details = []
    company_details.append(Paragraph(f"<b>{company.name}</b>", bold_style))
    if company.address:
        company_details.append(Paragraph(company.address, normal_style))
    if company.cin:
        company_details.append(Paragraph(f"CIN NO.: {company.cin}", normal_style))
    if company.email:
        company_details.append(Paragraph(f"Email: {company.email}", normal_style))
    if company.gstin:
        company_details.append(Paragraph(f"GSTIN: {company.gstin}", normal_style))
    if company.phone:
        company_details.append(Paragraph(f"Contact: {company.phone}", normal_style))
    
    for detail in company_details:
        elements.append(detail)
    
    elements.append(Spacer(1, 5*mm))
    
    # Two Column Layout: Recipient (Left) and Invoice Details (Right)
    # Left Column: Recipient Details
    recipient_data = []
    recipient_data.append(Paragraph(f"<b>{client.name}</b>", bold_style))
    if client.address:
        recipient_data.append(Paragraph(client.address, normal_style))
    if hasattr(client, 'gstin') and client.gstin:
        recipient_data.append(Paragraph(f"GSTIN: {client.gstin}", normal_style))
    if hasattr(client, 'pan') and client.pan:
        recipient_data.append(Paragraph(f"PAN: {client.pan}", normal_style))
    
    # Right Column: Invoice Details
    invoice_details_data = []
    # Billing Address
    billing_address = company.address or ""
    if company.address:
        # Try to extract state and pin if available
        invoice_details_data.append(Paragraph(f"<b>Billing Address ({company.name}):</b><br/>{billing_address}", normal_style))
    
    invoice_details_data.append(Spacer(1, 2*mm))
    
    # Vendor Code
    if invoice.vendor_code:
        invoice_details_data.append(Paragraph(f"<b>Vendor Code:</b> {invoice.vendor_code}", normal_style))
    
    # GSTIN and PAN
    if company.gstin:
        invoice_details_data.append(Paragraph(f"<b>GSTIN NO:</b> {company.gstin}", normal_style))
    if company.pan:
        invoice_details_data.append(Paragraph(f"<b>PAN:</b> {company.pan}", normal_style))
    
    invoice_details_data.append(Spacer(1, 2*mm))
    
    # Invoice Number and Date
    invoice_details_data.append(Paragraph(f"<b>INVOICE NO:</b> {invoice.invoice_number}", normal_style))
    invoice_details_data.append(Paragraph(f"<b>INVOICE DATE:</b> {invoice.invoice_date.strftime('%d/%m/%Y')}", normal_style))
    
    # PO Number and Date
    if invoice.po_number:
        invoice_details_data.append(Paragraph(f"<b>P.O.No:</b> {invoice.po_number}", normal_style))
        if invoice.po_date:
            invoice_details_data.append(Paragraph(f"<b>P.O. Date:</b> {invoice.po_date.strftime('%d/%m/%Y')}", normal_style))
    
    # Place of Supply and State Code
    if invoice.place_of_supply:
        invoice_details_data.append(Paragraph(f"<b>Place of Supply:</b> {invoice.place_of_supply}", normal_style))
    if invoice.state_code:
        invoice_details_data.append(Paragraph(f"<b>State Code:</b> {invoice.state_code}", normal_style))
    
    # Make both columns same height
    max_len = max(len(recipient_data), len(invoice_details_data))
    while len(recipient_data) < max_len:
        recipient_data.append(Spacer(1, 0.1*mm))
    while len(invoice_details_data) < max_len:
        invoice_details_data.append(Spacer(1, 0.1*mm))
    
    # Create two-column table
    two_col_data = []
    for i in range(max_len):
        left_item = recipient_data[i] if i < len(recipient_data) else Paragraph("", normal_style)
        right_item = invoice_details_data[i] if i < len(invoice_details_data) else Paragraph("", normal_style)
        two_col_data.append([left_item, right_item])
    
    two_col_table = Table(two_col_data, colWidths=[90*mm, 90*mm])
    two_col_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), TA_LEFT),
        ('ALIGN', (1, 0), (1, -1), TA_LEFT),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(two_col_table)
    elements.append(Spacer(1, 5*mm))
    
    # Items table
    items_data = [["Sr. No.", "Service Description", "SAC Code", "TOTAL UNIT\n(NOS)", "RATE/UNIT\n(NOS).", "Bill Amount\n(Rs.)"]]
    
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
        ('ALIGN', (0, 0), (0, -1), TA_CENTER),
        ('ALIGN', (1, 0), (1, -1), TA_LEFT),
        ('ALIGN', (2, 0), (2, -1), TA_CENTER),
        ('ALIGN', (3, 0), (-1, -1), TA_RIGHT),
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
        ('ALIGN', (0, 0), (0, -1), TA_LEFT),
        ('ALIGN', (1, 0), (1, -1), TA_RIGHT),
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
    elements.append(Spacer(1, 3*mm))
    
    # Amount in words
    amount_words = invoice.get_amount_in_words()
    elements.append(Paragraph(f"<b>Rupees (in words):</b> {amount_words}", normal_style))
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
