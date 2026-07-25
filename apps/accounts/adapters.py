from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


class CustomAccountAdapter(DefaultAccountAdapter):
    
    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.
        """
        if request.user.is_student:
            return reverse('dashboard:student_dashboard')
        elif request.user.is_instructor:
            return reverse('dashboard:instructor_dashboard')
        elif request.user.is_admin_user:
            return reverse('dashboard:admin_dashboard')
        return reverse('frontend:index')
    
    def get_signup_redirect_url(self, request):
        """
        Returns the default URL to redirect to after signing up.
        """
        # After signup, redirect to email verification sent page
        return reverse('accounts:email_verification_sent')
    
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Override to send custom verification email.
        """
        current_site = self.get_current_site(request)
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        
        ctx = {
            'user': emailconfirmation.email_address.user,
            'activate_url': activate_url,
            'current_site': current_site,
            'key': emailconfirmation.key,
        }
        
        if signup:
            email_template = 'accounts/emails/email_confirmation_signup'
        else:
            email_template = 'accounts/emails/email_confirmation'
        
        self.send_mail(
            email_template,
            emailconfirmation.email_address.email,
            ctx
        )
    
    def send_mail(self, template_prefix, email, context):
        """
        Send email with HTML template.
        """
        subject = render_to_string(f'{template_prefix}_subject.txt', context)
        # Remove superfluous line breaks
        subject = " ".join(subject.splitlines()).strip()
        subject = self.format_email_subject(subject)
        
        # Render HTML email
        html_message = render_to_string(f'{template_prefix}_message.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=False,
        )
    
    def respond_email_verification_sent(self, request, user):
        """
        Respond after email verification is sent.
        """
        messages.success(
            request,
            f'Verification email sent to {user.email}. Please check your inbox and spam folder.'
        )
        return redirect('accounts:email_verification_sent')
    
    def login(self, request, user):
        """
        Override to prevent login if email is not verified.
        """
        if not user.email_verified:
            messages.error(
                request,
                'Please verify your email address before logging in. '
                'Check your inbox for the verification link.'
            )
            return redirect('accounts:login')
        return super().login(request, user)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Returns the default URL to redirect to after connecting a social account.
        """
        return reverse('accounts:dashboard')
    
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed.
        """
        # Social accounts are automatically verified
        if sociallogin.is_existing:
            return
        
        # For new social accounts, mark email as verified
        email = sociallogin.account.extra_data.get('email')
        if email:
            try:
                from .models import CustomUser
                user = CustomUser.objects.get(email=email)
                if not user.email_verified:
                    user.email_verified = True
                    user.is_verified = True
                    user.is_active = True
                    user.save()
            except CustomUser.DoesNotExist:
                pass
    
    def populate_user(self, request, sociallogin, data):
        """
        Hook that can be used to further populate the user instance.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Set user type based on some logic or default to student
        if not user.user_type:
            user.user_type = 'STUDENT'
        
        # Social auth users are pre-verified
        user.email_verified = True
        user.is_active = True
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user and create the appropriate profile.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Create StudentProfile for users signing up via social auth
        if user.user_type == 'STUDENT':
            from .models import StudentProfile
            
            if not hasattr(user, 'student_profile'):
                student_id = f"STU{user.date_joined.strftime('%Y%m%d')}{str(user.id)[:8].upper()}"
                StudentProfile.objects.create(user=user, student_id=student_id)
        
        return user