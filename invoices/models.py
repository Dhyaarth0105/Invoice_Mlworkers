from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()


class Client(models.Model):
    """Client/Customer model"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clients'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_avatar_initials(self):
        """Get initials for avatar"""
        words = self.name.split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        return self.name[:2].upper() if len(self.name) >= 2 else self.name[0].upper()


class Product(models.Model):
    """Product/Service model"""
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'), validators=[MinValueValidator(Decimal('0'))])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UOM(models.Model):
    """Unit of Measurement Master"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'uom'
        verbose_name = 'Unit of Measurement'
        verbose_name_plural = 'Units of Measurement'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    """Purchase Order model with Main Line"""
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='purchase_orders', null=True, blank=True)
    po_number = models.CharField(max_length=100)
    main_line_number = models.CharField(max_length=50)
    main_line_description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-created_at']
        unique_together = [['company', 'po_number']]
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['company', 'po_number']),
        ]
    
    def __str__(self):
        return f"{self.po_number} - {self.main_line_description}"
    
    def get_total(self):
        """Calculate total from all subline items"""
        return sum(item.get_total() for item in self.subline_items.all())


class POLineItem(models.Model):
    """Purchase Order Subline Items"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='subline_items')
    subline_number = models.CharField(max_length=50)
    subline_description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))], default=Decimal('0.00'))
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT, related_name='po_line_items')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'po_line_items'
        ordering = ['subline_number', 'id']
    
    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.subline_description} ({self.subline_number})"
    
    def get_total(self):
        """Calculate total: quantity * price"""
        return self.quantity * self.price
    
    def get_invoiced_quantity(self, exclude_invoice=None):
        """Get total quantity already invoiced for this PO line item"""
        from .models import InvoiceItem
        queryset = InvoiceItem.objects.filter(po_line_item=self)
        if exclude_invoice:
            queryset = queryset.exclude(invoice=exclude_invoice)
        return sum(item.quantity for item in queryset)
    
    def get_available_quantity(self, exclude_invoice=None):
        """Get available quantity that can still be invoiced"""
        invoiced = self.get_invoiced_quantity(exclude_invoice=exclude_invoice)
        return self.quantity - invoiced


class Invoice(models.Model):
    """Invoice model"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]
    
    invoice_number = models.CharField(max_length=100, unique=True)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='invoices', null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    po_reference = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    po_number = models.CharField(max_length=100, blank=True, null=True, help_text="PO Number from client")
    po_date = models.DateField(blank=True, null=True, help_text="PO Date")
    vendor_code = models.CharField(max_length=50, blank=True, null=True, help_text="Vendor Code assigned by client")
    
    invoice_date = models.DateField()
    due_date = models.DateField()
    
    # Tax details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'))
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('9.00'), help_text="CGST Rate (%)")
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('9.00'), help_text="SGST Rate (%)")
    cgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    sgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Place of supply
    place_of_supply = models.CharField(max_length=200, blank=True, null=True)
    state_code = models.CharField(max_length=2, blank=True, null=True, help_text="State Code (e.g., 24 for Gujarat)")
    
    # Reverse charge
    reverse_charge = models.BooleanField(default=False)
    reverse_charge_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, null=True)
    
    # Document uploads
    measurement_sheet = models.FileField(upload_to='invoices/measurement_sheets/', blank=True, null=True, help_text="Measurement Sheet PDF")
    bill_summary = models.FileField(upload_to='invoices/bill_summaries/', blank=True, null=True, help_text="Bill Summary PDF")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    reminder_sent_at = models.DateTimeField(null=True, blank=True, help_text="When the last reminder email was sent")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['invoice_date']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.client.name}"
    
    def calculate_totals(self):
        """Calculate invoice totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.total for item in items)
        
        # Calculate CGST and SGST (split tax)
        taxable_amount = self.subtotal - self.discount
        self.cgst_amount = (taxable_amount * self.cgst_rate) / 100
        self.sgst_amount = (taxable_amount * self.sgst_rate) / 100
        self.tax_amount = self.cgst_amount + self.sgst_amount
        
        self.total = taxable_amount + self.tax_amount
        self.save()
    
    def get_amount_in_words(self):
        """Convert total amount to words"""
        try:
            from num2words import num2words
            amount = float(self.total)
            words = num2words(amount, lang='en_IN', to='currency', currency='INR')
            return words.replace('euro', 'rupees').replace('cents', 'paisa').title()
        except (ImportError, Exception):
            # Fallback if num2words not installed or error
            return f"Rupees {self.total:,.2f} Only"
    
    def get_status_class(self):
        """Get CSS class for status badge"""
        status_classes = {
            'PAID': 'paid',
            'PENDING': 'pending',
            'OVERDUE': 'overdue',
            'DRAFT': 'draft',
        }
        return status_classes.get(self.status, 'pending')
    
    def get_total_paid(self):
        """Get total amount paid (excluding on-hold payments)"""
        from .models import Payment
        return sum(
            p.net_amount for p in Payment.objects.filter(
                invoice=self, 
                status='RECEIVED', 
                is_on_hold=False
            )
        )
    
    def get_total_on_hold(self):
        """Get total amount on hold"""
        return sum(
            p.net_amount for p in self.payments.filter(
                is_on_hold=True
            )
        )
    
    def get_outstanding_amount(self):
        """Get outstanding amount"""
        return self.total - self.get_total_paid()
    
    def get_payment_status(self):
        """Get payment status based on payments"""
        paid = self.get_total_paid()
        if paid == 0:
            return 'UNPAID'
        elif paid >= self.total:
            return 'PAID'
        elif paid > 0:
            return 'PARTIAL'
        return 'UNPAID'
    
    def update_status_from_payments(self):
        """Update invoice status based on payment status"""
        payment_status = self.get_payment_status()
        if payment_status == 'PAID' and self.status != 'PAID':
            self.status = 'PAID'
            self.save(update_fields=['status'])
        elif payment_status == 'PARTIAL' and self.status == 'PAID':
            # Don't downgrade from PAID to PARTIAL automatically
            pass
        elif payment_status == 'UNPAID' and self.status == 'PAID':
            # Don't downgrade from PAID to UNPAID automatically
            pass


class InvoiceItem(models.Model):
    """Invoice line items"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    po_line_item = models.ForeignKey(POLineItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_items', help_text="Linked PO Line Item")
    description = models.CharField(max_length=500)
    sac_code = models.CharField(max_length=10, blank=True, null=True, help_text="Service Accounting Code (SAC)")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    rate = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'invoice_items'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        """Calculate total before saving"""
        self.total = self.quantity * self.rate
        super().save(*args, **kwargs)
        # Recalculate invoice totals
        if self.invoice:
            self.invoice.calculate_totals()


