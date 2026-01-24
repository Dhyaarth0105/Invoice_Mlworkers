# Deployment Guide: InvoicePro to Hostinger VPS

## Prerequisites
- SSH access to Hostinger VPS: `root@145.223.22.228`
- Domain: `invoice.mlworkers.com` (subdomain of mlworkers.com)
- Existing applications should not be disturbed

## Step 1: Connect to Server

```bash
ssh root@145.223.22.228
# Password: Dhyaarth@0105
```

## Step 2: Check Existing Setup

```bash
# Check Python version
python3 --version

# Check if PostgreSQL is installed
psql --version

# Check Nginx configuration
ls -la /etc/nginx/sites-enabled/

# Check existing applications
ls -la /var/www/
```

## Step 3: Create Application Directory

```bash
# Create directory for the application
mkdir -p /var/www/invoice_mlworkers
cd /var/www/invoice_mlworkers
```

## Step 4: Upload Project Files

From your local machine, upload the project:

```bash
# Using SCP (from local machine)
scp -r invoice-demo/* root@145.223.22.228:/var/www/invoice_mlworkers/

# Or use SFTP/FTP client
# Upload all files except: venv, __pycache__, *.pyc, db.sqlite3
```

**Important:** Exclude these from upload:
- `venv/` (virtual environment)
- `__pycache__/`
- `*.pyc`
- `db.sqlite3` (we'll use PostgreSQL)
- `.git/` (optional)

## Step 5: Set Up Python Virtual Environment

```bash
cd /var/www/invoice_mlworkers

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install django gunicorn psycopg2-binary python-decouple
```

## Step 6: Create .env File

```bash
cd /var/www/invoice_mlworkers
nano .env
```

Add the following (adjust values as needed):

```env
# Django Settings
SECRET_KEY=your-secret-key-here-generate-new-one
DEBUG=False
ALLOWED_HOSTS=invoice.mlworkers.com,145.223.22.228

# Database (PostgreSQL)
DB_NAME=invoice_db
DB_USER=invoice_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (Zoho SMTP)
EMAIL_HOST=smtp.zoho.in
EMAIL_PORT=465
EMAIL_HOST_USER=your-email@mlworkers.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=InvoicePro <noreply@mlworkers.com>

# Static Files
STATIC_ROOT=/var/www/invoice_mlworkers/static
MEDIA_ROOT=/var/www/invoice_mlworkers/media
```

## Step 7: Update settings.py for Production

Update `invoice_project/settings.py`:

```python
import os
from decouple import config

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Static files
STATIC_ROOT = config('STATIC_ROOT', default='/var/www/invoice_mlworkers/static')
MEDIA_ROOT = config('MEDIA_ROOT', default='/var/www/invoice_mlworkers/media')

# Email Configuration
EMAIL_BACKEND = 'accounts.email_backend.CustomEmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
```

## Step 8: Create PostgreSQL Database

```bash
# Switch to postgres user
su - postgres

# Create database and user
psql

# In PostgreSQL prompt:
CREATE DATABASE invoice_db;
CREATE USER invoice_user WITH PASSWORD 'your-db-password';
ALTER ROLE invoice_user SET client_encoding TO 'utf8';
ALTER ROLE invoice_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE invoice_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE invoice_db TO invoice_user;
\q

# Exit postgres user
exit
```

## Step 9: Run Migrations and Collect Static Files

```bash
cd /var/www/invoice_mlworkers
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## Step 10: Set Up Gunicorn Service

```bash
# Copy service file
cp gunicorn.service /etc/systemd/system/invoice_mlworkers.service

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable invoice_mlworkers

# Start service
systemctl start invoice_mlworkers

# Check status
systemctl status invoice_mlworkers
```

## Step 11: Configure Nginx

```bash
# Copy nginx configuration
cp nginx_invoice.conf /etc/nginx/sites-available/invoice_mlworkers

# Create symlink
ln -s /etc/nginx/sites-available/invoice_mlworkers /etc/nginx/sites-enabled/

# Test nginx configuration
nginx -t

# Reload nginx
systemctl reload nginx
```

## Step 12: Set Up SSL Certificate (Let's Encrypt)

```bash
# Install certbot if not already installed
apt-get update
apt-get install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d invoice.mlworkers.com

# Auto-renewal is set up automatically
```

## Step 13: Set Permissions

```bash
# Set proper ownership
chown -R www-data:www-data /var/www/invoice_mlworkers
chmod -R 755 /var/www/invoice_mlworkers

# Media directory needs write permissions
chmod -R 775 /var/www/invoice_mlworkers/media
```

## Step 14: Configure Domain DNS

In your domain DNS settings (Hostinger or domain registrar):

1. Add A record:
   - Type: A
   - Name: invoice (or @ if using subdomain)
   - Value: 145.223.22.228
   - TTL: 3600

2. Wait for DNS propagation (can take up to 24 hours, usually 1-2 hours)

## Step 15: Test the Application

1. Visit: `http://invoice.mlworkers.com` (or https after SSL)
2. Check if application loads
3. Test login functionality
4. Check static files are loading

## Troubleshooting

### Check Gunicorn logs:
```bash
tail -f /var/log/invoice_mlworkers/error.log
```

### Check Nginx logs:
```bash
tail -f /var/log/nginx/invoice_mlworkers_error.log
```

### Restart services:
```bash
systemctl restart invoice_mlworkers
systemctl restart nginx
```

### Check if port is in use:
```bash
netstat -tulpn | grep 8001
```

## Maintenance Commands

```bash
# Restart application
systemctl restart invoice_mlworkers

# View application logs
journalctl -u invoice_mlworkers -f

# Update code (after uploading new files)
cd /var/www/invoice_mlworkers
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart invoice_mlworkers
```

## Important Notes

1. **Port 8001**: Using port 8001 for Gunicorn to avoid conflicts with other applications
2. **Database**: Using separate PostgreSQL database to avoid conflicts
3. **Static Files**: Separate static directory to avoid conflicts
4. **Service Name**: Unique service name `invoice_mlworkers` to avoid conflicts
5. **Nginx Config**: Separate config file that won't interfere with existing sites

## Security Checklist

- [ ] DEBUG = False in production
- [ ] Strong SECRET_KEY
- [ ] SSL certificate installed
- [ ] Database password is strong
- [ ] File permissions set correctly
- [ ] Firewall configured (if applicable)
- [ ] Regular backups set up

