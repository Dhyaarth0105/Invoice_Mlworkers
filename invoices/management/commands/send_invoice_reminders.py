"""
Management command to send reminder emails for invoices with approaching due dates
Run this command daily via cron job or scheduled task
"""
import sys
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import date, timedelta
from invoices.models import Invoice, Company

class Command(BaseCommand):
    help = 'Send reminder emails for invoices with approaching due dates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before',
            type=int,
            default=3,
            help='Number of days before due date to send reminder (default: 3)',
        )
        parser.add_argument(
            '--days-after',
            type=int,
            default=0,
            help='Number of days after due date to send reminder for overdue invoices (default: 0)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually sending emails (for testing)',
        )

    def handle(self, *args, **options):
        days_before = options['days_before']
        days_after = options['days_after']
        dry_run = options['dry_run']
        
        today = date.today()
        reminder_date = today + timedelta(days=days_before)
        overdue_date = today - timedelta(days=days_after)
        
        # Find invoices that need reminders
        # 1. Invoices due in X days (not paid, not draft, reminder not sent in last 24 hours)
        upcoming_invoices = Invoice.objects.filter(
            due_date=reminder_date,
            status__in=['PENDING', 'OVERDUE'],
            company__isnull=False,
        ).exclude(
            # Exclude if reminder was sent in last 24 hours
            reminder_sent_at__gte=timezone.now() - timedelta(hours=24)
        ).select_related('company', 'client', 'company__user')
        
        # 2. Overdue invoices (due date passed, not paid)
        overdue_invoices = Invoice.objects.filter(
            due_date__lte=overdue_date,
            status='PENDING',
            company__isnull=False,
        ).exclude(
            # Exclude if reminder was sent in last 24 hours
            reminder_sent_at__gte=timezone.now() - timedelta(hours=24)
        ).select_related('company', 'client', 'company__user')
        
        all_invoices = list(upcoming_invoices) + list(overdue_invoices)
        
        if not all_invoices:
            self.stdout.write(self.style.SUCCESS('No invoices need reminders at this time.'))
            return
        
        self.stdout.write(f'Found {len(all_invoices)} invoice(s) needing reminders.')
        
        sent_count = 0
        error_count = 0
        
        for invoice in all_invoices:
            try:
                # Get the company's user email
                if not invoice.company or not invoice.company.user:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping invoice {invoice.invoice_number}: No company or user found')
                    )
                    continue
                
                user = invoice.company.user
                if not user.email:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping invoice {invoice.invoice_number}: User {user.username} has no email')
                    )
                    continue
                
                # Determine if invoice is overdue or upcoming
                days_until_due = (invoice.due_date - today).days
                is_overdue = days_until_due < 0
                
                # Prepare email context
                host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
                if not host.startswith('http'):
                    host = f"http://{host}"
                invoice_url = f"{host}/invoices/{invoice.pk}/"
                
                context = {
                    'invoice': invoice,
                    'company': invoice.company,
                    'client': invoice.client,
                    'user': user,
                    'days_until_due': abs(days_until_due),
                    'is_overdue': is_overdue,
                    'invoice_url': invoice_url,
                }
                
                # Render email template
                subject = f"Reminder: Invoice {invoice.invoice_number} {'Overdue' if is_overdue else 'Due Soon'}"
                html_message = render_to_string('invoices/email_reminder.html', context)
                plain_message = f"""
Dear {user.get_full_name() or user.username},

This is a reminder that invoice {invoice.invoice_number} for {invoice.client.name} 
is {'OVERDUE' if is_overdue else f'due in {days_until_due} day(s)'}.

Invoice Details:
- Invoice Number: {invoice.invoice_number}
- Client: {invoice.client.name}
- Amount: ₹{invoice.total:,.2f}
- Due Date: {invoice.due_date.strftime('%B %d, %Y')}
- Status: {invoice.get_status_display()}

Please follow up with the client to ensure timely payment.

View Invoice: {context['invoice_url']}

Best regards,
InvoicePro System
"""
                
                if not dry_run:
                    # Send email
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    
                    # Update reminder_sent_at
                    invoice.reminder_sent_at = timezone.now()
                    invoice.save(update_fields=['reminder_sent_at'])
                    
                    # Update status to OVERDUE if due date has passed
                    if is_overdue and invoice.status == 'PENDING':
                        invoice.status = 'OVERDUE'
                        invoice.save(update_fields=['status'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Reminder sent for invoice {invoice.invoice_number} to {user.email}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'[DRY RUN] Would send reminder for invoice {invoice.invoice_number} to {user.email}')
                    )
                
                sent_count += 1
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error sending reminder for invoice {invoice.invoice_number}: {str(e)}')
                )
                if not dry_run:
                    import traceback
                    self.stdout.write(traceback.format_exc())
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n[DRY RUN] Would send {sent_count} reminder(s), {error_count} error(s)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nSent {sent_count} reminder(s), {error_count} error(s)'))

