"""
Script to create admin user and initialize database
Run: python manage.py shell < create_admin.py
Or: python create_admin.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoice_project.settings')
django.setup()

from accounts.models import User
from invoices.models import CompanySettings

# Create admin user
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_user(
        username='admin',
        email='admin@invoicepro.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True
    )
    print(f"✓ Admin user created: username='admin', password='admin123'")
else:
    print("Admin user already exists")

# Initialize company settings
settings = CompanySettings.get_settings()
print(f"✓ Company settings initialized")

print("\nSetup complete!")
print("You can now login with:")
print("  Username: admin")
print("  Password: admin123")


