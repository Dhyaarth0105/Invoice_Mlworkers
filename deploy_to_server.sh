#!/bin/bash
# Deployment script to run on Hostinger VPS
# Run this script on the server after SSH connection

set -e  # Exit on error

echo "=========================================="
echo "Deploying InvoicePro from GitHub"
echo "Application: invoice.mlworkers.com"
echo "=========================================="

# Variables
APP_NAME="invoice_mlworkers"
APP_DIR="/var/www/$APP_NAME"
GIT_REPO="https://github.com/Dhyaarth0105/Invoice_Mlworkers.git"
DOMAIN="invoice.mlworkers.com"
USER="www-data"
PYTHON_VERSION="3.11"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Step 1: Installing required packages..."
apt-get update
apt-get install -y python3-pip python3-venv postgresql postgresql-contrib nginx git

echo "Step 2: Creating application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

echo "Step 3: Cloning repository..."
if [ -d ".git" ]; then
    echo "Repository already exists, pulling latest changes..."
    git pull origin main
else
    git clone $GIT_REPO .
fi

echo "Step 4: Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "Step 5: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Step 6: Creating necessary directories..."
mkdir -p static media logs
chown -R $USER:$USER $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 775 $APP_DIR/media

echo "Step 7: Setting up log directory..."
mkdir -p /var/log/$APP_NAME
chown -R $USER:$USER /var/log/$APP_NAME

echo "Step 8: Checking if .env file exists..."
if [ ! -f "$APP_DIR/.env" ]; then
    echo "WARNING: .env file not found!"
    echo "Please create .env file with the following variables:"
    echo "  - SECRET_KEY"
    echo "  - DEBUG=False"
    echo "  - ALLOWED_HOSTS"
    echo "  - Database credentials"
    echo "  - Email credentials"
    echo ""
    echo "See DEPLOYMENT_GUIDE.md for details"
    exit 1
fi

echo "Step 9: Running database migrations..."
source venv/bin/activate
python manage.py migrate --noinput

echo "Step 10: Collecting static files..."
python manage.py collectstatic --noinput

echo "Step 11: Setting up Gunicorn service..."
cp gunicorn.service /etc/systemd/system/$APP_NAME.service
systemctl daemon-reload
systemctl enable $APP_NAME
systemctl restart $APP_NAME

echo "Step 12: Setting up Nginx configuration..."
cp nginx_invoice.conf /etc/nginx/sites-available/$APP_NAME
if [ ! -L "/etc/nginx/sites-enabled/$APP_NAME" ]; then
    ln -s /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
fi

echo "Step 13: Testing Nginx configuration..."
nginx -t

echo "Step 14: Reloading Nginx..."
systemctl reload nginx

echo "=========================================="
echo "Deployment completed!"
echo "=========================================="
echo "Application URL: http://$DOMAIN"
echo ""
echo "Next steps:"
echo "1. Set up DNS A record for invoice.mlworkers.com pointing to server IP"
echo "2. Configure SSL certificate: certbot --nginx -d $DOMAIN"
echo "3. Create superuser: python manage.py createsuperuser"
echo ""
echo "Check service status:"
echo "  systemctl status $APP_NAME"
echo ""
echo "View logs:"
echo "  tail -f /var/log/$APP_NAME/error.log"
echo "  tail -f /var/log/nginx/${APP_NAME}_error.log"
echo "=========================================="

