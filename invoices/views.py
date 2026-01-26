from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import date, timedelta
from decimal import Decimal
import json
from .models import (
    Client, Product, PurchaseOrder, POLineItem, Invoice, InvoiceItem, Company, CompanySettings, UOM, Payment
)
from .forms import (
    PurchaseOrderForm, POLineItemFormSet, InvoiceForm, InvoiceItemFormSet,
    get_invoice_item_formset, ClientForm, ProductForm, CompanyForm, CompanySettingsForm, UOMForm, PaymentForm
)


@login_required
def dashboard(request):
    """Dashboard view with statistics"""
    # Get statistics
    total_invoices = Invoice.objects.count()
    paid_invoices = Invoice.objects.filter(status='PAID')
    pending_invoices = Invoice.objects.filter(status='PENDING')
    overdue_invoices = Invoice.objects.filter(status='OVERDUE')
    draft_invoices = Invoice.objects.filter(status='DRAFT')
    
    paid_amount = paid_invoices.aggregate(total=Sum('total'))['total'] or Decimal('0')
    pending_amount = pending_invoices.aggregate(total=Sum('total'))['total'] or Decimal('0')
    overdue_amount = overdue_invoices.aggregate(total=Sum('total'))['total'] or Decimal('0')
    active_clients = Client.objects.filter(is_active=True).count()
    
    # Status breakdown for pie chart
    status_breakdown = {
        'PAID': paid_invoices.count(),
        'PENDING': pending_invoices.count(),
        'OVERDUE': overdue_invoices.count(),
        'DRAFT': draft_invoices.count(),
    }
    
    # Monthly revenue for last 6 months
    from datetime import datetime, timedelta
    monthly_revenue = []
    for i in range(5, -1, -1):
        month_start = (timezone.now() - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        revenue = Invoice.objects.filter(
            status='PAID',
            invoice_date__gte=month_start,
            invoice_date__lte=month_end
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(revenue)
        })
    
    # Recent invoices
    recent_invoices = Invoice.objects.select_related('client').order_by('-created_at')[:5]
    
    # Top clients
    top_clients = Client.objects.annotate(
        invoice_count=Count('invoices'),
        total_revenue=Sum('invoices__total')
    ).filter(is_active=True).order_by('-total_revenue')[:3]
    
    context = {
        'total_invoices': total_invoices,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
        'overdue_amount': overdue_amount,
        'active_clients': active_clients,
        'recent_invoices': recent_invoices,
        'top_clients': top_clients,
        'status_breakdown': status_breakdown,
        'monthly_revenue': monthly_revenue,
    }
    return render(request, 'invoices/dashboard.html', context)


@login_required
def uom_list(request):
    """List all UOMs"""
    uoms = UOM.objects.all().order_by('name')
    return render(request, 'invoices/uom_list.html', {'uoms': uoms})


@login_required
def create_uom(request):
    """Create new UOM"""
    if request.method == 'POST':
        form = UOMForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'UOM created successfully!')
            return redirect('invoices:uom_list')
    else:
        form = UOMForm()
    return render(request, 'invoices/uom_form.html', {'form': form, 'title': 'Add New UOM'})


@login_required
def edit_uom(request, pk):
    """Edit UOM"""
    uom = get_object_or_404(UOM, pk=pk)
    if request.method == 'POST':
        form = UOMForm(request.POST, instance=uom)
        if form.is_valid():
            form.save()
            messages.success(request, 'UOM updated successfully!')
            return redirect('invoices:uom_list')
    else:
        form = UOMForm(instance=uom)
    return render(request, 'invoices/uom_form.html', {'form': form, 'uom': uom, 'title': 'Edit UOM'})


