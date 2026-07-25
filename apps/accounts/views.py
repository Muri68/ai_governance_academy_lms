from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, FormView, TemplateView, View
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from apps.accounts.forms import StudentRegistrationForm, CustomAuthenticationForm
from apps.accounts.models import CustomUser
from datetime import timedelta


class StudentRegistrationView(CreateView):
    form_class = StudentRegistrationForm
    template_name = 'accounts/student/register.html'
    success_url = reverse_lazy('accounts:email_verification_sent')
    
    def form_valid(self, form):
        # Save the user but don't activate
        user = form.save(commit=False)
        user.is_active = False
        user.email_verified = False
        user.save()
        
        # Create student profile
        from apps.accounts.models import StudentProfile
        student_id = f"STU{user.date_joined.strftime('%Y%m%d')}{str(user.id)[:8].upper()}"
        StudentProfile.objects.create(user=user, student_id=student_id)
        
        # Send verification email
        self.send_verification_email(self.request, user)
        
        messages.success(
            self.request,
            f'Registration successful! Please check your email ({user.email}) to verify your account.'
        )
        
        return redirect(self.success_url)
    
    def send_verification_email(self, request, user):
        """Send verification email to user"""
        # Generate verification token
        token = user.generate_verification_token()
        
        # Build verification URL
        verification_url = request.build_absolute_uri(
            reverse('accounts:verify_email', kwargs={'token': token})
        )
        
        # Email context
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'AI Governance Authority',
            'expiry_hours': 48,
        }
        
        # Render email templates
        try:
            html_message = render_to_string('accounts/emails/verify_email.html', context)
            plain_message = strip_tags(html_message)
        except Exception:
            html_message = f"Please verify your email by clicking this link: {verification_url}"
            plain_message = html_message
        
        subject = 'Verify Your Email Address - AI Governance Authority'
        
        # Send email
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


class VerifyEmailView(View):
    """Handle email verification"""
    
    def get(self, request, token):
        try:
            user = CustomUser.objects.get(verification_token=token)
            
            if user.verify_email(token):
                messages.success(
                    request,
                    'Your email has been verified successfully! You can now login to your account.'
                )
                # Auto-login after verification
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                return redirect('accounts:dashboard')
            else:
                messages.error(
                    request,
                    'Invalid or expired verification link. Please request a new verification email.'
                )
        except CustomUser.DoesNotExist:
            messages.error(
                request,
                'Invalid verification link. Please request a new verification email.'
            )
        
        return redirect('accounts:login')


class ResendVerificationEmailView(View):
    """Resend verification email"""
    
    def get(self, request):
        return render(request, 'accounts/resend_verification.html')
    
    def post(self, request):
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'accounts/resend_verification.html')
        
        try:
            user = CustomUser.objects.get(email=email, email_verified=False)
            
            # Check if last verification email was sent less than 5 minutes ago
            if user.verification_token_created:
                time_diff = timezone.now() - user.verification_token_created
                if time_diff < timedelta(minutes=5):
                    messages.warning(
                        request,
                        'Please wait 5 minutes before requesting another verification email.'
                    )
                    return redirect('accounts:login')
            
            # Generate new token and send email
            registration_view = StudentRegistrationView()
            registration_view.send_verification_email(request, user)
            
            messages.success(
                request,
                'Verification email has been resent. Please check your inbox.'
            )
            return redirect('accounts:login')
            
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists or not for security
            messages.info(
                request,
                'If your email is registered and not verified, you will receive a verification email shortly.'
            )
            return redirect('accounts:login')


from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import redirect_to_login
from django.views.generic import FormView
from django.utils import timezone
from .forms import CustomAuthenticationForm
from .models import CustomUser


class CustomLoginView(FormView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('accounts:dashboard')
    
    def get_success_url(self):
        """Get the URL to redirect to after successful login"""
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        
        return super().get_success_url()
    
    def get_context_data(self, **kwargs):
        """Pass the next URL to the template"""
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '')
        return context
    
    def form_valid(self, form):
        user = form.get_user()
        
        # Check if email is verified
        if not user.email_verified:
            resend_url = reverse('accounts:resend_verification')
            messages.error(
                self.request,
                f'Please verify your email address before logging in. '
                f'<a href="{resend_url}" class="alert-link">Click here to resend verification email</a>.',
                extra_tags='safe'
            )
            return render(self.request, self.template_name, self.get_context_data(form=form))
        
        # Check if account is active
        if not user.is_active:
            messages.error(
                self.request,
                'Your account is not active. Please verify your email or contact support.'
            )
            return render(self.request, self.template_name, self.get_context_data(form=form))
        
        # Check if account is locked
        if hasattr(user, 'locked_until') and user.locked_until:
            if user.locked_until > timezone.now():
                remaining_time = (user.locked_until - timezone.now()).seconds // 60
                messages.error(
                    self.request,
                    f'Account is locked. Please try again in {remaining_time} minutes.'
                )
                return render(self.request, self.template_name, self.get_context_data(form=form))
            else:
                user.failed_login_attempts = 0
                user.locked_until = None
                user.save()
        
        # Log the user in
        login(self.request, user)
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save()
        
        messages.success(self.request, f'Welcome back, {user.first_name}!')
        
        return redirect(self.get_success_url())
    
    def form_invalid(self, form):
        email = form.data.get('username', '').strip().lower()
        
        if email:
            try:
                user = CustomUser.objects.get(email=email)
                
                # Check if email is not verified
                if not user.email_verified:
                    resend_url = reverse('accounts:resend_verification')
                    messages.error(
                        self.request,
                        f'Please verify your email address before logging in. '
                        f'<a href="{resend_url}" class="alert-link">Click here to resend verification email</a>.',
                        extra_tags='safe'
                    )
                else:
                    # Increment failed login attempts for valid users
                    user.increment_failed_login()
                    
                    if user.locked_until and user.locked_until > timezone.now():
                        remaining_time = (user.locked_until - timezone.now()).seconds // 60
                        messages.error(
                            self.request,
                            f'Account locked due to too many failed attempts. Please try again in {remaining_time} minutes.'
                        )
                    else:
                        messages.error(self.request, 'Invalid email or password.')
                        
            except CustomUser.DoesNotExist:
                messages.error(self.request, 'Invalid email or password.')
        else:
            messages.error(self.request, 'Please enter your email and password.')
        
        # Return the form with errors
        return render(self.request, self.template_name, self.get_context_data(form=form))
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


class EmailVerificationSentView(TemplateView):
    template_name = 'accounts/email_verification_sent.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['support_email'] = settings.DEFAULT_FROM_EMAIL
        return context


@login_required
def dashboard_redirect(request):
    """Redirect users to their respective dashboards based on user type"""
    # Check if there's a next URL first
    next_url = request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    
    # Otherwise redirect to appropriate dashboard
    if request.user.is_student:
        return redirect('dashboard:student_dashboard')
    elif request.user.is_instructor:
        return redirect('dashboard:instructor_dashboard')
    elif request.user.is_admin_user:
        return redirect('dashboard:admin_dashboard')
    return redirect('frontend:index')


@login_required
def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('frontend:index')