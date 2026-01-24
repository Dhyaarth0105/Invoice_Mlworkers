#!/bin/bash
# Complete Production Deployment Script for InvoicePro
# Run this on Hostinger VPS as root
# This script ensures no conflicts with existing applications

set -e  # Exit on error

echo "=========================================="
echo "InvoicePro Production Deployment"
echo "Domain: invoice.mlworkers.com"
echo "=========================================="

# Variables
APP_NAME="invoice_mlworkers"
APP_DIR="/var/www/$APP_NAME"
GIT_REPO="https://github.com/Dhyaarth0105/Invoice_Mlworkers.git"
DOMAIN="invoice.mlworkers.com"
DB_NAME="invoice_db"
DB_USER="invoice_user"
SERVICE_USER="www-data"
GUNICORN_PORT="8001"  # Using 8001 to avoid conflicts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Checking system requirements...${NC}"
# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Installing Python3..."
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
fi

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}PostgreSQL not found. Installing...${NC}"
    apt-get update
    apt-get install -y postgresql postgresql-contrib
fi

# Check Nginx
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Nginx not found. Installing...${NC}"
    apt-get update
    apt-get install -y nginx
fi

# Check Git
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    apt-get update
    apt-get install -y git
fi

echo -e "${GREEN}Step 2: Creating application directory...${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

echo -e "${GREEN}Step 3: Cloning repository...${NC}"
if [ -d ".git" ]; then
    echo "Repository exists, pulling latest..."
    git pull origin main
else
    git clone $GIT_REPO .
fi

echo -e "${GREEN}Step 4: Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo -e "${GREEN}Step 5: Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}Step 6: Creating necessary directories...${NC}"
mkdir -p static media logs
chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 775 $APP_DIR/media

echo -e "${GREEN}Step 7: Setting up log directory...${NC}"
mkdir -p /var/log/$APP_NAME
chown -R $SERVICE_USER:$SERVICE_USER /var/log/$APP_NAME

echo -e "${GREEN}Step 8: Creating PostgreSQL database...${NC}"
# Generate a secure random password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Create database and user
sudo -u postgres psql <<EOF
-- Check if database exists
SELECT 1 FROM pg_database WHERE datname = '$DB_NAME' \gexec

-- Create database if it doesn't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME') THEN
        CREATE DATABASE $DB_NAME;
    END IF;
END
\$\$;

-- Create user if it doesn't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    ELSE
        ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Grant privileges
ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
EOF

echo -e "${GREEN}Database created successfully!${NC}"
echo -e "${YELLOW}Database Name: $DB_NAME${NC}"
echo -e "${YELLOW}Database User: $DB_USER${NC}"
echo -e "${YELLOW}Database Password: $DB_PASSWORD${NC}"
echo -e "${RED}SAVE THIS PASSWORD - You'll need it for .env file${NC}"

echo -e "${GREEN}Step 9: Creating .env file template...${NC}"
if [ ! -f "$APP_DIR/.env" ]; then
    cat > $APP_DIR/.env <<ENVFILE
# Django Settings
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
ALLOWED_HOSTS=invoice.mlworkers.com,145.223.22.228,localhost

# Database (PostgreSQL)
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
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
ENVFILE
    chown $SERVICE_USER:$SERVICE_USER $APP_DIR/.env
    chmod 600 $APP_DIR/.env
    echo -e "${GREEN}.env file created!${NC}"
    echo -e "${YELLOW}Please edit .env file and update EMAIL_HOST_USER and EMAIL_HOST_PASSWORD${NC}"
else
    echo -e "${YELLOW}.env file already exists, skipping...${NC}"
fi

echo -e "${GREEN}Step 10: Running database migrations...${NC}"
source venv/bin/activate
python manage.py migrate --noinput

echo -e "${GREEN}Step 11: Collecting static files...${NC}"
python manage.py collectstatic --noinput

echo -e "${GREEN}Step 12: Setting up Gunicorn service...${NC}"
# Update gunicorn.service with correct paths
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$APP_DIR|g" gunicorn.service
sed -i "s|Environment=.*|Environment=\"PATH=$APP_DIR/venv/bin\"|g" gunicorn.service
sed -i "s|ExecStart=.*|ExecStart=$APP_DIR/venv/bin/gunicorn \\\\|g" gunicorn.service
sed -i "s|--bind 127.0.0.1:.*|--bind 127.0.0.1:$GUNICORN_PORT \\\\|g" gunicorn.service
sed -i "s|--access-logfile.*|--access-logfile /var/log/$APP_NAME/access.log \\\\|g" gunicorn.service
sed -i "s|--error-logfile.*|--error-logfile /var/log/$APP_NAME/error.log \\\\|g" gunicorn.service

cp gunicorn.service /etc/systemd/system/$APP_NAME.service
systemctl daemon-reload
systemctl enable $APP_NAME
systemctl restart $APP_NAME

echo -e "${GREEN}Step 13: Setting up Nginx configuration...${NC}"
# Update nginx config with correct port
sed -i "s|proxy_pass http://127.0.0.1:.*|proxy_pass http://127.0.0.1:$GUNICORN_PORT;|g" nginx_invoice.conf
sed -i "s|alias /var/www/invoice_mlworkers/|alias $APP_DIR/|g" nginx_invoice.conf

cp nginx_invoice.conf /etc/nginx/sites-available/$APP_NAME
if [ ! -L "/etc/nginx/sites-enabled/$APP_NAME" ]; then
    ln -s /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
fi

echo -e "${GREEN}Step 14: Testing Nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}Nginx configuration is valid${NC}"
    systemctl reload nginx
else
    echo -e "${RED}Nginx configuration has errors!${NC}"
    exit 1
fi

echo -e "${GREEN}Step 15: Setting final permissions...${NC}"
chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 775 $APP_DIR/media
chmod 600 $APP_DIR/.env

echo "=========================================="
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Application Details:"
echo "  - Directory: $APP_DIR"
echo "  - Domain: $DOMAIN"
echo "  - Database: $DB_NAME"
echo "  - Database User: $DB_USER"
echo "  - Database Password: $DB_PASSWORD"
echo ""
echo "Next Steps:"
echo "  1. Edit .env file and update email credentials:"
echo "     nano $APP_DIR/.env"
echo ""
echo "  2. Create superuser:"
echo "     cd $APP_DIR"
echo "     source venv/bin/activate"
echo "     python manage.py createsuperuser"
echo ""
echo "  3. Set up DNS A record:"
echo "     Type: A"
echo "     Name: invoice"
echo "     Value: 145.223.22.228"
echo ""
echo "  4. After DNS propagates, set up SSL:"
echo "     certbot --nginx -d $DOMAIN"
echo ""
echo "  5. Check service status:"
echo "     systemctl status $APP_NAME"
echo ""
echo "  6. View logs:"
echo "     tail -f /var/log/$APP_NAME/error.log"
echo "     tail -f /var/log/nginx/${APP_NAME}_error.log"
echo ""
echo -e "${RED}IMPORTANT: Save the database password shown above!${NC}"
echo "=========================================="

