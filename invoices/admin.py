from django.contrib import admin
from .models import Client, Product, PurchaseOrder, POLineItem, Invoice, InvoiceItem, Company, CompanySettings, UOM


@admin.register(UOM)
class UOMAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    ordering = ('name',)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email', 'phone')
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'unit_price', 'tax_rate', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku', 'category')
    ordering = ('name',)


class POLineItemInline(admin.TabularInline):
    model = POLineItem
    extra = 1
    fields = ('subline_number', 'subline_description', 'quantity', 'price', 'uom', 'get_total')
    readonly_fields = ('get_total',)
    
    def get_total(self, obj):
        if obj.pk:
            return f"₹{obj.get_total():.2f}"
        return "-"
    get_total.short_description = 'Total'


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'main_line_number', 'main_line_description', 'get_total', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('po_number', 'main_line_description')
    ordering = ('-created_at',)
    inlines = [POLineItemInline]
    
    def get_total(self, obj):
        return f"₹{obj.get_total():.2f}"
    get_total.short_description = 'Total'


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('description', 'sac_code', 'quantity', 'rate', 'total')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'company', 'client', 'invoice_date', 'due_date', 'total', 'status', 'created_at')
    list_filter = ('status', 'invoice_date', 'created_at', 'company')
    search_fields = ('invoice_number', 'client__name', 'company__name')
    readonly_fields = ('subtotal', 'cgst_amount', 'sgst_amount', 'tax_amount', 'total', 'created_at', 'updated_at')
    inlines = [InvoiceItemInline]
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'company', 'client', 'po_reference', 'po_number', 'po_date', 'vendor_code', 'invoice_date', 'due_date', 'status')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_rate', 'cgst_rate', 'sgst_rate', 'cgst_amount', 'sgst_amount', 'tax_amount', 'discount', 'total')
        }),
        ('Tax & Supply Details', {
            'fields': ('place_of_supply', 'state_code', 'reverse_charge', 'reverse_charge_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'gstin', 'user', 'is_active', 'is_default', 'has_stamp', 'created_at')
    list_filter = ('is_active', 'is_default', 'created_at')
    search_fields = ('name', 'gstin', 'pan', 'cin')
    ordering = ('-is_default', 'name')
    readonly_fields = ('created_at', 'updated_at')
    
    def has_stamp(self, obj):
        return bool(obj.stamp)
    has_stamp.boolean = True
    has_stamp.short_description = 'Has Stamp'


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Only allow one settings record
        return not CompanySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
