import stripe
import json
import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from apps.courses.models import Course, Enrollment
from .models import Payment, Coupon

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def checkout_page(request, course_slug):
    """Show checkout page with order summary and terms before payment"""
    course = get_object_or_404(Course, slug=course_slug, status='published')
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course, status='active').exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('frontend:course_learning', slug=course.slug)
    
    # Calculate price
    final_price = float(course.discount_price or course.price)
    discount_amount = float(course.price) - final_price if course.discount_price else 0
    
    context = {
        'course': course,
        'final_price': round(final_price, 2),
        'discount_amount': round(discount_amount, 2),
    }
    return render(request, 'payments/checkout.html', context)


@login_required
def process_checkout(request, course_slug):
    """Process the checkout form and redirect to Stripe"""
    if request.method != 'POST':
        return redirect('payments:checkout', course_slug=course_slug)
    
    course = get_object_or_404(Course, slug=course_slug, status='published')
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course, status='active').exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('frontend:course_learning', slug=course.slug)
    
    # If free course, enroll directly
    if course.is_free:
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            status='active'
        )
        messages.success(request, f'You have been enrolled in {course.title}!')
        return redirect('frontend:course_learning', slug=course.slug)
    
    # Redirect to Stripe checkout
    return redirect('payments:stripe_checkout', course_slug=course.slug)


@login_required
def stripe_checkout(request, course_slug):
    """Create Stripe checkout session for course payment"""
    course = get_object_or_404(Course, slug=course_slug, status='published')
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course, status='active').exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('frontend:course_learning', slug=course.slug)
    
    # Free course - enroll directly
    if course.is_free:
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            status='active'
        )
        messages.success(request, f'You have been enrolled in {course.title}!')
        return redirect('frontend:course_learning', slug=course.slug)
    
    # Get price (use discount if available)
    price = float(course.price)
    if course.discount_price:
        price = float(course.discount_price)
    
    # Convert to cents for Stripe
    amount_in_cents = int(price * 100)
    
    try:
        # Build success and cancel URLs
        success_url = request.build_absolute_uri(
            reverse('payments:payment_success')
        ) + f'?session_id={{CHECKOUT_SESSION_ID}}&course_id={course.id}'
        
        cancel_url = request.build_absolute_uri(
            reverse('payments:checkout', kwargs={'course_slug': course.slug})
        )
        
        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': course.title,
                        'description': course.short_description or f'Enroll in {course.title}',
                        'images': [request.build_absolute_uri(course.featured_image.url)] if course.featured_image else [],
                    },
                    'unit_amount': amount_in_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=request.user.email,
            metadata={
                'user_id': str(request.user.id),
                'course_id': str(course.id),
            }
        )
        
        # Create pending payment record
        Payment.objects.create(
            user=request.user,
            course=course,
            stripe_session_id=checkout_session.id,
            amount=price,
            currency='usd',
            status='pending',
        )
        
        # Redirect to Stripe payment page
        return redirect(checkout_session.url)
        
    except stripe.error.StripeError as e:
        messages.error(request, f'Stripe payment error: {str(e)}')
        return redirect('payments:checkout', course_slug=course.slug)
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('payments:checkout', course_slug=course.slug)


@login_required
def payment_success(request):
    """Handle successful payment return from Stripe"""
    session_id = request.GET.get('session_id')
    course_id = request.GET.get('course_id')
    
    if not session_id or not course_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('frontend:index')
    
    try:
        # Verify the session with Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            course = get_object_or_404(Course, id=course_id)
            
            # Update payment record
            payment = Payment.objects.filter(stripe_session_id=session_id).first()
            if payment:
                payment.stripe_payment_intent_id = session.payment_intent
                payment.status = 'completed'
                payment.receipt_url = f"https://dashboard.stripe.com/payments/{session.payment_intent}"
                payment.save()
            
            # Create or activate enrollment
            enrollment, created = Enrollment.objects.get_or_create(
                student=request.user,
                course=course,
                defaults={'status': 'active'}
            )
            
            if not created and enrollment.status != 'active':
                enrollment.status = 'active'
                enrollment.save()
            
            # Link payment to enrollment
            if payment:
                payment.enrollment = enrollment
                payment.save()
            
            messages.success(request, f'Payment successful! You are now enrolled in "{course.title}". Start learning now!')
            return redirect('frontend:course_learning', slug=course.slug)
        else:
            messages.error(request, 'Payment was not completed. Please try again.')
            course = get_object_or_404(Course, id=course_id)
            return redirect('payments:checkout', course_slug=course.slug)
            
    except stripe.error.StripeError as e:
        messages.error(request, f'Error verifying payment: {str(e)}')
        return redirect('frontend:index')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('frontend:index')


