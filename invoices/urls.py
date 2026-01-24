from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # UOM Master
    path('uom/', views.uom_list, name='uom_list'),
    path('uom/create/', views.create_uom, name='create_uom'),
    path('uom/<int:pk>/edit/', views.edit_uom, name='edit_uom'),
    path('uom/<int:pk>/delete/', views.delete_uom, name='delete_uom'),
    
    # Purchase Orders
    path('manage-po/', views.manage_po, name='manage_po'),
    path('po/create/', views.create_po, name='create_po'),
    path('po/<int:pk>/edit/', views.edit_po, name='edit_po'),
    path('po/<int:pk>/delete/', views.delete_po, name='delete_po'),
    
    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('invoices/<int:pk>/edit/', views.edit_invoice, name='edit_invoice'),
    path('invoices/<int:pk>/delete/', views.delete_invoice, name='delete_invoice'),
    
    # Payments
    path('invoices/<int:invoice_id>/payment/add/', views.add_payment, name='add_payment'),
    path('payments/<int:pk>/edit/', views.edit_payment, name='edit_payment'),
    path('payments/<int:pk>/delete/', views.delete_payment, name='delete_payment'),
    
    # Clients
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.create_client, name='create_client'),
    path('clients/<int:pk>/edit/', views.edit_client, name='edit_client'),
    path('clients/<int:pk>/delete/', views.delete_client, name='delete_client'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.create_product, name='create_product'),
    path('products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:pk>/delete/', views.delete_product, name='delete_product'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # Companies
    path('companies/', views.company_list, name='company_list'),
    path('companies/create/', views.create_company, name='create_company'),
    path('companies/<int:pk>/edit/', views.edit_company, name='edit_company'),
    path('companies/<int:pk>/delete/', views.delete_company, name='delete_company'),
    
    # Settings
    path('settings/', views.settings, name='settings'),
    
    # API endpoints
    path('api/po/<int:po_id>/line-items/', views.api_po_line_items, name='api_po_line_items'),
    path('api/po-line-item/<int:item_id>/', views.api_po_line_item_detail, name='api_po_line_item_detail'),
    path('api/company/<int:company_id>/pos/', views.api_company_pos, name='api_company_pos'),
    path('api/company/<int:company_id>/next-invoice-number/', views.api_company_next_invoice_number, name='api_company_next_invoice_number'),
]

