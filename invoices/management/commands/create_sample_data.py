"""
Management command to create sample data for testing
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from invoices.models import (
    Company, Client, UOM, PurchaseOrder, POLineItem, Invoice, InvoiceItem
)
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample PO and Invoice data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing admin user: {admin_user.username}'))
        
        # Get or create default company
        company, created = Company.objects.get_or_create(
            user=admin_user,
            name='NRKEN Private Limited',
            defaults={
                'gstin': '24AABCU9603R1ZX',
                'pan': 'AABCU9603R',
                'address': '123 Business Street, Ahmedabad, Gujarat - 380001',
                'email': 'info@nrken.com',
                'phone': '+91-79-12345678',
                'invoice_prefix': 'NRK',
                'default_due_days': 30,
                'default_tax_rate': Decimal('18.00'),
                'currency': '₹ INR',
                'is_default': True,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created company: {company.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing company: {company.name}'))
        
        # Get or create client
        client, created = Client.objects.get_or_create(
            name='ABC Corporation',
            defaults={
                'email': 'contact@abccorp.com',
                'phone': '+91-22-98765432',
                'address': '456 Corporate Avenue, Mumbai, Maharashtra - 400001',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created client: {client.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing client: {client.name}'))
        
        # Get or create UOMs - try by code first, then by name
        uom_pcs = UOM.objects.filter(code='PCS').first()
        if not uom_pcs:
            uom_pcs = UOM.objects.filter(name='Pieces').first()
        if not uom_pcs:
            uom_pcs = UOM.objects.create(code='PCS', name='Pieces', description='Pieces', is_active=True)
        
        uom_kg = UOM.objects.filter(code='KG').first()
        if not uom_kg:
            uom_kg = UOM.objects.filter(name='Kilograms').first()
        if not uom_kg:
            uom_kg = UOM.objects.create(code='KG', name='Kilograms', description='Kilograms', is_active=True)
        
        uom_hrs = UOM.objects.filter(code='HRS').first()
        if not uom_hrs:
            uom_hrs = UOM.objects.filter(name='Hours').first()
        if not uom_hrs:
            uom_hrs = UOM.objects.create(code='HRS', name='Hours', description='Hours', is_active=True)
        
        self.stdout.write(self.style.SUCCESS('Created/verified UOMs'))
        
        # Create Purchase Order
        po, created = PurchaseOrder.objects.get_or_create(
            po_number='PO-2024-001',
            defaults={
                'main_line_number': 'ML-001',
                'main_line_description': 'Software Development Services',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created PO: {po.po_number}'))
            
            # Create PO Line Items
            po_items = [
                {
                    'subline_number': 'SL-001',
                    'subline_description': 'Frontend Development - React Components',
                    'quantity': Decimal('100.00'),
                    'price': Decimal('1500.00'),
                    'uom': uom_hrs,
                },
                {
                    'subline_number': 'SL-002',
                    'subline_description': 'Backend Development - API Integration',
                    'quantity': Decimal('80.00'),
                    'price': Decimal('2000.00'),
                    'uom': uom_hrs,
                },
                {
                    'subline_number': 'SL-003',
                    'subline_description': 'Database Design & Optimization',
                    'quantity': Decimal('50.00'),
                    'price': Decimal('1800.00'),
                    'uom': uom_hrs,
                },
                {
                    'subline_number': 'SL-004',
                    'subline_description': 'Testing & QA Services',
                    'quantity': Decimal('40.00'),
                    'price': Decimal('1200.00'),
                    'uom': uom_hrs,
                },
            ]
            
            for item_data in po_items:
                POLineItem.objects.create(
                    purchase_order=po,
                    **item_data
                )
            
            self.stdout.write(self.style.SUCCESS(f'Created {len(po_items)} PO line items'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing PO: {po.po_number}'))
        
        # Create Invoice (partial - only some items from PO)
        invoice_number = f'{company.invoice_prefix}-INV-2024-001'
        invoice, created = Invoice.objects.get_or_create(
            invoice_number=invoice_number,
            defaults={
                'company': company,
                'client': client,
                'po_reference': po,
                'po_number': po.po_number,
                'po_date': date.today() - timedelta(days=30),
                'vendor_code': 'VEND-001',
                'invoice_date': date.today(),
                'due_date': date.today() + timedelta(days=30),
                'cgst_rate': Decimal('9.00'),
                'sgst_rate': Decimal('9.00'),
                'tax_rate': Decimal('18.00'),
                'place_of_supply': 'Gujarat',
                'state_code': '24',
                'reverse_charge': False,
                'status': 'PENDING',
                'created_by': admin_user,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Invoice: {invoice.invoice_number}'))
            
            # Get PO line items
            po_line_items = po.subline_items.all()
            
            # Create invoice items (partial quantities from PO)
            invoice_items_data = [
                {
                    'po_line_item': po_line_items[0],  # Frontend Development
                    'description': 'Frontend Development - React Components',
                    'sac_code': '998314',
                    'quantity': Decimal('60.00'),  # Less than PO quantity (100)
                    'rate': Decimal('1500.00'),
                },
                {
                    'po_line_item': po_line_items[1],  # Backend Development
                    'description': 'Backend Development - API Integration',
                    'sac_code': '998314',
                    'quantity': Decimal('50.00'),  # Less than PO quantity (80)
                    'rate': Decimal('2000.00'),
                },
            ]
            
            for item_data in invoice_items_data:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    **item_data
                )
            
            invoice.calculate_totals()
            self.stdout.write(self.style.SUCCESS(f'Created {len(invoice_items_data)} invoice items'))
            self.stdout.write(self.style.SUCCESS(f'Invoice Total: INR {invoice.total}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing Invoice: {invoice.invoice_number}'))
        
        self.stdout.write(self.style.SUCCESS('\nSample data created successfully!'))
        self.stdout.write(self.style.SUCCESS(f'\nLogin credentials:'))
        self.stdout.write(self.style.SUCCESS(f'  Username: admin'))
        self.stdout.write(self.style.SUCCESS(f'  Password: admin123'))
        self.stdout.write(self.style.SUCCESS(f'\nPO Number: {po.po_number}'))
        self.stdout.write(self.style.SUCCESS(f'Invoice Number: {invoice.invoice_number}'))