@login_required
def delete_uom(request, pk):
    """Delete UOM"""
    uom = get_object_or_404(UOM, pk=pk)
    if request.method == 'POST':
        # Check if UOM is being used
        if uom.purchase_orders.exists():
            messages.error(request, f'Cannot delete UOM "{uom.name}" as it is being used in Purchase Orders.')
            return redirect('invoices:uom_list')
        uom.delete()
        messages.success(request, 'UOM deleted successfully!')
        return redirect('invoices:uom_list')
    return render(request, 'invoices/uom_confirm_delete.html', {'uom': uom})


@login_required
def manage_po(request):
    """Manage Purchase Orders"""
    # Get user's companies
    user_companies = Company.objects.filter(user=request.user, is_active=True)
    
    # Get company filter from request
    company_id = request.GET.get('company')
    
    # Filter POs by user's companies
    pos = PurchaseOrder.objects.filter(company__in=user_companies).prefetch_related('subline_items__uom', 'company').order_by('-created_at')
    
    # Apply company filter if selected
    if company_id:
        try:
            selected_company = Company.objects.get(pk=company_id, user=request.user, is_active=True)
            pos = pos.filter(company=selected_company)
        except Company.DoesNotExist:
            pass
    
    return render(request, 'invoices/manage_po.html', {
        'pos': pos,
        'companies': user_companies,
        'selected_company_id': company_id
    })


@login_required
def create_po(request):
    """Create new Purchase Order"""
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, user=request.user)
        formset = POLineItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            po = form.save()
            formset.instance = po
            formset.save()
            messages.success(request, 'Purchase Order created successfully!')
            return redirect('invoices:manage_po')
        else:
            # Debug: Print form errors
            if not form.is_valid():
                messages.error(request, f'Form errors: {form.errors}')
            if not formset.is_valid():
                messages.error(request, f'Formset errors: {formset.errors}')
    else:
        form = PurchaseOrderForm(user=request.user)
        formset = POLineItemFormSet()
    return render(request, 'invoices/po_form.html', {'form': form, 'formset': formset, 'title': 'Add New PO'})


@login_required
def edit_po(request, pk):
    """Edit Purchase Order"""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po, user=request.user)
        formset = POLineItemFormSet(request.POST, instance=po)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Purchase Order updated successfully!')
            return redirect('invoices:manage_po')
        else:
            # Debug: Print form errors
            if not form.is_valid():
                messages.error(request, f'Form errors: {form.errors}')
            if not formset.is_valid():
                messages.error(request, f'Formset errors: {formset.errors}')
    else:
        form = PurchaseOrderForm(instance=po, user=request.user)
        formset = POLineItemFormSet(instance=po)
    return render(request, 'invoices/po_form.html', {'form': form, 'formset': formset, 'po': po, 'title': 'Edit PO'})


@login_required
def delete_po(request, pk):
    """Delete Purchase Order"""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        po.delete()
        messages.success(request, 'Purchase Order deleted successfully!')
        return redirect('invoices:manage_po')
    return render(request, 'invoices/po_confirm_delete.html', {'po': po})


@login_required
def invoice_list(request):
    """List all invoices"""
    # Filter invoices by user's companies
    user_companies = Company.objects.filter(user=request.user, is_active=True)
    invoices = Invoice.objects.filter(company__in=user_companies).select_related('client', 'po_reference', 'company').order_by('-created_at')
    
    # Calculate total amount
    total_amount = invoices.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    total_count = invoices.count()
    
    # Calculate by status
    paid_amount = invoices.filter(status='PAID').aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    pending_amount = invoices.filter(status='PENDING').aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    draft_amount = invoices.filter(status='DRAFT').aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    overdue_amount = invoices.filter(status='OVERDUE').aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    
    return render(request, 'invoices/invoice_list.html', {
        'invoices': invoices,
        'total_amount': total_amount,
        'total_count': total_count,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
        'draft_amount': draft_amount,
        'overdue_amount': overdue_amount,
    })


