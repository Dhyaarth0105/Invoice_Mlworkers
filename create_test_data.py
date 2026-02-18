"""
Create test data based on the NRKEN invoice sample
"""
import os
import django
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoice_project.settings')
django.setup()

from accounts.models import User
from invoices.models import Company, Client, Invoice, InvoiceItem, UOM, PurchaseOrder, POLineItem

# Get admin user
admin = User.objects.get(username='admin')

print("Creating test data based on NRKEN invoice...")

# 1. Create Company - NRKEN PRIVATE LIMITED
company, created = Company.objects.get_or_create(
    user=admin,
    name='NRKEN PRIVATE LIMITED',
    defaults={
        'address': 'G-10, MAHALAXMI SHOPPING, UMARA, OLPAD, SURAT - 394130',
        'gstin': '24AAJCN3315P1Z7',
        'pan': 'AAJCN3315P',
        'cin': 'U71100GJ2023PTC147359',
        'email': 'nrkenpvtltd@gmail.com',
        'phone': '+91 6354397377',
        'invoice_prefix': 'NRKEN/',
        'default_due_days': 30,
        'default_tax_rate': Decimal('18.00'),
        'is_default': True,
    }
)
if created:
    print(f"  [+] Company created: {company.name}")
else:
    print(f"  [=] Company exists: {company.name}")

# 2. Create Client - L&T MHI POWER BOILERS PVT LTD
client, created = Client.objects.get_or_create(
    name='M/S L&T MHI POWER BOILERS PVT LTD',
    defaults={
        'email': 'accounts@ltmhi.com',
        'phone': '+91 261 6693000',
        'gstin': '24AABCL2635C1Z3',  # GSTIN from address
        'address': '''(Formerly known as L&T- MHPS Boilers Private Limited)
Gate no: 6,
Hazira Manufacturing Complex (West),
Surat-Hazira Road.
P.O.- Bhatha Surat, Gujarat - 394510
GSTIN: 24AABCL2635C1Z3
PAN: AABCL2635C''',
    }
)
if created:
    print(f"  [+] Client created: {client.name}")
else:
    print(f"  [=] Client exists: {client.name}")

# 3. Get or create UOM for NOS (Numbers)
uom, created = UOM.objects.get_or_create(
    name='NOS',
    defaults={
        'code': 'NOS',
        'description': 'Numbers/Units',
        'is_active': True,
    }
)
if created:
    print(f"  [+] UOM created: {uom.name}")
else:
    print(f"  [=] UOM exists: {uom.name}")

# 4. Create Purchase Order - LMB/H62/21001-84251
po, created = PurchaseOrder.objects.get_or_create(
    company=company,
    po_number='LMB/H62/21001-84251',
    defaults={
        'main_line_number': '1',
        'main_line_description': 'HYDRO PLUG FITUP & WELDING - GMAW Services',
    }
)
if created:
    print(f"  [+] Purchase Order created: {po.po_number}")
    
    # Create PO Line Items
    po_item1 = POLineItem.objects.create(
        purchase_order=po,
        subline_number='1.1',
        subline_description='HYDRO PLUG FITUP & WELDING - GMAW',
        quantity=Decimal('768.00'),
        price=Decimal('32.99'),
        uom=uom,
    )
    print(f"    [+] PO Line 1: {po_item1.subline_description} - Qty: {po_item1.quantity}")
    
    po_item2 = POLineItem.objects.create(
        purchase_order=po,
        subline_number='1.2',
        subline_description='HYDRO PLUG FITUP & WELDING - GMAW',
        quantity=Decimal('5756.00'),
        price=Decimal('32.99'),
        uom=uom,
    )
    print(f"    [+] PO Line 2: {po_item2.subline_description} - Qty: {po_item2.quantity}")
else:
    print(f"  [=] Purchase Order exists: {po.po_number}")
    po_item1 = po.subline_items.first()
    po_item2 = po.subline_items.last()

# 5. Create or Update Invoice linked to PO
invoice, created = Invoice.objects.get_or_create(
    invoice_number='NRKEN/2526/131',
    defaults={
        'company': company,
        'client': client,
        'po_reference': po,  # Link to PO
        'invoice_date': date(2025, 12, 29),
        'due_date': date(2026, 1, 28),
        'po_number': 'LMB/H62/21001-84251',
        'po_date': date(2025, 10, 9),
        'vendor_code': '504777',
        'place_of_supply': 'Hazira (Gujarat)',
        'state_code': '24',
        'cgst_rate': Decimal('9.00'),
        'sgst_rate': Decimal('9.00'),
        'tax_rate': Decimal('18.00'),
        'reverse_charge': False,
        'status': 'PENDING',
        'created_by': admin,
    }
)

if created:
    print(f"  [+] Invoice created: {invoice.invoice_number}")
    
    # Create Invoice Items linked to PO Line Items
    item1 = InvoiceItem.objects.create(
        invoice=invoice,
        po_line_item=po_item1,  # Link to PO Line
        description='HYDRO PLUG FITUP & WELDING - GMAW',
        sac_code='998871',
        quantity=Decimal('768.00'),
        rate=Decimal('32.99'),
    )
    print(f"    [+] Item 1: {item1.description} - Qty: {item1.quantity}, Amount: {item1.total}")
    
    item2 = InvoiceItem.objects.create(
        invoice=invoice,
        po_line_item=po_item2,  # Link to PO Line
        description='HYDRO PLUG FITUP & WELDING - GMAW',
        sac_code='998871',
        quantity=Decimal('5756.00'),
        rate=Decimal('32.99'),
    )
    print(f"    [+] Item 2: {item2.description} - Qty: {item2.quantity}, Amount: {item2.total}")
    
    # Recalculate totals
    invoice.calculate_totals()
    print(f"\n  Invoice Totals:")
    print(f"    Sub Total: Rs. {invoice.subtotal:,.2f}")
    print(f"    CGST (9%): Rs. {invoice.cgst_amount:,.2f}")
    print(f"    SGST (9%): Rs. {invoice.sgst_amount:,.2f}")
    print(f"    Total:     Rs. {invoice.total:,.2f}")
else:
    # Update existing invoice to link PO
    if not invoice.po_reference:
        invoice.po_reference = po
        invoice.save()
        print(f"  [=] Invoice updated with PO reference: {invoice.invoice_number}")
    else:
        print(f"  [=] Invoice exists: {invoice.invoice_number}")
    print(f"    Sub Total: Rs. {invoice.subtotal:,.2f}")
    print(f"    Total:     Rs. {invoice.total:,.2f}")

print("\n" + "="*50)
print("Test data creation complete!")
print("="*50)
print(f"\nData created:")
print(f"  - Company: {company.name}")
print(f"  - Client: {client.name}")
print(f"  - Purchase Order: {po.po_number}")
print(f"  - Invoice: {invoice.invoice_number} (linked to PO)")
print(f"\nLogin at: http://127.0.0.1:8000")
print(f"  Username: admin")
print(f"  Password: admin123")
