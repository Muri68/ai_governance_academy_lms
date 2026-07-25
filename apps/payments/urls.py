from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Checkout page (shows terms & order summary)
    path('checkout/<slug:course_slug>/', views.checkout_page, name='checkout'),
    # Process and redirect to Stripe
    path('process/<slug:course_slug>/', views.process_checkout, name='process_checkout'),
    # Stripe checkout session
    path('stripe/<slug:course_slug>/', views.stripe_checkout, name='stripe_checkout'),
    # Success return
    path('success/', views.payment_success, name='payment_success'),
    # Webhook
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    # Coupon validation
    path('validate-coupon/', views.validate_coupon, name='validate_coupon'),
    # Payment history
    path('student/history/', views.payment_history, name='payment_history'),
]