# InvoicePro – QA Report

**Date:** 2026-01-26  
**Scope:** Security, data scoping, reports, and critical flows  

---

## Critical issues fixed (security & data)

### 1. **Dashboard showed all users’ data (fixed)**
- **Issue:** Dashboard used `Invoice.objects.count()` and unfiltered `Invoice`/`Client` queries, so every user saw system-wide totals and recent invoices.
- **Fix:** Dashboard now scopes all stats to the current user’s companies (`_user_invoices(request)`, `_user_companies(request)`). Recent invoices and top clients are limited to those companies.

### 2. **Reports showed all users’ data (fixed)**
- **Issue:** Reports used unfiltered `Invoice.objects` and `Client.objects`, so revenue and charts were global.
- **Fix:** Reports now use `_user_invoices(request)` and clients are filtered by `invoices__company__in=user_companies`. Monthly revenue already used `status='PAID'`; scope was added.

### 3. **Monthly revenue included non-PAID invoices (fixed)**
- **Issue:** In reports, monthly revenue aggregated all invoices in the date range, not only `status='PAID'`.
- **Fix:** Monthly revenue query now includes `status='PAID'` so only paid revenue is shown.

### 4. **Invoice detail/PDF/edit/delete – no permission check (fixed)**
- **Issue:** Any logged-in user could view, download PDF, edit, or delete any invoice by guessing the ID (e.g. `/invoices/123/`).
- **Fix:** `invoice_detail`, `invoice_pdf`, `edit_invoice`, and `delete_invoice` now resolve the invoice via `_user_invoices(request).filter(pk=pk)` and return 404 if not in the user’s companies.

### 5. **Payments – no permission check (fixed)**
- **Issue:** `add_payment`, `edit_payment`, and `delete_payment` did not check that the invoice belonged to the user’s companies.
- **Fix:** Add payment uses `_user_invoices(request)` for the invoice; edit/delete payment check that the payment’s invoice is in `_user_invoices(request)`.

### 6. **PO edit/delete – no permission check (fixed)**
- **Issue:** Any user could edit or delete any purchase order by ID.
- **Fix:** `edit_po` and `delete_po` now load the PO with `PurchaseOrder.objects.filter(pk=pk, company__in=user_companies)` and return 404 if not found.

### 7. **E-Way Bill / E-Invoice – no permission check (fixed)**
- **Issue:** `eway_bill_data`, `eway_bill_info`, `einvoice_data`, and `einvoice_info` allowed access to any invoice by ID.
- **Fix:** All four views now resolve the invoice via `_user_invoices(request).filter(pk=pk)` and return 404 if not in the user’s companies.

### 8. **API `api_po_line_items` – no permission check (fixed)**
- **Issue:** Any user could fetch line items for any PO by ID.
- **Fix:** PO is loaded with `PurchaseOrder.objects.filter(pk=po_id, company__in=user_companies)`; 404 JSON response if not found.

---

## Design notes (no change)

### Clients are global
- **Observation:** `client_list` shows all clients; `Client` has no `user` or `company` FK. Invoices are scoped by company.
- **Interpretation:** Clients are treated as a shared address book; any user can pick any client when creating an invoice. Left as-is; document for product clarity.

### Invoice list & company list
- **Status:** Already correctly scoped to `user_companies` and `company__in=user_companies`. No change.

---

## Recommendations for further QA

1. **Forms & validation**
   - Test create/edit invoice with invalid dates (e.g. due_date before invoice_date).
   - Test negative quantity/rate and required fields (client, company).
   - Test file upload limits and types for measurement_sheet/bill_summary.

2. **Delete confirmations**
   - Ensure delete views require POST; confirm pages for invoice/PO/client/company/payment are not used as GET-only delete.

3. **CSRF**
   - All forms should use `{% csrf_token %}` (quick template audit).

4. **Performance**
   - Dashboard and reports use aggregates and filters; for large data, consider indexing on `(company_id, status)`, `(company_id, invoice_date)`.

5. **Browser/UX**
   - Login with wrong credentials, session timeout, and redirect after login.
   - Mobile: PO list, invoice list, and client list layouts (already improved in past work).

---

## Summary

| Area              | Issue                                      | Status   |
|-------------------|--------------------------------------------|----------|
| Dashboard         | Showed all users’ data                     | Fixed    |
| Reports           | Showed all users’ data                     | Fixed    |
| Reports           | Monthly revenue included non-PAID          | Fixed    |
| Invoice detail/PDF/edit/delete | No permission check              | Fixed    |
| Payments          | No permission check                        | Fixed    |
| PO edit/delete    | No permission check                        | Fixed    |
| E-Way / E-Invoice | No permission check                        | Fixed    |
| API PO line items | No permission check                        | Fixed    |
| Client list       | Global by design                           | Documented |

All listed security and data-scoping issues have been addressed in code. Run the test suite and a quick smoke test (login, dashboard, one invoice flow, reports) to confirm.