@login_required
def payment_cancel(request):
    """Handle cancelled payment"""
    messages.warning(request, 'Payment was cancelled. You can try again when ready.')
    return redirect('frontend:courses')


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)
    
    # Handle specific events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        handle_expired_session(session)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_failed_payment(payment_intent)
    
    return HttpResponse(status=200)


def handle_successful_payment(session):
    """Process successful payment from webhook"""
    metadata = session.get('metadata', {})
    user_id = metadata.get('user_id')
    course_id = metadata.get('course_id')
    
    if not user_id or not course_id:
        return
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        course = Course.objects.get(id=course_id)
        
        # Update payment record
        payment = Payment.objects.filter(stripe_session_id=session['id']).first()
        if payment and payment.status != 'completed':
            payment.stripe_payment_intent_id = session.get('payment_intent')
            payment.status = 'completed'
            payment.save()
        
        # Create enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={'status': 'active'}
        )
        
        if payment:
            payment.enrollment = enrollment
            payment.save()
            
    except (User.DoesNotExist, Course.DoesNotExist):
        pass


def handle_expired_session(session):
    """Handle expired checkout session"""
    payment = Payment.objects.filter(stripe_session_id=session['id']).first()
    if payment and payment.status == 'pending':
        payment.status = 'failed'
        payment.save()


def handle_failed_payment(payment_intent):
    """Handle failed payment"""
    payment = Payment.objects.filter(
        stripe_payment_intent_id=payment_intent['id']
    ).first()
    if payment:
        payment.status = 'failed'
        payment.save()


@login_required
@csrf_exempt
def validate_coupon(request):
    """AJAX endpoint to validate coupon code"""
    if request.method != 'POST':
        return JsonResponse({'valid': False, 'message': 'Invalid request method.'})
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '').upper().strip()
        course_id = data.get('course_id')
        
        if not code:
            return JsonResponse({'valid': False, 'message': 'Please enter a coupon code.'})
        
        coupon = Coupon.objects.filter(code=code, is_active=True).first()
        
        if not coupon:
            return JsonResponse({'valid': False, 'message': 'Invalid coupon code.'})
        
        if not coupon.is_valid:
            return JsonResponse({'valid': False, 'message': 'Coupon has expired or reached maximum uses.'})
        
        # Check if coupon is for a specific course
        if coupon.course and str(coupon.course.id) != str(course_id):
            return JsonResponse({'valid': False, 'message': 'This coupon is not valid for this course.'})
        
        # Get course price
        course = Course.objects.get(id=course_id)
        price = float(course.discount_price or course.price)
        
        # Check minimum purchase amount
        if price < float(coupon.min_purchase_amount):
            return JsonResponse({
                'valid': False, 
                'message': f'Minimum purchase amount for this coupon is ${coupon.min_purchase_amount}.'
            })
        
        # Calculate discount
        discount = coupon.calculate_discount(price)
        final_price = max(0, price - discount)
        
        return JsonResponse({
            'valid': True,
            'discount': round(discount, 2),
            'final_price': round(final_price, 2),
            'original_price': price,
            'code': coupon.code,
            'message': f'Coupon applied! You save ${round(discount, 2)}.',
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'valid': False, 'message': 'Invalid request data.'})
    except Course.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Course not found.'})
    except Exception as e:
        return JsonResponse({'valid': False, 'message': f'Error: {str(e)}'})


@login_required
def payment_history(request):
    """View payment history for the user"""
    payments = Payment.objects.filter(
        user=request.user
    ).select_related('course').order_by('-created_at')
    
    total_spent = sum(p.amount for p in payments if p.status == 'completed')
    
    context = {
        'payments': payments,
        'total_spent': round(total_spent, 2),
        'completed_count': payments.filter(status='completed').count(),
        'pending_count': payments.filter(status='pending').count(),
        'failed_count': payments.filter(status='failed').count(),
    }
    return render(request, 'payments/history.html', context)