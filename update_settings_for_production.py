"""
Script to update settings.py for production deployment
This adds support for python-decouple and environment variables
"""

import re

settings_file = 'invoice_project/settings.py'

# Read current settings
with open(settings_file, 'r') as f:
    content = f.read()

# Check if decouple is already imported
if 'from decouple import config' not in content:
    # Add import after existing imports
    import_pattern = r'(from pathlib import Path)'
    replacement = r'\1\nfrom decouple import config'
    content = re.sub(import_pattern, replacement, content)

# Update SECRET_KEY
secret_key_pattern = r"SECRET_KEY = 'django-insecure-.*?'"
if re.search(secret_key_pattern, content):
    content = re.sub(
        secret_key_pattern,
        "SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')",
        content
    )

# Update DEBUG
debug_pattern = r'DEBUG = True'
if re.search(debug_pattern, content):
    content = re.sub(
        debug_pattern,
        "DEBUG = config('DEBUG', default=False, cast=bool)",
        content
    )

# Update ALLOWED_HOSTS
allowed_hosts_pattern = r"ALLOWED_HOSTS = \['localhost', '127.0.0.1'\]"
if re.search(allowed_hosts_pattern, content):
    content = re.sub(
        allowed_hosts_pattern,
        "ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')",
        content
    )

# Update Database configuration
db_pattern = r"# Database - SQLite.*?DATABASES = \{.*?'default': \{.*?\}\s*\}"
db_replacement = """# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='invoice_db'),
        'USER': config('DB_USER', default='invoice_user'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Uncomment below for SQLite (development only):
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }"""

if re.search(r'DATABASES = \{', content):
    # Replace the entire database section
    content = re.sub(
        r'# Database.*?DATABASES = \{.*?\}',
        db_replacement,
        content,
        flags=re.DOTALL
    )

# Update Email Configuration
email_pattern = r"# Email Configuration.*?DEFAULT_FROM_EMAIL = .*?\n"
email_replacement = """# Email Configuration (Zoho SMTP) - credentials from environment variables
EMAIL_BACKEND = 'accounts.email_backend.CustomEmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.zoho.in')
EMAIL_PORT = config('EMAIL_PORT', default=465, cast=int)
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='InvoicePro <noreply@invoicepro.com>')
"""

if re.search(r'# Email Configuration', content):
    content = re.sub(
        r'# Email Configuration.*?DEFAULT_FROM_EMAIL = .*?\n',
        email_replacement,
        content,
        flags=re.DOTALL
    )

# Update STATIC_ROOT and MEDIA_ROOT
static_pattern = r"STATIC_ROOT = BASE_DIR / 'staticfiles'"
if re.search(static_pattern, content):
    content = re.sub(
        static_pattern,
        "STATIC_ROOT = config('STATIC_ROOT', default=BASE_DIR / 'staticfiles')",
        content
    )

media_pattern = r"MEDIA_ROOT = BASE_DIR / 'media'"
if re.search(media_pattern, content):
    content = re.sub(
        media_pattern,
        "MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'media')",
        content
    )

# Write updated content
with open(settings.py, 'w') as f:
    f.write(content)

print("Settings updated for production deployment!")
print("Make sure to install python-decouple: pip install python-decouple")

