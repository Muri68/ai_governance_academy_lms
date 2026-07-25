from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('register/', views.StudentRegistrationView.as_view(), name='student_register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    
    # Email Verification URLs
    path('verify-email/<str:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('email-verification-sent/', views.EmailVerificationSentView.as_view(), name='email_verification_sent'),
    path('resend-verification/', views.ResendVerificationEmailView.as_view(), name='resend_verification'),
    
    # django-allauth URLs
    # path('social/', include('allauth.socialaccount.urls')),
]