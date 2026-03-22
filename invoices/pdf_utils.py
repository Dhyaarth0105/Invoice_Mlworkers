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
    """Generate high-fidelity Invoice PDF matching the provided sample format"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=5*mm, leftMargin=5*mm,
                           topMargin=10*mm, bottomMargin=10*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Define Colors (match the provided screenshot: dark blue-gray borders, light gray headers)
    border_color = colors.Color(0.2, 0.3, 0.4)
    header_bg = colors.Color(0.95, 0.96, 0.98)
    
    # Custom Styles
    style_center = ParagraphStyle('Center', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, fontName='Helvetica', leading=11)
    style_center_bold = ParagraphStyle('CenterBold', parent=style_center, fontName='Helvetica-Bold', fontSize=14, leading=18)
    style_left = ParagraphStyle('Left', parent=styles['Normal'], fontSize=8, alignment=TA_LEFT, fontName='Helvetica', leading=10)
    style_left_bold = ParagraphStyle('LeftBold', parent=style_left, fontName='Helvetica-Bold')
    style_right = ParagraphStyle('Right', parent=styles['Normal'], fontSize=8, alignment=TA_RIGHT, fontName='Helvetica')
    style_small = ParagraphStyle('Small', parent=style_left, fontSize=7)
    style_title = ParagraphStyle('Title', parent=style_center, fontSize=12, fontName='Helvetica-Bold', spaceAfter=2)
    style_header_cell = ParagraphStyle('HCell', parent=style_center, fontSize=8, fontName='Helvetica-Bold', leading=9)

    # 1. TAX INVOICE Title
    elements.append(Paragraph("<b>Tax Invoice</b>", style_title))
    elements.append(Spacer(1, 4*mm))

    # 2. COMPANY HEADER BOX (Logo Left, Text Center)
    logo = None
    if company.stamp:
        try:
            if os.path.exists(company.stamp.path):
                logo = Image(company.stamp.path, width=25*mm, height=25*mm)
        except: pass

    company_info = [
        Paragraph(f"<b>{company.name.upper()}</b>", style_center_bold),
        Spacer(1, 2*mm),
        Paragraph(f"{company.address.upper() if company.address else ''}", style_center),
        Paragraph(f"Phone: {company.phone or ''} &nbsp;&nbsp;&nbsp;&nbsp; Email: {company.email or ''}", style_center),
        Paragraph(f"GSTIN: {company.gstin or ''} &nbsp;&nbsp;&nbsp;&nbsp; State: {company.state_code or ''}", style_center),
    ]

    header_table = Table([[logo, company_info]], colWidths=[35*mm, 165*mm])
    header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)

    # 3. BILL TO / INVOICE DETAILS SPLIT
    bill_to_text = [
        Paragraph("<b>Bill To:</b>", style_left),
        Paragraph(f"<b>{invoice.bill_to_name or client.name}</b>", style_left_bold),
        Paragraph(f"{(invoice.bill_to_address or client.address or '').replace('\n', '<br/>')}", style_left),
        Paragraph(f"Contact No: {client.phone or ''} &nbsp;&nbsp; GSTIN: {invoice.bill_to_gstin or client.gstin or ''}", style_left),
        Paragraph(f"State: {invoice.state_code or ''}", style_left),
    ]
    
    invoice_details = [
        Paragraph(f"Inv No: <b>{invoice.invoice_number}</b>", style_left),
        Paragraph(f"Date: <b>{invoice.invoice_date.strftime('%d/%m/%Y')}</b>", style_left),
        Paragraph(f"Vendor Code: <b>{invoice.vendor_code or ''}</b>", style_left),
        Paragraph(f"Order No: <b>{invoice.po_number or ''}</b>", style_left),
        Paragraph(f"Order Date: <b>{invoice.po_date.strftime('%d/%m/%Y') if invoice.po_date else ''}</b>", style_left),
        Paragraph(f"Place of Supply: <b>{invoice.place_of_supply or ''}</b>", style_left),
    ]

    details_table = Table([[bill_to_text, invoice_details]], colWidths=[110*mm, 90*mm])
    details_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('LINEBEFORE', (1, 0), (1, 0), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(details_table)

    # 4. SHIP TO (Full Width)
    ship_to_text = [
        Paragraph(f"<b>Ship To:</b> &nbsp;&nbsp; {invoice.ship_to_name or invoice.bill_to_name or client.name}", style_left),
        Paragraph(f"Address: &nbsp;&nbsp; {(invoice.ship_to_address or invoice.bill_to_address or client.address or '').replace('\n', ', ')}", style_left),
    ]
    ship_to_table = Table([[ship_to_text]], colWidths=[200*mm])
    ship_to_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BACKGROUND', (0, 0), (-1, -1), header_bg),
    ]))
    elements.append(ship_to_table)

    # 5. ITEMS TABLE (8 Columns)
    items_header = [
        Paragraph("#", style_header_cell),
        Paragraph("Item name", style_header_cell),
        Paragraph("HSN/ SAC", style_header_cell),
        Paragraph("Quantity", style_header_cell),
        Paragraph("Unit", style_header_cell),
        Paragraph("Rate/Unit (Rs.)", style_header_cell),
        Paragraph("GST (Rs.)", style_header_cell),
        Paragraph("Amount (Rs.)", style_header_cell)
    ]
    items_data = [items_header]
    
    total_qty = 0
    total_tax_calc = Decimal('0.00')
    hsn_summary = {}

    for idx, item in enumerate(items, 1):
        # Determine tax rates
        if invoice.is_igst:
            tax_rate = invoice.igst_rate
        else:
            tax_rate = invoice.cgst_rate + invoice.sgst_rate
            
        tax_amt = (item.total * tax_rate / 100).quantize(Decimal('0.01'))
        row_total = item.total + tax_amt
        total_qty += item.quantity
        total_tax_calc += tax_amt
        
        # Track for HSN summary
        hsn = item.sac_code or "N/A"
        if hsn not in hsn_summary:
            hsn_summary[hsn] = {'taxable': Decimal('0.00'), 'tax': Decimal('0.00'), 'rate': tax_rate}
        hsn_summary[hsn]['taxable'] += item.total
        hsn_summary[hsn]['tax'] += tax_amt

        items_data.append([
            Paragraph(str(idx), style_center),
            Paragraph(item.description, style_left),
            Paragraph(item.sac_code or "", style_center),
            Paragraph(f"{item.quantity:.0f}", style_right),
            Paragraph(item.uom_display, style_center),
            Paragraph(f"{item.rate:,.2f}", style_right),
            Paragraph(f"{tax_amt:,.2f} ({tax_rate:.0f}%)", style_right),
            Paragraph(f"{row_total:,.2f}", style_right)
        ])

    # Fill empty rows
    for _ in range(max(0, 10 - len(items))):
        items_data.append(["", "", "", "", "", "", "", ""])

    # Total row in items table
    items_data.append([
        Paragraph("<b>Total</b>", style_left), "", "", 
        Paragraph(f"<b>{total_qty:.0f}</b>", style_right), "", "", 
        Paragraph(f"<b>{total_tax_calc:,.2f}</b>", style_right), 
        Paragraph(f"<b>{invoice.total:,.2f}</b>", style_right)
    ])

    col_widths = [10*mm, 70*mm, 20*mm, 15*mm, 15*mm, 22*mm, 23*mm, 25*mm]
    items_table = Table(items_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(items_table)

    # 6. TAX SUMMARY & TOTALS SECTION
    hsn_headers = [
        Paragraph("HSN/ SAC", style_header_cell),
        Paragraph("Taxable amt(Rs.)", style_header_cell),
        Paragraph("CGST (Amt)", style_header_cell),
        Paragraph("SGST (Amt)", style_header_cell),
        Paragraph("Total Tax(Rs.)", style_header_cell)
    ]
    hsn_data = [hsn_headers]
    for hsn, vals in hsn_summary.items():
        cgst_tax = (vals['tax'] / 2) if not invoice.is_igst else 0
        sgst_tax = (vals['tax'] / 2) if not invoice.is_igst else 0
        
        if invoice.is_igst:
            hsn_data.append([
                Paragraph(hsn, style_center), 
                Paragraph(f"{vals['taxable']:,.2f}", style_right), 
                "-", "-", 
                Paragraph(f"{vals['tax']:,.2f}", style_right)
            ])
        else:
            hsn_data.append([
                Paragraph(hsn, style_center), 
                Paragraph(f"{vals['taxable']:,.2f}", style_right), 
                Paragraph(f"{cgst_tax:,.2f}", style_right), 
                Paragraph(f"{sgst_tax:,.2f}", style_right), 
                Paragraph(f"{vals['tax']:,.2f}", style_right)
            ])
    
    hsn_table = Table(hsn_data, colWidths=[25*mm, 30*mm, 25*mm, 25*mm, 25*mm])
    hsn_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    # Right Totals Table
    total_paid = invoice.get_total_paid()
    balance = invoice.get_balance()
    totals_data = [
        ["Sub Total", ":", f"{invoice.subtotal:,.2f}"],
        ["Total", ":", f"{invoice.total:,.2f}"],
        [Paragraph(f"<b>In Words:</b><br/>{invoice.get_amount_in_words().upper()}", style_small), "", ""],
        ["Received", ":", f"{total_paid:,.2f}"],
        ["Balance", ":", f"{balance:,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[30*mm, 5*mm, 25*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('SPAN', (0, 2), (2, 2)),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, border_color),
    ]))

    summary_split = Table([[hsn_table, totals_table]], colWidths=[130*mm, 70*mm])
    summary_split.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(summary_split)

    # 7. TERMS & BANK/SIGNATURE FOOTER
    elements.append(Spacer(1, 2*mm))
    terms = Paragraph(f"<b>Terms & Conditions:</b><br/>{invoice.notes or 'Thanks for doing business with us!'}", style_small)
    elements.append(Table([[terms]], colWidths=[200*mm], style=[('BOX', (0,0),(-1,-1),0.5,border_color)]))
    
    bank_info = [
        Paragraph("<b>Bank Details:</b>", style_left_bold),
        Paragraph(f"Name : {company.bank_name or ''}", style_small),
        Paragraph(f"Account No. : {company.account_number or ''}", style_small),
        Paragraph(f"IFSC code : {company.ifsc_code or ''}", style_small),
        Paragraph(f"Account holder's name : {company.name.upper()}", style_small),
    ]
    
    sig_info = [
        Paragraph(f"For <b>{company.name.upper()}</b>:", style_center),
        Spacer(1, 10*mm),
        Paragraph("________________________", style_center),
        Paragraph("Authorized Signatory", style_center),
    ]

    footer_table = Table([[bank_info, sig_info]], colWidths=[120*mm, 80*mm])
    footer_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('LINEBEFORE', (1, 0), (1, 0), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(footer_table)

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
    return response


def generate_credit_note_pdf(credit_note, items, company, client):
    """Generate high-fidelity Credit Note PDF matching the invoice design"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=5*mm, leftMargin=5*mm,
                           topMargin=10*mm, bottomMargin=10*mm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Define Colors
    border_color = colors.Color(0.2, 0.3, 0.4)
    header_bg = colors.Color(0.95, 0.96, 0.98)
    
    # Custom Styles
    style_center = ParagraphStyle('Center', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, fontName='Helvetica', leading=11)
    style_center_bold = ParagraphStyle('CenterBold', parent=style_center, fontName='Helvetica-Bold', fontSize=14, leading=18)
    style_left = ParagraphStyle('Left', parent=styles['Normal'], fontSize=8, alignment=TA_LEFT, fontName='Helvetica', leading=10)
    style_left_bold = ParagraphStyle('LeftBold', parent=style_left, fontName='Helvetica-Bold')
    style_right = ParagraphStyle('Right', parent=styles['Normal'], fontSize=8, alignment=TA_RIGHT, fontName='Helvetica')
    style_small = ParagraphStyle('Small', parent=style_left, fontSize=7)
    style_title = ParagraphStyle('Title', parent=style_center, fontSize=12, fontName='Helvetica-Bold', spaceAfter=2)

    # 1. CREDIT NOTE Title
    elements.append(Paragraph("<b><u>Credit Note</u></b>", style_title))
    elements.append(Spacer(1, 1*mm))

    # 2. COMPANY HEADER BOX (Logo Left, Text Center)
    logo = None
    if company.stamp:
        try:
            if os.path.exists(company.stamp.path):
                logo = Image(company.stamp.path, width=25*mm, height=25*mm)
        except: pass

    company_info = [
        Paragraph(f"<b>{company.name.upper()}</b>", style_center_bold),
        Spacer(1, 2*mm),
        Paragraph(f"{company.address.upper() if company.address else ''}", style_center),
        Paragraph(f"Phone: {company.phone or ''} &nbsp;&nbsp;&nbsp;&nbsp; Email: {company.email or ''}", style_center),
        Paragraph(f"GSTIN: {company.gstin or ''} &nbsp;&nbsp;&nbsp;&nbsp; State: {company.state_code or ''}", style_center),
    ]

    header_table = Table([[logo, company_info]], colWidths=[35*mm, 155*mm])
    header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)

    # 3. TO / NOTE DETAILS SPLIT
    to_text = [
        Paragraph("<b>To:</b>", style_left),
        Paragraph(f"<b>{credit_note.bill_to_name or client.name}</b>", style_left_bold),
        Paragraph(f"{(credit_note.bill_to_address or client.address or '').replace('\n', '<br/>')}", style_left),
        Paragraph(f"Contact No: {client.phone or ''} &nbsp;&nbsp; GSTIN: {credit_note.bill_to_gstin or client.gstin or ''}", style_left),
    ]
    
    note_details = [
        Paragraph("<b>Details:</b>", style_left),
        Paragraph(f"Note No: <b>{credit_note.credit_note_number}</b>", style_left),
        Paragraph(f"Date: <b>{credit_note.date.strftime('%d/%m/%Y')}</b>", style_left),
    ]
    if credit_note.invoice_reference:
        note_details.append(Paragraph(f"Ref Inv No: <b>{credit_note.invoice_reference.invoice_number}</b>", style_left))
        note_details.append(Paragraph(f"Inv Date: <b>{credit_note.invoice_reference.invoice_date.strftime('%d/%m/%Y')}</b>", style_left))

    details_table = Table([[to_text, note_details]], colWidths=[110*mm, 80*mm])
    details_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('LINEBEFORE', (1, 0), (1, 0), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(details_table)

    # 4. ITEMS TABLE
    items_header = ["#", "Item name", "HSN/ SAC", "Quantity", "Unit", "Rate(\u20B9)", "GST(\u20B9)", "Amount(\u20B9)"]
    items_data = [items_header]
    
    total_qty = 0
    total_tax_calc = Decimal('0.00')
    hsn_summary = {}

    for idx, item in enumerate(items, 1):
        tax_rate = credit_note.igst_rate if credit_note.is_igst else (credit_note.cgst_rate + credit_note.sgst_rate)
        tax_amt = (item.total * tax_rate / 100).quantize(Decimal('0.01'))
        row_total = item.total + tax_amt
        total_qty += item.quantity
        total_tax_calc += tax_amt
        
        # Track for HSN summary
        hsn = item.sac_code or "N/A"
        if hsn not in hsn_summary:
            hsn_summary[hsn] = {'taxable': Decimal('0.00'), 'tax': Decimal('0.00'), 'rate': tax_rate}
        hsn_summary[hsn]['taxable'] += item.total
        hsn_summary[hsn]['tax'] += tax_amt

        items_data.append([
            idx,
            Paragraph(item.description, style_left),
            item.sac_code or "",
            f"{item.quantity:.0f}",
            "Pcs",
            f"{item.rate:,.2f}",
            f"{tax_amt:,.2f}",
            f"{row_total:,.2f}"
        ])

    for _ in range(max(0, 5 - len(items))):
        items_data.append(["", "", "", "", "", "", "", ""])

    items_data.append(["Total", "", "", f"{total_qty:.0f}", "", "", f"{total_tax_calc:,.2f}", f"{credit_note.total:,.2f}"])

    col_widths = [10*mm, 70*mm, 20*mm, 15*mm, 15*mm, 20*mm, 20*mm, 20*mm]
    items_table = Table(items_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(items_table)

    # 5. HSN Summary & TOTALS SECTION
    hsn_headers = ["HSN/ SAC", "Taxable amt(\u20B9)", "CGST (Amt)", "SGST (Amt)", "Total Tax(\u20B9)"]
    hsn_data = [hsn_headers]
    for hsn, vals in hsn_summary.items():
        cgst_tax = (vals['tax'] / 2) if not credit_note.is_igst else 0
        sgst_tax = (vals['tax'] / 2) if not credit_note.is_igst else 0
        if credit_note.is_igst:
            hsn_data.append([hsn, f"{vals['taxable']:,.2f}", "-", "-", f"{vals['tax']:,.2f}"])
        else:
            hsn_data.append([hsn, f"{vals['taxable']:,.2f}", f"{cgst_tax:,.2f}", f"{sgst_tax:,.2f}", f"{vals['tax']:,.2f}"])
    
    hsn_table = Table(hsn_data, colWidths=[25*mm, 30*mm, 25*mm, 25*mm, 25*mm])
    hsn_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
    ]))

    totals_data = [
        ["Sub Total", ":", f"{credit_note.subtotal:,.2f}"],
        ["Total Tax", ":", f"{total_tax_calc:,.2f}"],
        ["Total Amount", ":", f"{credit_note.total:,.2f}"],
        [Paragraph(f"<b>In Words:</b><br/>{credit_note.get_amount_in_words().upper()}", style_small), "", ""],
    ]
    totals_table = Table(totals_data, colWidths=[30*mm, 5*mm, 25*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Bold'),
        ('SPAN', (0, 3), (2, 3)),
        ('LINEBELOW', (0, 2), (-1, 2), 0.5, border_color),
    ]))

    summary_split = Table([[hsn_table, totals_table]], colWidths=[130*mm, 60*mm])
    summary_split.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(summary_split)

    # 6. SIGNATURE
    elements.append(Spacer(1, 5*mm))
    sig_info = [
        Paragraph(f"For <b>{company.name.upper()}</b>:", style_right),
        Spacer(1, 15*mm),
        Paragraph("________________________", style_right),
        Paragraph("Authorized Signatory&nbsp;&nbsp;&nbsp;&nbsp;", style_right),
    ]
    elements.extend(sig_info)

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CreditNote_{credit_note.credit_note_number}.pdf"'
    return response
