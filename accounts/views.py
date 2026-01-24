from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .forms import LoginForm, SignupForm, ForgotPasswordForm, VerifyOTPForm, ResetPasswordForm
from .models import PasswordResetOTP

User = get_user_model()


def user_login(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('invoices:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('invoices:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def user_signup(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('invoices:dashboard')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created successfully! Welcome, {user.first_name}!')
            login(request, user)
            return redirect('invoices:dashboard')
    else:
        form = SignupForm()
    
    return render(request, 'accounts/signup.html', {'form': form})


def forgot_password(request):
    """Handle forgot password - send OTP"""
    if request.user.is_authenticated:
        return redirect('invoices:dashboard')
    
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            
            # Invalidate any existing OTPs
            PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Generate new OTP
            otp_code = PasswordResetOTP.generate_otp()
            PasswordResetOTP.objects.create(user=user, otp=otp_code)
            
            # Send email with OTP
            subject = 'Password Reset OTP - InvoicePro'
            html_message = render_to_string('accounts/email/otp_email.html', {
                'user': user,
                'otp': otp_code,
                'expiry_minutes': settings.OTP_EXPIRY_MINUTES
            })
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=html_message,
                    fail_silently=False,
                )
                messages.success(request, f'OTP sent to {email}. Please check your inbox.')
                request.session['reset_email'] = email
                return redirect('accounts:verify_otp')
            except Exception as e:
                messages.error(request, f'Failed to send email. Please try again later.')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'accounts/forgot_password.html', {'form': form})


def verify_otp(request):
    """Verify OTP for password reset"""
    if request.user.is_authenticated:
        return redirect('invoices:dashboard')
    
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Please request a password reset first.')
        return redirect('accounts:forgot_password')
    
    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            
            try:
                user = User.objects.get(email=email)
                otp_record = PasswordResetOTP.objects.filter(
                    user=user,
                    otp=otp,
                    is_used=False
                ).latest('created_at')
                
                if otp_record.is_valid():
                    request.session['otp_verified'] = True
                    request.session['otp_id'] = otp_record.id
                    messages.success(request, 'OTP verified! Please set your new password.')
                    return redirect('accounts:reset_password')
                else:
                    messages.error(request, 'OTP has expired. Please request a new one.')
            except PasswordResetOTP.DoesNotExist:
                messages.error(request, 'Invalid OTP. Please try again.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = VerifyOTPForm()
    
    return render(request, 'accounts/verify_otp.html', {'form': form, 'email': email})


def reset_password(request):
    """Reset password after OTP verification"""
    if request.user.is_authenticated:
        return redirect('invoices:dashboard')
    
    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_verified')
    otp_id = request.session.get('otp_id')
    
    if not email or not otp_verified or not otp_id:
        messages.error(request, 'Please verify your OTP first.')
        return redirect('accounts:forgot_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email=email)
                otp_record = PasswordResetOTP.objects.get(id=otp_id)
                
                # Set new password
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                
                # Mark OTP as used
                otp_record.is_used = True
                otp_record.save()
                
                # Clear session data
                del request.session['reset_email']
                del request.session['otp_verified']
                del request.session['otp_id']
                
                messages.success(request, 'Password reset successfully! Please login with your new password.')
                return redirect('accounts:login')
            except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
                messages.error(request, 'An error occurred. Please try again.')
                return redirect('accounts:forgot_password')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'accounts/reset_password.html', {'form': form})


def resend_otp(request):
    """Resend OTP"""
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Please request a password reset first.')
        return redirect('accounts:forgot_password')
    
    try:
        user = User.objects.get(email=email)
        
        # Invalidate existing OTPs
        PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new OTP
        otp_code = PasswordResetOTP.generate_otp()
        PasswordResetOTP.objects.create(user=user, otp=otp_code)
        
        # Send email
        subject = 'Password Reset OTP - InvoicePro'
        html_message = render_to_string('accounts/email/otp_email.html', {
            'user': user,
            'otp': otp_code,
            'expiry_minutes': settings.OTP_EXPIRY_MINUTES
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=False,
        )
        messages.success(request, f'New OTP sent to {email}.')
    except Exception as e:
        messages.error(request, 'Failed to send OTP. Please try again.')
    
    return redirect('accounts:verify_otp')


@login_required
def user_logout(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')