@login_required
def create_invoice(request):
    """Create new invoice"""
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES, user=request.user)
        # Get PO reference from form data if available
        po_reference_id = request.POST.get('po_reference')
        po_reference = None
        if po_reference_id:
            try:
                po_reference = PurchaseOrder.objects.get(pk=po_reference_id)
            except PurchaseOrder.DoesNotExist:
                pass
        
        # Create formset with PO reference context
        InvoiceItemFormSetWithContext = get_invoice_item_formset(po_reference=po_reference)
        formset = InvoiceItemFormSetWithContext(request.POST)
        
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            
            # Auto-generate invoice number if not provided and company is selected
            if not invoice.invoice_number and invoice.company:
                invoice.invoice_number = invoice.company.get_next_invoice_number()
            elif not invoice.invoice_number:
                # Fallback if no company selected
                from datetime import datetime
                current_year = datetime.now().year
                # Get last invoice number globally
                last_invoice = Invoice.objects.filter(
                    invoice_number__startswith=f'INV-{current_year}-'
                ).order_by('-invoice_number').first()
                if last_invoice:
                    try:
                        number_part = last_invoice.invoice_number.split('-')[-1]
                        next_num = int(number_part) + 1
                    except (ValueError, IndexError):
                        next_num = 1
                else:
                    next_num = 1
                invoice.invoice_number = f'INV-{current_year}-{next_num:03d}'
            
            # Auto-calculate tax_rate from CGST + SGST
            invoice.tax_rate = invoice.cgst_rate + invoice.sgst_rate
            invoice.save()
            
            # Validate quantities against PO before saving items
            if invoice.po_reference:
                for form_item in formset:
                    if form_item.cleaned_data and not form_item.cleaned_data.get('DELETE', False):
                        po_line_item = form_item.cleaned_data.get('po_line_item')
                        quantity = form_item.cleaned_data.get('quantity', Decimal('0'))
                        
                        if po_line_item and quantity:
                            available_qty = po_line_item.get_available_quantity()
                            if quantity > available_qty:
                                messages.error(request, 
                                    f'Quantity ({quantity}) for "{po_line_item.subline_description}" exceeds available PO quantity ({available_qty}).')
                                return render(request, 'invoices/invoice_form.html', {
                                    'form': form, 
                                    'formset': formset, 
                                    'title': 'Create Invoice'
                                })
            
            formset.instance = invoice
            formset.save()
            invoice.calculate_totals()
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
            return redirect('invoices:invoice_list')
        else:
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            if not formset.is_valid():
                for form_item in formset:
                    if form_item.errors:
                        for field, errors in form_item.errors.items():
                            for error in errors:
                                messages.error(request, str(error))
            
            # Re-initialize formset with PO reference from POST data if available
            # This ensures PO line items are populated when re-rendering after validation errors
            po_reference_id = request.POST.get('po_reference')
            if po_reference_id:
                try:
                    po_ref = PurchaseOrder.objects.get(pk=po_reference_id)
                    InvoiceItemFormSetWithContext = get_invoice_item_formset(po_reference=po_ref)
                    formset = InvoiceItemFormSetWithContext(request.POST)
                except PurchaseOrder.DoesNotExist:
                    # If PO doesn't exist, re-initialize with empty formset
                    InvoiceItemFormSetWithContext = get_invoice_item_formset()
                    formset = InvoiceItemFormSetWithContext(request.POST)
            else:
                # If no PO reference, re-initialize formset to clear any stale data
                InvoiceItemFormSetWithContext = get_invoice_item_formset()
                formset = InvoiceItemFormSetWithContext(request.POST)
    else:
        form = InvoiceForm(user=request.user)
        # Check if there's a PO reference in GET parameters (for pre-selection)
        po_reference_id = request.GET.get('po_reference')
        po_reference = None
        if po_reference_id:
            try:
                po_reference = PurchaseOrder.objects.get(pk=po_reference_id)
                form.fields['po_reference'].initial = po_reference
            except PurchaseOrder.DoesNotExist:
                pass
        InvoiceItemFormSetWithContext = get_invoice_item_formset(po_reference=po_reference)
        formset = InvoiceItemFormSetWithContext()
    return render(request, 'invoices/invoice_form.html', {'form': form, 'formset': formset, 'title': 'Create Invoice'})


