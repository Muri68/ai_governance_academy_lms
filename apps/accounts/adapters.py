from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.core.files.base import ContentFile
import requests
from urllib.parse import urlparse
import os


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
        subject = " ".join(subject.splitlines()).strip()
        subject = self.format_email_subject(subject)
        
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
        if sociallogin.is_existing:
            return
        
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
        
        if not user.user_type:
            user.user_type = 'STUDENT'
        
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
        
        # Try to save profile picture
        self.save_profile_picture(user, sociallogin)
        
        return user
    
    def save_profile_picture(self, user, sociallogin):
        """
        Download and save profile picture from social account.
        """
        try:
            # Print all extra data for debugging
            print(f"Provider: {sociallogin.account.provider}")
            print(f"Extra data keys: {sociallogin.account.extra_data.keys()}")
            
            picture_url = None
            
            if sociallogin.account.provider == 'google':
                # Try different possible keys for Google
                picture_url = sociallogin.account.extra_data.get('picture')
                if not picture_url:
                    picture_url = sociallogin.account.extra_data.get('image', {}).get('url')
                
                print(f"Google picture URL: {picture_url}")
                
            elif sociallogin.account.provider == 'facebook':
                # Try to get Facebook picture
                picture_data = sociallogin.account.extra_data.get('picture')
                print(f"Facebook picture data type: {type(picture_data)}")
                print(f"Facebook picture data: {picture_data}")
                
                if isinstance(picture_data, dict):
                    picture_url = picture_data.get('data', {}).get('url')
                elif isinstance(picture_data, str):
                    picture_url = picture_data
            
            if picture_url:
                # Download the image
                print(f"Downloading from: {picture_url}")
                response = requests.get(picture_url)
                
                if response.status_code == 200:
                    # Get file extension from URL or default to jpg
                    parsed_url = urlparse(picture_url)
                    ext = os.path.splitext(parsed_url.path)[1]
                    if not ext:
                        ext = '.jpg'
                    
                    # Create filename
                    file_name = f"social_avatar_{user.id}{ext}"
                    
                    # Save the image
                    user.profile_picture.save(
                        file_name,
                        ContentFile(response.content),
                        save=True
                    )
                    print(f"Successfully saved profile picture to: {user.profile_picture.path}")
                else:
                    print(f"Failed to download image. Status code: {response.status_code}")
            else:
                print("No picture URL found in extra data")
                
        except Exception as e:
            print(f"Error saving profile picture: {str(e)}")
            import traceback
            traceback.print_exc()