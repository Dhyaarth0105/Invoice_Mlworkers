# Quick Deployment Guide - Hostinger VPS

## Prerequisites
- SSH access: `root@145.223.22.228`
- Password: `Dhyaarth@0105`
- PostgreSQL already installed on server
- Domain: `invoice.mlworkers.com`

## Quick Deployment Steps

### 1. Connect to Server
```bash
ssh root@145.223.22.228
```

### 2. Run Deployment Script
```bash
cd /var/www
git clone https://github.com/Dhyaarth0105/Invoice_Mlworkers.git invoice_mlworkers
cd invoice_mlworkers
chmod +x deploy_production.sh
./deploy_production.sh
```

The script will:
- ✅ Install required packages (if needed)
- ✅ Clone/update repository
- ✅ Set up Python virtual environment
- ✅ Install dependencies
- ✅ Create PostgreSQL database (`invoice_db`) - **Won't disturb existing databases**
- ✅ Generate secure database password
- ✅ Create .env file with database credentials
- ✅ Run migrations
- ✅ Collect static files
- ✅ Set up Gunicorn service (port 8001 - won't conflict)
- ✅ Configure Nginx
- ✅ Start services

### 3. Update Email Credentials
```bash
nano /var/www/invoice_mlworkers/.env
```

Update these lines:
```env
EMAIL_HOST_USER=your-email@mlworkers.com
EMAIL_HOST_PASSWORD=your-email-password
```

Save and exit (Ctrl+X, Y, Enter)

### 4. Create Superuser
```bash
cd /var/www/invoice_mlworkers
source venv/bin/activate
python manage.py createsuperuser
```

### 5. Set Up DNS
In your domain DNS settings (Hostinger or domain registrar):
- **Type**: A
- **Name**: invoice
- **Value**: 145.223.22.228
- **TTL**: 3600

### 6. Set Up SSL (After DNS propagates - usually 1-2 hours)
```bash
certbot --nginx -d invoice.mlworkers.com
```

## Important Notes

### Database Safety
- ✅ Creates separate database: `invoice_db`
- ✅ Creates separate user: `invoice_user`
- ✅ **Won't affect existing databases**
- ✅ Password is auto-generated and shown in deployment output

### Port Safety
- ✅ Uses port **8001** for Gunicorn (won't conflict with other apps)
- ✅ Nginx proxies to port 8001

### Service Safety
- ✅ Service name: `invoice_mlworkers` (unique)
- ✅ Separate Nginx config file
- ✅ Separate log directories

## Verification

### Check if service is running:
```bash
systemctl status invoice_mlworkers
```

### Check Nginx:
```bash
systemctl status nginx
nginx -t
```

### View logs:
```bash
# Application logs
tail -f /var/log/invoice_mlworkers/error.log

# Nginx logs
tail -f /var/log/nginx/invoice_mlworkers_error.log
```

### Test application:
Visit: `http://invoice.mlworkers.com` (or IP: `http://145.223.22.228`)

## Troubleshooting

### If service fails to start:
```bash
systemctl restart invoice_mlworkers
journalctl -u invoice_mlworkers -n 50
```

### If database connection fails:
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection
sudo -u postgres psql -c "\l" | grep invoice_db
```

### If static files not loading:
```bash
cd /var/www/invoice_mlworkers
source venv/bin/activate
python manage.py collectstatic --noinput
```

### Restart everything:
```bash
systemctl restart invoice_mlworkers
systemctl restart nginx
```

## Database Password Recovery

If you need to see the database password again:
```bash
cat /var/www/invoice_mlworkers/.env | grep DB_PASSWORD
```

Or reset it:
```bash
sudo -u postgres psql
ALTER USER invoice_user WITH PASSWORD 'new-password';
\q
```

Then update `.env` file with new password.

## Update Application

To update the application after code changes:
```bash
cd /var/www/invoice_mlworkers
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart invoice_mlworkers
```

## Security Checklist

- [x] Separate database (won't conflict)
- [x] Strong auto-generated password
- [x] DEBUG=False in production
- [x] Secure SECRET_KEY
- [x] Proper file permissions
- [ ] SSL certificate (after DNS setup)
- [ ] Firewall configured (if applicable)