@login_required
def invoice_detail(request, pk):
    """View invoice details"""
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()
    company = invoice.company
    payments = invoice.payments.all().order_by('-payment_date', '-created_at')
    
    # Calculate payment totals
    total_paid = invoice.get_total_paid()
    total_on_hold = invoice.get_total_on_hold()
    outstanding = invoice.get_outstanding_amount()
    payment_status = invoice.get_payment_status()
    
    return render(request, 'invoices/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'company': company,
        'payments': payments,
        'total_paid': total_paid,
        'total_on_hold': total_on_hold,
        'outstanding': outstanding,
        'payment_status': payment_status,
    })


@login_required
def invoice_pdf(request, pk):
    """Generate PDF for invoice"""
    from .pdf_utils import generate_invoice_pdf
    
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()
    company = invoice.company
    client = invoice.client
    
    if not company:
        messages.error(request, 'Company not found for this invoice.')
        return redirect('invoices:invoice_detail', pk=pk)
    
    return generate_invoice_pdf(invoice, items, company, client)


@login_required
def edit_invoice(request, pk):
    """Edit invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES, instance=invoice, user=request.user)
        InvoiceItemFormSetWithContext = get_invoice_item_formset(invoice=invoice)
        formset = InvoiceItemFormSetWithContext(request.POST, instance=invoice)
        
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            # Auto-calculate tax_rate from CGST + SGST
            invoice.tax_rate = invoice.cgst_rate + invoice.sgst_rate
            invoice.save()
            
            # Validate quantities against PO before saving items
            if invoice.po_reference:
                for form_item in formset:
                    if form_item.cleaned_data and not form_item.cleaned_data.get('DELETE', False):
                        po_line_item = form_item.cleaned_data.get('po_line_item')
                        quantity = form_item.cleaned_data.get('quantity', Decimal('0'))
                        
                        if po_line_item and quantity:
                            available_qty = po_line_item.get_available_quantity(exclude_invoice=invoice)
                            if quantity > available_qty:
                                messages.error(request, 
                                    f'Quantity ({quantity}) for "{po_line_item.subline_description}" exceeds available PO quantity ({available_qty}).')
                                return render(request, 'invoices/invoice_form.html', {
                                    'form': form, 
                                    'formset': formset, 
                                    'invoice': invoice,
                                    'title': 'Edit Invoice'
                                })
            
            formset.save()
            invoice.calculate_totals()
            messages.success(request, 'Invoice updated successfully!')
            return redirect('invoices:invoice_list')
        else:
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            if not formset.is_valid():
                for form_item in formset:
                    if form_item.errors:
                        for field, errors in form_item.errors.items():
                            for error in errors:
                                messages.error(request, str(error))
    else:
        form = InvoiceForm(instance=invoice, user=request.user)
        InvoiceItemFormSetWithContext = get_invoice_item_formset(invoice=invoice)
        formset = InvoiceItemFormSetWithContext(instance=invoice)
    return render(request, 'invoices/invoice_form.html', {'form': form, 'formset': formset, 'invoice': invoice, 'title': 'Edit Invoice'})


@login_required
def delete_invoice(request, pk):
    """Delete invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted successfully!')
        return redirect('invoices:invoice_list')
    return render(request, 'invoices/invoice_confirm_delete.html', {'invoice': invoice})


@login_required
def client_list(request):
    """List all clients"""
    clients = Client.objects.annotate(
        invoice_count=Count('invoices'),
        total_revenue=Sum('invoices__total')
    ).order_by('name')
    return render(request, 'invoices/client_list.html', {'clients': clients})