class Company(models.Model):
    """Multiple companies per user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies')
    name = models.CharField(max_length=200)
    gstin = models.CharField(max_length=15, blank=True, null=True)
    pan = models.CharField(max_length=10, blank=True, null=True)
    cin = models.CharField(max_length=21, blank=True, null=True, help_text="Company Identification Number")
    address = models.TextField()
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Invoice settings
    invoice_prefix = models.CharField(max_length=20, default='INV-')
    default_due_days = models.IntegerField(default=30)
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'))
    currency = models.CharField(max_length=10, default='₹ INR')
    
    # Bank details
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    branch = models.CharField(max_length=200, blank=True, null=True)
    
    # Company Stamp/Logo
    stamp = models.ImageField(upload_to='company_stamps/', blank=True, null=True, help_text="Company stamp/logo for invoices")
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default company for new invoices")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Ensure only one default company per user"""
        if self.is_default:
            Company.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_default(cls, user):
        """Get default company for user"""
        company = cls.objects.filter(user=user, is_default=True).first()
        if not company:
            company = cls.objects.filter(user=user, is_active=True).first()
        return company
    
    def get_next_invoice_number(self):
        """Generate next sequential invoice number for this company"""
        from datetime import datetime
        from .models import Invoice
        
        current_year = datetime.now().year
        prefix = self.invoice_prefix or 'INV-'
        
        # Find the highest invoice number for this company in current year
        # Format: PREFIX-YYYY-XXX (e.g., INV-2024-001, NRK-INV-2024-002)
        pattern = f"{prefix}{current_year}-"
        
        # Get all invoices for this company that match the pattern
        existing_invoices = Invoice.objects.filter(
            company=self,
            invoice_number__startswith=pattern
        ).order_by('-invoice_number')
        
        if existing_invoices.exists():
            # Extract the number part and increment
            last_number = 0
            for invoice in existing_invoices:
                try:
                    # Extract number after year (e.g., "001" from "INV-2024-001")
                    number_part = invoice.invoice_number.split('-')[-1]
                    last_number = int(number_part)
                    break
                except (ValueError, IndexError):
                    continue
            
            next_number = last_number + 1
        else:
            # First invoice for this company this year
            next_number = 1
        
        # Format with leading zeros (e.g., 001, 002, 010, 100)
        return f"{prefix}{current_year}-{next_number:03d}"


