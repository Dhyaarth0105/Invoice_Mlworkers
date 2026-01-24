# InvoicePro - Smart Invoice Management System

A comprehensive Django-based invoice management system with multi-company support, purchase order tracking, and automated reminders.

## Features

- **Multi-Company Support**: Manage multiple companies with separate invoice numbering
- **Purchase Order Management**: Track POs with main lines and subline items
- **Invoice Generation**: Create invoices with tax calculations (CGST/SGST)
- **PDF Export**: Generate professional invoice PDFs
- **Document Management**: Upload measurement sheets and bill summaries
- **Automated Reminders**: Email reminders for upcoming and overdue invoices
- **Client Management**: Manage client database with contact information
- **UOM Master**: Manage units of measurement
- **Responsive Design**: Mobile-friendly interface

## Technology Stack

- **Backend**: Django 5.0+
- **Database**: PostgreSQL
- **PDF Generation**: ReportLab
- **Email**: Zoho SMTP
- **Web Server**: Nginx + Gunicorn

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/Dhyaarth0105/Invoice_Mlworkers.git
cd Invoice_Mlworkers
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file:
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=invoice_db
DB_USER=invoice_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run development server:
```bash
python manage.py runserver
```

## Production Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions to Hostinger VPS.

### Quick Deployment Steps

1. SSH to server:
```bash
ssh root@145.223.22.228
```

2. Run deployment script:
```bash
cd /var/www
git clone https://github.com/Dhyaarth0105/Invoice_Mlworkers.git invoice_mlworkers
cd invoice_mlworkers
chmod +x deploy_to_server.sh
sudo ./deploy_to_server.sh
```

3. Configure `.env` file with production settings

4. Set up SSL certificate:
```bash
certbot --nginx -d invoice.mlworkers.com
```

## Project Structure

```
Invoice_Mlworkers/
├── accounts/              # User authentication app
├── invoices/              # Main invoice management app
├── invoice_project/       # Django project settings
├── templates/             # HTML templates
├── static/                # Static files (CSS, JS)
├── media/                 # User uploaded files
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── deploy.sh              # Local deployment script
├── deploy_to_server.sh    # Server deployment script
├── nginx_invoice.conf     # Nginx configuration
├── gunicorn.service       # Systemd service file
└── DEPLOYMENT_GUIDE.md    # Detailed deployment guide
```

## Key Models

- **User**: Custom user model with roles
- **Company**: Multi-company support with invoice prefix
- **Client**: Client/customer management
- **PurchaseOrder**: PO with main lines
- **POLineItem**: PO subline items with quantity and price
- **Invoice**: Invoice with tax calculations
- **InvoiceItem**: Invoice line items
- **UOM**: Units of measurement

## Management Commands

### Create Sample Data
```bash
python manage.py create_sample_data
```

### Send Invoice Reminders
```bash
# Dry run (test)
python manage.py send_invoice_reminders --dry-run

# Send reminders (3 days before due date)
python manage.py send_invoice_reminders

# Custom days before
python manage.py send_invoice_reminders --days-before 5
```

## Environment Variables

Required environment variables (set in `.env` file):

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=invoice.mlworkers.com,145.223.22.228

# Database
DB_NAME=invoice_db
DB_USER=invoice_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Email (Zoho SMTP)
EMAIL_HOST=smtp.zoho.in
EMAIL_PORT=465
EMAIL_HOST_USER=your-email@mlworkers.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=InvoicePro <noreply@mlworkers.com>
```

## API Endpoints

- `/api/po/<po_id>/line-items/` - Get PO line items
- `/api/po-line-item/<item_id>/` - Get PO line item details
- `/api/company/<company_id>/pos/` - Get company POs
- `/api/company/<company_id>/next-invoice-number/` - Get next invoice number

## License

Private - ML Workers

## Support

For issues and questions, contact the development team.
