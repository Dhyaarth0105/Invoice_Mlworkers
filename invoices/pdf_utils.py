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
                           rightMargin=10*mm, leftMargin=10*mm,
                           topMargin=10*mm, bottomMargin=10*mm)
    
    # Container for the 'Flowable' objects
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    company_title_style = ParagraphStyle(
        'CompanyTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=2,
        fontName='Helvetica-Bold',
    )
    
    company_detail_style = ParagraphStyle(
        'CompanyDetail',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=1,
        fontName='Helvetica',
    )
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=2,
        fontName='Helvetica-Bold',
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.black,
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=10,
    )
    
    bold_style = ParagraphStyle(
        'Bold',
        parent=normal_style,
        fontName='Helvetica-Bold',
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=normal_style,
        fontSize=7,
    )
    
    right_style = ParagraphStyle(
        'Right',
        parent=normal_style,
        alignment=TA_RIGHT,
    )
    
    # ==================== COMPANY HEADER ====================
    # Company Name (Large, Bold, Centered)
    elements.append(Paragraph(f"<b>{company.name}</b>", company_title_style))
    
    # Company Address and Details (Centered)
    if company.address:
        elements.append(Paragraph(company.address, company_detail_style))
    if company.cin:
        elements.append(Paragraph(f"CIN NO. : {company.cin}", company_detail_style))
    if company.email:
        elements.append(Paragraph(f"E mail : {company.email}", company_detail_style))
    if company.gstin:
        elements.append(Paragraph(f"GSTIN : {company.gstin}", company_detail_style))
    if company.phone:
        elements.append(Paragraph(f"Contact : {company.phone}", company_detail_style))
    
    elements.append(Spacer(1, 3*mm))
    
    # ==================== TAX INVOICE TITLE WITH CHECKBOXES ====================
    # Create a table with TAX INVOICE on left and checkboxes on right
    invoice_type_box = """( ORIGINAL )
( DUPLICATE )
( TRIPLICATE )"""
    
    title_row = [
        [Paragraph("", normal_style), 
         Paragraph("<b>TAX INVOICE</b>", title_style),
         Paragraph(invoice_type_box, small_style)]
    ]
    
    title_table = Table(title_row, colWidths=[50*mm, 80*mm, 50*mm])
    title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (2, 0), (2, 0), 0.5, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 3*mm))
    
    # ==================== CLIENT AND INVOICE DETAILS (TWO COLUMNS) ====================
    # Left Column: Client (Recipient) Details
    client_text = f"<b>{client.name}</b><br/>"
    if client.address:
        # Clean up address formatting
        addr_lines = client.address.replace('\r\n', '<br/>').replace('\n', '<br/>')
        client_text += addr_lines
    
    # Right Column: Billing Address + Invoice Details
    right_text = f"<b>Billing Address ({company.name}):</b><br/>"
    if company.address:
        right_text += f"{company.address}<br/>"
    # Add state/pin if in place of supply
    if invoice.place_of_supply:
        right_text += f"Surat, Pin - 394130 ( Gujarat , INDIA )<br/>"
    if invoice.vendor_code:
        right_text += f"<b>Vendor Code :</b> {invoice.vendor_code}<br/>"
    if company.gstin:
        right_text += f"<b>GSTIN NO:</b> {company.gstin}<br/>"
    if company.pan:
        right_text += f"<b>PAN:</b> {company.pan}<br/>"
    right_text += f"<b>INVOICE NO:</b> {invoice.invoice_number}<br/>"
    right_text += f"<b>INVOICE DATE:</b> {invoice.invoice_date.strftime('%d/%m/%Y')}<br/>"
    if invoice.po_number:
        right_text += f"<b>P.O.No :</b> {invoice.po_number}<br/>"
    if invoice.po_date:
        right_text += f"<b>P.O. Date:</b> {invoice.po_date.strftime('%d/%m/%Y')}<br/>"
    if invoice.place_of_supply:
        right_text += f"<b>Place of Supply :</b> {invoice.place_of_supply}<br/>"
    if invoice.state_code:
        right_text += f"<b>State Code -</b> {invoice.state_code}"
    
    two_col_data = [[
        Paragraph(client_text, normal_style),
        Paragraph(right_text, normal_style)
    ]]
    
    two_col_table = Table(two_col_data, colWidths=[95*mm, 95*mm])
    two_col_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBEFORE', (1, 0), (1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(two_col_table)
    elements.append(Spacer(1, 2*mm))
    
    # ==================== ITEMS TABLE ====================
    # Header row
    items_header = [
        Paragraph("<b>Sr.<br/>No:</b>", normal_style),
        Paragraph("<b>Service Description</b>", normal_style),
        Paragraph("<b>SAC Code</b>", normal_style),
        Paragraph("<b>TOTAL UNIT (NOS)</b>", normal_style),
        Paragraph("<b>RATE/UNIT (NOS).</b>", normal_style),
        Paragraph("<b>Bill Amount<br/>Rs.</b>", normal_style)
    ]
    
    items_data = [items_header]
    
    for idx, item in enumerate(items, 1):
        items_data.append([
            Paragraph(str(idx), normal_style),
            Paragraph(item.description, normal_style),
            Paragraph(item.sac_code or "-", normal_style),
            Paragraph(f"{item.quantity:.2f}", right_style),
            Paragraph(f"{item.rate:.2f}", right_style),
            Paragraph(f"{item.total:.2f}", right_style)
        ])
    
    # Add empty rows if needed (to match original format)
    while len(items_data) < 5:
        items_data.append([
            Paragraph("", normal_style),
            Paragraph("", normal_style),
            Paragraph("", normal_style),
            Paragraph("", normal_style),
            Paragraph("", normal_style),
            Paragraph("", normal_style)
        ])
    
    items_table = Table(items_data, colWidths=[12*mm, 58*mm, 22*mm, 30*mm, 28*mm, 40*mm])
    items_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.85, 0.85, 0.85)),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(items_table)
    
    # ==================== SUMMARY TABLE ====================
    summary_data = [
        [Paragraph("", normal_style), Paragraph("<b>Sub Total</b>", right_style), Paragraph(f"<b>{invoice.subtotal:,.2f}</b>", right_style)],
        [Paragraph("", normal_style), Paragraph(f"Tax: GST : CGST ( {invoice.cgst_rate:.0f} % )", right_style), Paragraph(f"{invoice.cgst_amount:,.2f}", right_style)],
        [Paragraph("", normal_style), Paragraph(f"Tax: GST: SGST ( {invoice.sgst_rate:.0f} % )", right_style), Paragraph(f"{invoice.sgst_amount:,.2f}", right_style)],
        [Paragraph("", normal_style), Paragraph("<b>Total</b>", right_style), Paragraph(f"<b>{invoice.total:,.2f}</b>", right_style)],
        [Paragraph("", normal_style), Paragraph("Amount of Tax subject to Reverse charge", right_style), Paragraph(f"{invoice.reverse_charge_amount:.2f}", right_style)],
        [Paragraph("", normal_style), Paragraph("Reverse Charge (Yes/ No)", right_style), Paragraph("YES" if invoice.reverse_charge else "NO", right_style)],
    ]
    
    summary_table = Table(summary_data, colWidths=[70*mm, 80*mm, 40*mm])
    summary_table.setStyle(TableStyle([
        ('BOX', (1, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (1, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 2*mm))
    
    # ==================== AMOUNT IN WORDS ====================
    amount_words = invoice.get_amount_in_words()
    words_data = [[Paragraph(f"<b>Rupees -</b> {amount_words.upper()}", normal_style)]]
    words_table = Table(words_data, colWidths=[190*mm])
    words_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(words_table)
    elements.append(Spacer(1, 5*mm))
    
    # ==================== SIGNATURE AND STAMP ====================
    signature_left = Paragraph(f"<b>For, {company.name}</b>", normal_style)
    
    # Create signature section
    sig_data = [[signature_left, Paragraph("", normal_style)]]
    sig_table = Table(sig_data, colWidths=[95*mm, 95*mm])
    sig_table.setStyle(TableStyle([
        ('BOX', (0, 0), (0, 0), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 3*mm))
    
    # Add stamp if available
    if company.stamp:
        try:
            stamp_path = company.stamp.path
            if os.path.exists(stamp_path):
                stamp_img = Image(stamp_path, width=40*mm, height=40*mm, kind='proportional')
                elements.append(stamp_img)
                elements.append(Spacer(1, 3*mm))
        except Exception as e:
            pass
    else:
        # Add space for stamp
        elements.append(Spacer(1, 25*mm))
    
    # Authorized signatory with box
    auth_data = [[Paragraph("<b>AUTHORIZED SIGNATORY</b>", normal_style)]]
    auth_table = Table(auth_data, colWidths=[60*mm])
    auth_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(auth_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
    return response
