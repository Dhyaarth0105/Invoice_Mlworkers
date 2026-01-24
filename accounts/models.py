from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
import string


class User(AbstractUser):
    """Custom User model - Admin only"""
    
    mobile = models.CharField(max_length=15, blank=True, null=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_full_name() or self.username})"
    
    def get_full_name(self):
        """Return full name or username"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.username


class PasswordResetOTP(models.Model):
    """Store OTP for password reset"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_otp'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp}"
    
    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def is_valid(self):
        """Check if OTP is still valid (within 10 minutes)"""
        from django.conf import settings
        expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        expiry_time = self.created_at + timezone.timedelta(minutes=expiry_minutes)
        return timezone.now() <= expiry_time and not self.is_used
