from django.http import HttpResponse
from django.shortcuts import render
from django.core.mail import send_mail

from django.conf import settings

# Create your views here.
def test_email(request):
    """Test if email sending works"""
    try:
        send_mail(
            'Test Email from AI Governance Academy',
            'This is a test email to verify email configuration.',
            settings.DEFAULT_FROM_EMAIL,
            ['muriisyaku68@gmail.com'],  # Change to your email
            fail_silently=False,
        )
        return HttpResponse('Email sent successfully! Check your inbox.')
    except Exception as e:
        return HttpResponse(f'Email failed: {str(e)}')