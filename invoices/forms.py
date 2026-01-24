from django import forms
from django.forms import inlineformset_factory
from .models import (
    PurchaseOrder, POLineItem, Invoice, InvoiceItem, Client, Product, Company, CompanySettings, UOM
)
from decimal import Decimal


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['company', 'po_number', 'main_line_number', 'main_line_description']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'po_number': forms.TextInput(attrs={'class': 'form-control'}),
            'main_line_number': forms.TextInput(attrs={'class': 'form-control'}),
            'main_line_description': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Filter companies for current user
            self.fields['company'].queryset = Company.objects.filter(user=user, is_active=True)
            # Set default company
            default_company = Company.get_default(user)
            if default_company:
                self.fields['company'].initial = default_company
            self.fields['company'].required = True


class POLineItemForm(forms.ModelForm):
    class Meta:
        model = POLineItem
        fields = ['subline_number', 'subline_description', 'quantity', 'price', 'uom']
        widgets = {
            'subline_number': forms.TextInput(attrs={'class': 'form-control'}),
            'subline_description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control qty', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-control price', 'step': '0.01'}),
            'uom': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active UOMs
        self.fields['uom'].queryset = UOM.objects.filter(is_active=True).order_by('name')


POLineItemFormSet = inlineformset_factory(
    PurchaseOrder, POLineItem,
    form=POLineItemForm,
    extra=1,
    can_delete=True
)


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'company', 'client', 'po_reference', 'po_number', 'po_date', 'vendor_code',
                  'invoice_date', 'due_date', 'status', 'tax_rate', 'cgst_rate', 'sgst_rate', 
                  'discount', 'place_of_supply', 'state_code', 'reverse_charge', 'notes',
                  'measurement_sheet', 'bill_summary']
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'po_reference': forms.Select(attrs={'class': 'form-control'}),
            'po_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PO Number from client'}),
            'po_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vendor_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vendor Code'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
            'cgst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sgst_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'place_of_supply': forms.TextInput(attrs={'class': 'form-control'}),
            'state_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 24 for Gujarat'}),
            'reverse_charge': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'measurement_sheet': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'bill_summary': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Filter companies for current user
            self.fields['company'].queryset = Company.objects.filter(user=user, is_active=True)
            # Set default company
            default_company = Company.get_default(user)
            if default_company:
                self.fields['company'].initial = default_company
                # Auto-generate invoice number for new invoices
                if not self.instance.pk:
                    self.fields['invoice_number'].initial = default_company.get_next_invoice_number()
                    self.fields['invoice_number'].widget.attrs['readonly'] = True
                    self.fields['invoice_number'].help_text = 'Auto-generated from company prefix'
            
            # Filter PO reference by company
            if self.instance and self.instance.pk and self.instance.company:
                # Editing existing invoice - filter by invoice's company
                self.fields['po_reference'].queryset = PurchaseOrder.objects.filter(
                    company=self.instance.company
                ).order_by('-created_at')
            elif default_company:
                # New invoice with default company - show POs for default company
                self.fields['po_reference'].queryset = PurchaseOrder.objects.filter(
                    company=default_company
                ).order_by('-created_at')
            else:
                # New invoice without default company - start with empty queryset
                self.fields['po_reference'].queryset = PurchaseOrder.objects.none()


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['po_line_item', 'description', 'sac_code', 'quantity', 'rate']
        widgets = {
            'po_line_item': forms.Select(attrs={'class': 'form-control po-line-item-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'sac_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SAC Code (e.g., 998871)'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control qty', 'step': '0.01'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control rate', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)
        
        # Filter PO line items based on invoice's PO reference
        if invoice and invoice.po_reference:
            self.fields['po_line_item'].queryset = POLineItem.objects.filter(
                purchase_order=invoice.po_reference
            ).order_by('subline_number')
            self.fields['po_line_item'].required = False
        else:
            self.fields['po_line_item'].queryset = POLineItem.objects.none()
            self.fields['po_line_item'].required = False
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        po_line_item = self.cleaned_data.get('po_line_item')
        
        if po_line_item and quantity:
            # Get the invoice instance from formset
            invoice = getattr(self, '_invoice', None)
            available_qty = po_line_item.get_available_quantity(exclude_invoice=invoice)
            
            if quantity > available_qty:
                raise forms.ValidationError(
                    f'Quantity ({quantity}) exceeds available PO quantity ({available_qty}). '
                    f'PO has {po_line_item.quantity} total, {po_line_item.get_invoiced_quantity(exclude_invoice=invoice)} already invoiced.'
                )
        
        return quantity


InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True
)


def get_invoice_item_formset(invoice=None, po_reference=None):
    """Get InvoiceItemFormSet with invoice context"""
    class InvoiceItemFormSetBase(inlineformset_factory(
        Invoice, InvoiceItem,
        form=InvoiceItemForm,
        extra=1,
        can_delete=True
    )):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Determine PO reference - use invoice's PO reference or provided po_reference
            po_ref = invoice.po_reference if invoice else po_reference
            
            # Pass invoice to forms
            if invoice:
                for form in self.forms:
                    form._invoice = invoice
                    # Update PO line item queryset based on invoice's PO reference
                    if invoice.po_reference:
                        form.fields['po_line_item'].queryset = POLineItem.objects.filter(
                            purchase_order=invoice.po_reference
                        ).order_by('subline_number')
            elif po_ref:
                # For new invoices, use the provided PO reference
                for form in self.forms:
                    form.fields['po_line_item'].queryset = POLineItem.objects.filter(
                        purchase_order=po_ref
                    ).order_by('subline_number')
    
    return InvoiceItemFormSetBase


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'unit_price', 'tax_rate', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'gstin', 'pan', 'cin', 'address', 'email', 'phone',
                  'invoice_prefix', 'default_due_days', 'default_tax_rate', 'currency',
                  'bank_name', 'account_number', 'ifsc_code', 'branch', 'stamp', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'gstin': forms.TextInput(attrs={'class': 'form-control'}),
            'pan': forms.TextInput(attrs={'class': 'form-control'}),
            'cin': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_prefix': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'default_due_days': forms.NumberInput(attrs={'class': 'form-control', 'required': True}),
            'default_tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True}),
            'currency': forms.Select(attrs={'class': 'form-control', 'required': True}, choices=[
                ('₹ INR', '₹ INR (Indian Rupee)'),
                ('$ USD', '$ USD (US Dollar)'),
                ('€ EUR', '€ EUR (Euro)'),
            ]),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.TextInput(attrs={'class': 'form-control'}),
            'stamp': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = ['company_name', 'gstin', 'pan', 'address', 'email', 'phone',
                  'invoice_prefix', 'default_due_days', 'default_tax_rate', 'currency',
                  'bank_name', 'account_number', 'ifsc_code', 'branch']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gstin': forms.TextInput(attrs={'class': 'form-control'}),
            'pan': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_prefix': forms.TextInput(attrs={'class': 'form-control'}),
            'default_due_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'default_tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('₹ INR', '₹ INR (Indian Rupee)'),
                ('$ USD', '$ USD (US Dollar)'),
                ('€ EUR', '€ EUR (Euro)'),
            ]),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UOMForm(forms.ModelForm):
    class Meta:
        model = UOM
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
