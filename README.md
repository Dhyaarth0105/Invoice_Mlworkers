# InvoicePro - Django Invoice Management System

A modern invoice management system built with Django and PostgreSQL.

## Features

- User Authentication (Signup, Login, Forgot Password with OTP)
- Purchase Order Management (PO with Main Line and Subline structure)
- Invoice Management (Create, Edit, Delete, View)
- Client Management
- Product/Service Catalog
- Reports & Analytics
- Company Settings
- Modern Dark Theme UI

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create PostgreSQL Database

Make sure PostgreSQL is installed and running. Create a database:

```sql
CREATE DATABASE invoice_db;
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Admin User

```bash
python manage.py shell
```

Then run:
```python
from accounts.models import User
User.objects.create_user(
    username='admin',
    email='admin@invoicepro.com',
    password='admin123',
    first_name='Admin',
    last_name='User',
    is_staff=True,
    is_superuser=True
)
```

Or use the create_admin.py script:
```bash
python create_admin.py
```

### 5. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

## Default Login Credentials

- Username: `admin`
- Password: `admin123`

## Database Configuration

The project uses PostgreSQL with the following default settings:
- Database: `invoice_db`
- User: `postgres`
- Password: `root@123`
- Host: `localhost`
- Port: `5432`

Update these in `invoice_project/settings.py` if needed.

## Project Structure

```
invoice-demo/
├── accounts/          # Authentication app
├── invoices/          # Invoice management app
├── templates/         # HTML templates
├── static/            # CSS, JS, images
├── invoice_project/   # Django project settings
└── manage.py
```

## Features Overview

### Authentication
- User signup with email verification
- Login with username or email
- Forgot password with OTP via email
- Secure password reset

### Invoice Management
- Create invoices linked to Purchase Orders
- Multi-item invoices with quantity and rates
- Automatic tax and discount calculations
- Invoice status tracking (Draft, Pending, Paid, Overdue)

### Purchase Orders
- Hierarchical PO structure (Main Line → Subline)
- Quantity and Unit of Measurement (UOM)
- Link POs to invoices

### Clients & Products
- Client database with contact information
- Product catalog with SKU and pricing
- Tax rate configuration

### Reports
- Revenue statistics
- Monthly revenue trends
- Invoice status breakdown
- Top clients analysis

## Email Configuration

For password reset OTP emails, configure email settings in `invoice_project/settings.py`:

```python
EMAIL_HOST = 'smtp.zoho.in'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'InvoicePro <noreply@invoicepro.com>'
```

## License

This project is for demonstration purposes.


