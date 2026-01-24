# Generated migration

from django.db import migrations


def create_default_uoms(apps, schema_editor):
    UOM = apps.get_model('invoices', 'UOM')
    default_uoms = [
        {'name': 'Units', 'code': 'UN', 'description': 'Units'},
        {'name': 'Hours', 'code': 'HR', 'description': 'Hours'},
        {'name': 'Days', 'code': 'DY', 'description': 'Days'},
        {'name': 'Months', 'code': 'MO', 'description': 'Months'},
        {'name': 'Licenses', 'code': 'LIC', 'description': 'Licenses'},
        {'name': 'Instances', 'code': 'INS', 'description': 'Instances'},
        {'name': 'Kg', 'code': 'KG', 'description': 'Kilograms'},
        {'name': 'Lot', 'code': 'LOT', 'description': 'Lot'},
    ]
    for uom_data in default_uoms:
        UOM.objects.get_or_create(name=uom_data['name'], defaults=uom_data)


def reverse_default_uoms(apps, schema_editor):
    UOM = apps.get_model('invoices', 'UOM')
    UOM.objects.filter(name__in=['Units', 'Hours', 'Days', 'Months', 'Licenses', 'Instances', 'Kg', 'Lot']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0002_uom_purchaseorder_price_alter_purchaseorder_uom'),
    ]

    operations = [
        migrations.RunPython(create_default_uoms, reverse_default_uoms),
    ]
