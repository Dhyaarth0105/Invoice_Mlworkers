#!/bin/bash
# Deployment script for invoice_mlworkers.com on Hostinger VPS
# This script sets up the application without disturbing existing applications

set -e  # Exit on error

echo "=========================================="
echo "Deploying InvoicePro to Hostinger VPS"
echo "Application: invoice.mlworkers.com"
echo "=========================================="

# Variables
APP_NAME="invoice_mlworkers"
APP_DIR="/var/www/$APP_NAME"
DOMAIN="invoice.mlworkers.com"
USER="www-data"
PYTHON_VERSION="3.11"  # Adjust based on server Python version

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Step 1: Creating application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

echo "Step 2: Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Step 3: Installing Python dependencies..."
pip install --upgrade pip
pip install django gunicorn psycopg2-binary python-decouple

echo "Step 4: Creating necessary directories..."
mkdir -p static media logs
chown -R $USER:$USER $APP_DIR
chmod -R 755 $APP_DIR

echo "Step 5: Setting up log directory..."
mkdir -p /var/log/$APP_NAME
chown -R $USER:$USER /var/log/$APP_NAME

echo "=========================================="
echo "Deployment script completed!"
echo "Next steps:"
echo "1. Upload your Django project files to $APP_DIR"
echo "2. Create .env file with database and email credentials"
echo "3. Run migrations: python manage.py migrate"
echo "4. Collect static files: python manage.py collectstatic"
echo "5. Configure Nginx (see nginx.conf)"
echo "6. Set up systemd service (see gunicorn.service)"
echo "=========================================="