@login_required
def create_client(request):
    """Create new client"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client created successfully!')
            return redirect('invoices:client_list')
    else:
        form = ClientForm()
    return render(request, 'invoices/client_form.html', {'form': form, 'title': 'Add Client'})


@login_required
def edit_client(request, pk):
    """Edit client"""
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client updated successfully!')
            return redirect('invoices:client_list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'invoices/client_form.html', {'form': form, 'client': client, 'title': 'Edit Client'})


@login_required
def delete_client(request, pk):
    """Delete client"""
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Client deleted successfully!')
        return redirect('invoices:client_list')
    return render(request, 'invoices/client_confirm_delete.html', {'client': client})


@login_required
def product_list(request):
    """List all products"""
    products = Product.objects.all().order_by('name')
    return render(request, 'invoices/product_list.html', {'products': products})


@login_required
def create_product(request):
    """Create new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully!')
            return redirect('invoices:product_list')
    else:
        form = ProductForm()
    return render(request, 'invoices/product_form.html', {'form': form, 'title': 'Add Product'})


@login_required
def edit_product(request, pk):
    """Edit product"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('invoices:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'invoices/product_form.html', {'form': form, 'product': product, 'title': 'Edit Product'})


@login_required
def delete_product(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('invoices:product_list')
    return render(request, 'invoices/product_confirm_delete.html', {'product': product})


@login_required
def reports(request):
    """Reports and analytics"""
    # Revenue statistics
    total_revenue = Invoice.objects.filter(status='PAID').aggregate(total=Sum('total'))['total'] or Decimal('0')
    paid_count = Invoice.objects.filter(status='PAID').count()
    pending_count = Invoice.objects.filter(status='PENDING').count()
    overdue_count = Invoice.objects.filter(status='OVERDUE').count()
    draft_count = Invoice.objects.filter(status='DRAFT').count()
    
    # Status breakdown for pie chart
    status_breakdown = {
        'PAID': paid_count,
        'PENDING': pending_count,
        'OVERDUE': overdue_count,
        'DRAFT': draft_count,
    }
    
    # Monthly revenue (last 6 months)
    monthly_revenue = []
    for i in range(5, -1, -1):
        month_start = date.today().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        revenue = Invoice.objects.filter(
            invoice_date__gte=month_start,
            invoice_date__lte=month_end
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        monthly_revenue.append({
            'month': month_start.strftime('%b'),
            'revenue': float(revenue)
        })
    
    # Top clients revenue
    top_clients = Client.objects.annotate(
        total_revenue=Sum('invoices__total')
    ).filter(total_revenue__gt=0).order_by('-total_revenue')[:5]
    
    client_revenue = []
    for client in top_clients:
        client_revenue.append({
            'name': client.name[:20] + '...' if len(client.name) > 20 else client.name,
            'revenue': float(client.total_revenue or 0)
        })
    
    context = {
        'total_revenue': total_revenue,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'monthly_revenue': monthly_revenue,
        'status_breakdown': status_breakdown,
        'client_revenue': client_revenue,
    }
    return render(request, 'invoices/reports.html', context)


@login_required
def company_list(request):
    """List all companies for current user"""
    companies = Company.objects.filter(user=request.user).order_by('-is_default', 'name')
    return render(request, 'invoices/company_list.html', {'companies': companies})


@login_required
def create_company(request):
    """Create new company"""
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.save()
            messages.success(request, 'Company created successfully!')
            return redirect('invoices:company_list')
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CompanyForm()
    return render(request, 'invoices/company_form.html', {'form': form, 'title': 'Add New Company', 'company': None})


@login_required
def edit_company(request, pk):
    """Edit company"""
    company = get_object_or_404(Company, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            company = form.save()
            messages.success(request, 'Company updated successfully!')
            return redirect('invoices:company_list')
        else:
            # Reload company from DB to show current stamp even if form has errors
            company.refresh_from_db()
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'invoices/company_form.html', {'form': form, 'company': company, 'title': 'Edit Company'})


@login_required
def delete_company(request, pk):
    """Delete company"""
    company = get_object_or_404(Company, pk=pk, user=request.user)
    if request.method == 'POST':
        if company.invoices.exists():
            messages.error(request, f'Cannot delete company "{company.name}" as it has invoices.')
            return redirect('invoices:company_list')
        company.delete()
        messages.success(request, 'Company deleted successfully!')
        return redirect('invoices:company_list')
    return render(request, 'invoices/company_confirm_delete.html', {'company': company})


@login_required
def settings(request):
    """Company settings (legacy)"""
    settings_obj = CompanySettings.get_settings()
    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved successfully!')
            return redirect('invoices:settings')
    else:
        form = CompanySettingsForm(instance=settings_obj)
    return render(request, 'invoices/settings.html', {'form': form})


@login_required
def api_po_line_items(request, po_id):
    """API endpoint to get PO line items for a PO"""
    try:
        po = get_object_or_404(PurchaseOrder, pk=po_id)
        line_items = []
        for item in po.subline_items.all():
            line_items.append({
                'id': item.id,
                'subline_number': item.subline_number,
                'description': item.subline_description,
                'quantity': str(item.quantity),
                'available_quantity': str(item.get_available_quantity()),
                'price': str(item.price),
            })
        return JsonResponse({'items': line_items})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_company_pos(request, company_id):
    """API endpoint to get POs for a company"""
    try:
        company = get_object_or_404(Company, pk=company_id, user=request.user)
        pos = PurchaseOrder.objects.filter(company=company).order_by('-created_at')
        po_list = []
        for po in pos:
            po_list.append({
                'id': po.id,
                'po_number': po.po_number,
                'description': po.main_line_description,
                'display': f"{po.po_number} - {po.main_line_description}",
            })
        return JsonResponse({'pos': po_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_company_next_invoice_number(request, company_id):
    """API endpoint to get next invoice number for a company"""
    try:
        company = get_object_or_404(Company, pk=company_id, user=request.user)
        next_invoice_number = company.get_next_invoice_number()
        return JsonResponse({'invoice_number': next_invoice_number})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def add_payment(request, invoice_id):
    """Add payment to invoice"""
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, invoice=invoice)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.created_by = request.user
            payment.save()
            messages.success(request, f'Payment of ₹{payment.net_amount:,.2f} recorded successfully!')
            return redirect('invoices:invoice_detail', pk=invoice_id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PaymentForm(invoice=invoice)
    
    return render(request, 'invoices/payment_form.html', {
        'form': form,
        'invoice': invoice,
        'title': 'Add Payment'
    })


@login_required
def edit_payment(request, pk):
    """Edit payment"""
    payment = get_object_or_404(Payment, pk=pk)
    invoice = payment.invoice
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment, invoice=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated successfully!')
            return redirect('invoices:invoice_detail', pk=invoice.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PaymentForm(instance=payment, invoice=invoice)
    
    return render(request, 'invoices/payment_form.html', {
        'form': form,
        'invoice': invoice,
        'payment': payment,
        'title': 'Edit Payment'
    })


@login_required
def delete_payment(request, pk):
    """Delete payment"""
    payment = get_object_or_404(Payment, pk=pk)
    invoice = payment.invoice
    
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted successfully!')
        return redirect('invoices:invoice_detail', pk=invoice.pk)
    
    return render(request, 'invoices/payment_confirm_delete.html', {
        'payment': payment,
        'invoice': invoice
    })


@login_required
def api_po_line_item_detail(request, item_id):
    """API endpoint to get a specific PO line item details"""
    try:
        item = get_object_or_404(POLineItem, pk=item_id)
        return JsonResponse({
            'id': item.id,
            'description': item.subline_description,
            'quantity': str(item.quantity),
            'available_quantity': str(item.get_available_quantity()),
            'price': str(item.price),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def eway_bill_data(request, pk):
    """Generate e-way bill JSON data for invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    company = invoice.company
    client = invoice.client
    items = invoice.items.all()
    
    if not company:
        messages.error(request, 'Company not found for this invoice.')
        return redirect('invoices:invoice_detail', pk=pk)
    
    # Prepare e-way bill data according to GSTN format
    eway_bill_data = {
        "version": "1.0.0421",
        "billLists": [
            {
                "userGstin": company.gstin or "",
                "supplyType": "O",  # O=Outward, I=Inward
                "subSupplyType": "1",  # 1=Supply, 2=Import, etc.
                "docType": "INV",  # INV=Invoice, CHL=Challan, etc.
                "docNo": invoice.invoice_number,
                "docDate": invoice.invoice_date.strftime("%d/%m/%Y"),
                "fromGstin": company.gstin or "",
                "fromTrdName": company.name,
                "fromAddr1": company.address.split('\n')[0] if company.address else "",
                "fromAddr2": '\n'.join(company.address.split('\n')[1:]) if company.address and '\n' in company.address else "",
                "fromPlace": company.address.split(',')[-1].strip() if company.address else "",
                "fromPincode": "",  # Add if available in Company model
                "fromStateCode": "",  # Extract from address or add field
                "actFromStateCode": "",  # Actual state code
                "toGstin": client.address or "",  # Client GSTIN if available
                "toTrdName": client.name,
                "toAddr1": client.address.split('\n')[0] if client.address else "",
                "toAddr2": '\n'.join(client.address.split('\n')[1:]) if client.address and '\n' in client.address else "",
                "toPlace": client.address.split(',')[-1].strip() if client.address else "",
                "toPincode": "",
                "toStateCode": invoice.state_code or "",
                "actToStateCode": invoice.state_code or "",
                "transactionType": "1",  # 1=Regular, 2=Bill to Ship to
                "otherValue": 0,
                "totInvValue": float(invoice.total),
                "cgstValue": float(invoice.cgst_amount),
                "sgstValue": float(invoice.sgst_amount),
                "igstValue": 0,
                "cessValue": 0,
                "transMode": "",  # 1=Road, 2=Rail, 3=Air, 4=Ship
                "transDistance": "",
                "transporterName": "",
                "transporterId": "",
                "transporterDocNo": "",
                "transporterDocDate": "",
                "vehicleNo": "",
                "vehicleType": "",
                "itemList": []
            }
        ]
    }
    
    # Add items
    for idx, item in enumerate(items, 1):
        item_data = {
            "itemNo": idx,
            "productName": item.description,
            "productDesc": item.description,
            "hsnCode": item.sac_code or "",
            "qtyUnit": "",  # UOM code
            "quantity": float(item.quantity),
            "taxableAmount": float(item.total),
            "igstRate": 0,
            "igstValue": 0,
            "cgstRate": float(invoice.cgst_rate),
            "cgstValue": float(item.total * invoice.cgst_rate / 100),
            "sgstRate": float(invoice.sgst_rate),
            "sgstValue": float(item.total * invoice.sgst_rate / 100),
            "cessRate": 0,
            "cessValue": 0,
            "cessNonAdvolValue": 0
        }
        eway_bill_data["billLists"][0]["itemList"].append(item_data)
    
    # Return as downloadable JSON file
    response = HttpResponse(
        json.dumps(eway_bill_data, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="eway_bill_{invoice.invoice_number}.json"'
    return response


@login_required
def eway_bill_info(request, pk):
    """Show e-way bill information page"""
    invoice = get_object_or_404(Invoice, pk=pk)
    company = invoice.company
    client = invoice.client
    items = invoice.items.all()
    
    if not company:
        messages.error(request, 'Company not found for this invoice.')
        return redirect('invoices:invoice_detail', pk=pk)
    
    # Prepare e-way bill details for display
    eway_info = {
        'invoice': invoice,
        'company': company,
        'client': client,
        'items': items,
        'eway_portal_url': 'https://ewaybillgst.gov.in/',
    }
    
    return render(request, 'invoices/eway_bill_info.html', eway_info)