class Payment(models.Model):
    """Payment tracking for invoices"""
    PAYMENT_STATUS_CHOICES = [
        ('RECEIVED', 'Received'),
        ('ON_HOLD', 'On Hold'),
        ('PENDING', 'Pending'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('NEFT', 'NEFT'),
        ('RTGS', 'RTGS'),
        ('OTHER', 'Other'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))], help_text="Amount received")
    
    # Adjustments
    tds_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0'))], help_text="TDS Deducted")
    tds_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0'))], help_text="TDS %")
    fine_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0'))], help_text="Fine/Penalty")
    adjustment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Other Adjustments (+/-)")
    
    # Net amount received
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Net amount after adjustments")
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='BANK_TRANSFER')
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="Cheque/Transaction/Reference Number")
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='RECEIVED')
    is_on_hold = models.BooleanField(default=False, help_text="Payment on hold")
    hold_reason = models.TextField(blank=True, null=True, help_text="Reason for hold")
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def save(self, *args, **kwargs):
        # Calculate net amount: amount - TDS - fine + adjustment
        self.net_amount = self.amount - self.tds_amount - self.fine_amount + self.adjustment_amount
        
        # Auto-set is_on_hold based on status
        if self.status == 'ON_HOLD':
            self.is_on_hold = True
        elif self.status == 'RECEIVED':
            self.is_on_hold = False
        
        super().save(*args, **kwargs)
        
        # Update invoice status after payment is saved
        if self.invoice:
            self.invoice.update_status_from_payments()
    
    def delete(self, *args, **kwargs):
        invoice = self.invoice
        super().delete(*args, **kwargs)
        # Update invoice status after payment is deleted
        if invoice:
            invoice.update_status_from_payments()
    
    def __str__(self):
        return f"Payment of ₹{self.net_amount:,.2f} for {self.invoice.invoice_number} on {self.payment_date}"
    
    def get_status_badge_class(self):
        """Get CSS class for status badge"""
        status_classes = {
            'RECEIVED': 'paid',
            'ON_HOLD': 'pending',
            'PENDING': 'pending',
            'CANCELLED': 'overdue',
        }
        return status_classes.get(self.status, 'pending')


class CompanySettings(models.Model):
    """Legacy company settings - kept for backward compatibility"""
    company_name = models.CharField(max_length=200, default='ABC Technologies Pvt. Ltd.')
    gstin = models.CharField(max_length=15, blank=True, null=True)
    pan = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Invoice settings
    invoice_prefix = models.CharField(max_length=20, default='INV-')
    default_due_days = models.IntegerField(default=30)
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'))
    currency = models.CharField(max_length=10, default='₹ INR')
    
    # Bank details
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    branch = models.CharField(max_length=200, blank=True, null=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'company_settings'
        verbose_name = 'Company Settings'
        verbose_name_plural = 'Company Settings'
    
    def __str__(self):
        return self.company_name
    
    def save(self, *args, **kwargs):
        """Ensure only one settings record exists"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create company settings"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
