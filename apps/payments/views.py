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
from django.core.mail import send_mail, EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.core.mail import EmailMessage
from apps.courses.models import Course, Enrollment
from apps.dashboard.models import SiteSetting
from .models import Payment, Coupon

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_site_settings_for_email():
    """Get site settings for email templates"""
    settings_dict = {}
    for s in SiteSetting.objects.all():
        settings_dict[s.key] = s.value
    
    return {
        'site_name': settings_dict.get('site_name', 'AI GOVERNANCE ACADEMY'),
        'site_tagline': settings_dict.get('site_tagline', 'AI Ethics & Compliance Platform'),
        'contact_email': settings_dict.get('contact_email', 'info@aiga.ac'),
        'contact_phone': settings_dict.get('contact_phone', ''),
        'office_address': settings_dict.get('office_address', '128 City Road, London, United Kingdom, EC1V 2NX'),
        'primary_color': settings_dict.get('primary_color', '#ad7a49'),
        'facebook_url': settings_dict.get('facebook_url', '#'),
        'twitter_url': settings_dict.get('twitter_url', '#'),
        'linkedin_url': settings_dict.get('linkedin_url', '#'),
        'instagram_url': settings_dict.get('instagram_url', '#'),
        'youtube_url': settings_dict.get('youtube_url', '#'),
    }


def send_payment_success_email(user, course, payment):
    """Send professional payment success email - SIMPLIFIED VERSION"""
    try:
        site_settings = get_site_settings_for_email()
        
        subject = f'Payment Confirmation - {course.title}'
        
        # Simple plain text email first to ensure delivery
        plain_message = f"""
Dear {user.get_full_name() or user.username},

Your payment has been successfully processed for {course.title}.

Amount Paid: £{payment.amount if payment else 0}
Date: {timezone.now().strftime('%B %d, %Y')}

You are now enrolled in this course. You can access it from your dashboard.

If you have any questions, please contact us at {site_settings.get('contact_email', 'info@aiga.ac')}.

Thank you,
{site_settings.get('site_name', 'AI GOVERNANCE ACADEMY')}
        """
        
        # Try to send HTML email
        try:
            context = {
                'user': user,
                'course': course,
                'payment': payment,
                'date': timezone.now(),
                **site_settings,
            }
            
            html_message = render_to_string('payments/emails/payment_success.html', context)
            
            # Send with both plain text and HTML
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)  # Set to False to see errors
            
            print(f"✅ Payment success email sent to {user.email}")
            
        except Exception as template_error:
            print(f"HTML email failed, sending plain text: {str(template_error)}")
            
            # Fallback to plain text email
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            print(f"✅ Plain text payment email sent to {user.email}")
        
    except Exception as e:
        print(f"❌ Email sending failed completely: {str(e)}")
        # Try one more time with minimal settings
        try:
            send_mail(
                f'Payment Confirmation - {course.title}',
                f'Your payment for {course.title} was successful.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            print(f"✅ Minimal email sent to {user.email}")
        except Exception as final_error:
            print(f"❌ All email attempts failed: {str(final_error)}")


def send_payment_failed_email(user, course, reason="Payment failed"):
    """Send payment failure notification email - SIMPLIFIED VERSION"""
    try:
        site_settings = get_site_settings_for_email()
        
        subject = f'Payment Unsuccessful - {course.title}'
        
        plain_message = f"""
Dear {user.get_full_name() or user.username},

Your payment for {course.title} was unsuccessful.

Reason: {reason}

No charges have been made to your account. You can try again at any time.

If you need assistance, please contact us at {site_settings.get('contact_email', 'info@aiga.ac')}.

Thank you,
{site_settings.get('site_name', 'AI GOVERNANCE ACADEMY')}
        """
        
        # Try HTML email
        try:
            context = {
                'user': user,
                'course': course,
                'reason': reason,
                'date': timezone.now(),
                **site_settings,
            }
            
            html_message = render_to_string('payments/emails/payment_failed.html', context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            print(f"✅ Payment failed email sent to {user.email}")
            
        except Exception as template_error:
            print(f"HTML email failed, sending plain text: {str(template_error)}")
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            print(f"✅ Plain text failed email sent to {user.email}")
        
    except Exception as e:
        print(f"❌ Failed email sending failed: {str(e)}")


def send_payment_refund_email(user, course, payment, refund_amount):
    """Send refund confirmation email - SIMPLIFIED VERSION"""
    try:
        site_settings = get_site_settings_for_email()
        
        subject = f'Refund Processed - {course.title}'
        
        plain_message = f"""
Dear {user.get_full_name() or user.username},

A refund has been processed for your payment for {course.title}.

Refund Amount: £{refund_amount}
Date: {timezone.now().strftime('%B %d, %Y')}

The refund will appear in your account within 5-10 business days.

If you have any questions, please contact us at {site_settings.get('contact_email', 'info@aiga.ac')}.

Thank you,
{site_settings.get('site_name', 'AI GOVERNANCE ACADEMY')}
        """
        
        # Try HTML email
        try:
            context = {
                'user': user,
                'course': course,
                'payment': payment,
                'refund_amount': refund_amount,
                'date': timezone.now(),
                **site_settings,
            }
            
            html_message = render_to_string('payments/emails/payment_refund.html', context)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            print(f"✅ Refund email sent to {user.email}")
            
        except Exception as template_error:
            print(f"HTML email failed, sending plain text: {str(template_error)}")
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            print(f"✅ Plain text refund email sent to {user.email}")
        
    except Exception as e:
        print(f"❌ Refund email sending failed: {str(e)}")


def payment_success(request):
    """Handle successful payment return from Stripe - NO login required"""
    session_id = request.GET.get('session_id')
    course_id = request.GET.get('course_id')
    
    print(f"🔍 Payment success page loaded - Session: {session_id}, Course: {course_id}")
    
    if not session_id or not course_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('frontend:index')
    
    course = None
    payment = None
    enrollment = None
    
    try:
        # Get course
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            course = None
        
        # Retrieve Stripe session to verify payment
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            payment_status = session.get('payment_status')
            print(f"🔍 Stripe payment status: {payment_status}")
            
            # Get user from metadata
            metadata = session.get('metadata', {})
            user_id = metadata.get('user_id')
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    user = request.user if request.user.is_authenticated else None
            else:
                user = request.user if request.user.is_authenticated else None
            
            # Process payment if status is paid
            if payment_status == 'paid' and user:
                payment = Payment.objects.filter(stripe_session_id=session_id).first()
                if payment:
                    if payment.status != 'completed':
                        payment.status = 'completed'
                        payment.stripe_payment_intent_id = session.get('payment_intent')
                        payment.save()
                        print(f"✅ Payment {payment.id} updated to completed")
                else:
                    payment = Payment.objects.create(
                        user=user,
                        course=course,
                        stripe_session_id=session_id,
                        stripe_payment_intent_id=session.get('payment_intent'),
                        amount=float(course.discount_price or course.price) if course else 0,
                        currency='gbp',
                        status='completed',
                        payment_method='card',
                    )
                    print(f"✅ Payment created for session {session_id}")
                
                # Create enrollment
                if course and user:
                    enrollment, created = Enrollment.objects.get_or_create(
                        student=user,
                        course=course,
                        defaults={'status': 'active'}
                    )
                    
                    if not created and enrollment.status != 'active':
                        enrollment.status = 'active'
                        enrollment.save()
                    
                    if payment:
                        payment.enrollment = enrollment
                        payment.save()
                    
                    print(f"✅ Enrollment created/updated for user {user.id} in course {course.id}")
                    
                    # Send email only if not already sent
                    if not payment.receipt_url:  # Use receipt_url as flag for email sent
                        send_payment_success_email(user, course, payment)
                        payment.receipt_url = session.get('receipt_url', '')
                        payment.save()
                        print(f"✅ Success email sent")
                
                messages.success(request, f'Payment successful! You are now enrolled in "{course.title}".')
            else:
                messages.warning(request, 'Your payment is being processed. You will be notified by email once confirmed.')
                
        except stripe.error.StripeError as e:
            print(f"❌ Stripe error: {str(e)}")
            messages.info(request, 'Payment verification in progress. Please check your email.')
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            messages.info(request, 'Payment verification in progress. Please check your email.')
        
    except Exception as e:
        import traceback
        print("=== PAYMENT SUCCESS ERROR ===")
        print(traceback.format_exc())
        print("============================")
        messages.info(request, 'Payment verification in progress. Please check your email.')
    
    return render(request, 'payments/payment_success.html', {
        'course': course,
        'payment': payment,
        'enrollment': enrollment,
    })


@login_required
def checkout_page(request, course_slug):
    """Show checkout page with order summary and terms before payment"""
    course = get_object_or_404(Course, slug=course_slug, status='published')
    
    if Enrollment.objects.filter(student=request.user, course=course, status='active').exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('accounts:dashboard')
    
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
    
    if Enrollment.objects.filter(student=request.user, course=course, status='active').exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('accounts:dashboard')
    
    if course.is_free:
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            status='active'
        )
        
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            amount=0,
            currency='gbp',
            status='completed',
            payment_method='free',
            enrollment=enrollment,
        )
        
        send_payment_success_email(request.user, course, payment)
        
        messages.success(request, f'You have been enrolled in {course.title}!')
        return redirect('accounts:dashboard')
    
    return redirect('payments:stripe_checkout', course_slug=course.slug)


@login_required
def stripe_checkout(request, course_slug):
    """Create Stripe checkout session for course payment"""
    course = get_object_or_404(Course, slug=course_slug, status='published')
    
    if Enrollment.objects.filter(student=request.user, course=course, status='active').exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('accounts:dashboard')
    
    if course.is_free:
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            status='active'
        )
        messages.success(request, f'You have been enrolled in {course.title}!')
        return redirect('accounts:dashboard')
    
    price = float(course.price)
    if course.discount_price:
        price = float(course.discount_price)
    
    amount_in_pence = int(price * 100)
    
    try:
        success_url = request.build_absolute_uri(
            reverse('payments:payment_success')
        ) + f'?session_id={{CHECKOUT_SESSION_ID}}&course_id={course.id}'
        
        cancel_url = request.build_absolute_uri(
            reverse('payments:payment_cancel')
        ) + f'?course_slug={course.slug}'
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': course.title,
                        'description': course.short_description or f'Enroll in {course.title}',
                    },
                    'unit_amount': amount_in_pence,
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
                'user_email': request.user.email,
            }
        )
        
        Payment.objects.create(
            user=request.user,
            course=course,
            stripe_session_id=checkout_session.id,
            amount=price,
            currency='gbp',
            status='pending',
        )
        
        return redirect(checkout_session.url)
        
    except stripe.error.CardError as e:
        send_payment_failed_email(request.user, course, str(e.error.message))
        messages.error(request, f'Your card was declined: {e.error.message}')
        return redirect('payments:checkout', course_slug=course.slug)
    except stripe.error.StripeError as e:
        send_payment_failed_email(request.user, course, str(e))
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('payments:checkout', course_slug=course.slug)
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('payments:checkout', course_slug=course.slug)


@login_required
def payment_cancel(request):
    """Handle cancelled payment"""
    messages.warning(request, 'Payment was cancelled. No charges have been made.')
    
    course = None
    course_slug = request.GET.get('course_slug')
    if course_slug:
        try:
            course = Course.objects.get(slug=course_slug)
            
            Payment.objects.filter(
                user=request.user,
                course=course,
                status='pending'
            ).update(status='cancelled')
            
            send_payment_failed_email(
                request.user, 
                course, 
                "Payment was cancelled by user"
            )
            
        except Course.DoesNotExist:
            pass
    
    return render(request, 'payments/payment_cancel.html', {
        'course': course,
    })


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    
    # Add detailed logging
    if not sig_header:
        print("❌ No Stripe signature header found")
        return HttpResponse(status=400)
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        print(f"✅ Webhook received: {event['type']}")
    except ValueError as e:
        print(f"❌ Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        print(f"❌ Invalid signature: {str(e)}")
        return HttpResponse(status=400)
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return HttpResponse(status=400)
    
    # Handle different event types
    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            print(f"📦 Processing checkout.session.completed for session {session['id']}")
            print(f"📦 Payment status: {session.get('payment_status')}")
            print(f"📦 Metadata: {session.get('metadata', {})}")
            
            # Process regardless of payment_status - Stripe only sends this when paid
            handle_successful_payment(session)
            
        elif event['type'] == 'checkout.session.async_payment_succeeded':
            session = event['data']['object']
            print(f"📦 Processing async_payment_succeeded for session {session['id']}")
            handle_successful_payment(session)
            
        elif event['type'] == 'checkout.session.async_payment_failed':
            session = event['data']['object']
            handle_failed_payment_from_session(session)
            
        elif event['type'] == 'checkout.session.expired':
            session = event['data']['object']
            handle_expired_session(session)
            
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            handle_failed_payment(payment_intent)
            
        elif event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            handle_payment_intent_succeeded(payment_intent)
            
        elif event['type'] == 'charge.refunded':
            charge = event['data']['object']
            handle_refunded_payment(charge)
            
        elif event['type'] == 'charge.dispute.created':
            dispute = event['data']['object']
            handle_dispute_created(dispute)
            
        elif event['type'] == 'payment_intent.canceled':
            payment_intent = event['data']['object']
            handle_payment_canceled(payment_intent)
        
        print(f"✅ Successfully processed: {event['type']}")
        
    except Exception as e:
        print(f"❌ Error processing webhook event {event['type']}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Always return 200 to acknowledge receipt
    return HttpResponse(status=200)


def handle_successful_payment(session):
    """Process successful payment from webhook"""
    print(f"🔍 Processing successful payment for session: {session['id']}")
    
    metadata = session.get('metadata', {})
    user_id = metadata.get('user_id')
    course_id = metadata.get('course_id')
    
    print(f"🔍 Metadata - user_id: {user_id}, course_id: {course_id}")
    
    # If no metadata, try to find by session ID
    if not user_id or not course_id:
        print("❌ No metadata found, trying to find payment by session ID")
        payment = Payment.objects.filter(stripe_session_id=session['id']).first()
        if payment:
            user_id = payment.user_id
            course_id = payment.course_id
            print(f"✅ Found payment - user_id: {user_id}, course_id: {course_id}")
        else:
            print("❌ No payment found for session")
            return
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        course = Course.objects.get(id=course_id)
        
        print(f"✅ User found: {user.email}")
        print(f"✅ Course found: {course.title}")
        
        # Get or create payment
        payment = Payment.objects.filter(stripe_session_id=session['id']).first()
        if payment:
            print(f"✅ Existing payment found: ID={payment.id}, Status={payment.status}")
            if payment.status != 'completed':
                payment.stripe_payment_intent_id = session.get('payment_intent')
                payment.status = 'completed'
                payment.save()
                print(f"✅ Payment updated to completed")
        else:
            # Create payment if it doesn't exist
            payment = Payment.objects.create(
                user=user,
                course=course,
                stripe_session_id=session['id'],
                stripe_payment_intent_id=session.get('payment_intent'),
                amount=float(course.discount_price or course.price),
                currency='gbp',
                status='completed',
                payment_method='card',
            )
            print(f"✅ New payment created: ID={payment.id}")
        
        # Create or update enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={'status': 'active'}
        )
        
        if created:
            print(f"✅ New enrollment created: ID={enrollment.id}")
        else:
            print(f"✅ Existing enrollment found: ID={enrollment.id}, Status={enrollment.status}")
            if enrollment.status != 'active':
                enrollment.status = 'active'
                enrollment.save()
                print(f"✅ Enrollment updated to active")
        
        # Link payment to enrollment
        if payment and enrollment:
            payment.enrollment = enrollment
            payment.save()
            print(f"✅ Payment linked to enrollment")
        
        # Send success email
        send_payment_success_email(user, course, payment)
        print(f"✅ Success email sent to {user.email}")
        
    except User.DoesNotExist:
        print(f"❌ User {user_id} not found")
    except Course.DoesNotExist:
        print(f"❌ Course {course_id} not found")
    except Exception as e:
        print(f"❌ Error in handle_successful_payment: {str(e)}")
        import traceback
        traceback.print_exc()


def handle_failed_payment_from_session(session):
    """Handle async payment failure from checkout session"""
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
        
        payment = Payment.objects.filter(stripe_session_id=session['id']).first()
        if payment:
            payment.status = 'failed'
            payment.save()
            send_payment_failed_email(user, course, "Payment failed during processing")
            print(f"✅ Payment {payment.id} marked as failed")
            
    except (User.DoesNotExist, Course.DoesNotExist):
        pass
    except Exception as e:
        print(f"Error in handle_failed_payment_from_session: {str(e)}")


def handle_expired_session(session):
    """Handle expired checkout session"""
    payment = Payment.objects.filter(stripe_session_id=session['id']).first()
    if payment and payment.status == 'pending':
        payment.status = 'expired'
        payment.save()
        send_payment_failed_email(payment.user, payment.course, "Payment session expired")
        print(f"✅ Payment {payment.id} marked as expired")


def handle_failed_payment(payment_intent):
    """Handle failed payment"""
    payment = Payment.objects.filter(
        stripe_payment_intent_id=payment_intent['id']
    ).first()
    
    if payment:
        payment.status = 'failed'
        payment.save()
        error_message = payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
        send_payment_failed_email(payment.user, payment.course, error_message)
        print(f"✅ Payment {payment.id} marked as failed")
    else:
        # Try to find by session ID from metadata
        session_id = payment_intent.get('metadata', {}).get('checkout_session_id')
        if session_id:
            payment = Payment.objects.filter(stripe_session_id=session_id).first()
            if payment:
                payment.status = 'failed'
                payment.stripe_payment_intent_id = payment_intent['id']
                payment.save()
                error_message = payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
                send_payment_failed_email(payment.user, payment.course, error_message)
                print(f"✅ Payment {payment.id} marked as failed (by session ID)")


def handle_payment_intent_succeeded(payment_intent):
    """Handle successful payment intent"""
    # Try to find payment by payment intent ID first
    payment = Payment.objects.filter(
        stripe_payment_intent_id=payment_intent['id']
    ).first()
    
    # If not found, try to find by session ID from metadata
    if not payment:
        session_id = payment_intent.get('metadata', {}).get('checkout_session_id')
        if session_id:
            payment = Payment.objects.filter(stripe_session_id=session_id).first()
    
    if payment and payment.status != 'completed':
        payment.status = 'completed'
        payment.stripe_payment_intent_id = payment_intent['id']
        payment.save()
        
        # Create or update enrollment
        if payment.course and payment.user:
            enrollment, created = Enrollment.objects.get_or_create(
                student=payment.user,
                course=payment.course,
                defaults={'status': 'active'}
            )
            
            if not created and enrollment.status != 'active':
                enrollment.status = 'active'
                enrollment.save()
            
            payment.enrollment = enrollment
            payment.save()
            
            send_payment_success_email(payment.user, payment.course, payment)
            print(f"✅ Payment {payment.id} marked as completed (from payment intent)")


def handle_refunded_payment(charge):
    """Handle refunded payment"""
    payment_intent_id = charge.get('payment_intent')
    if payment_intent_id:
        payment = Payment.objects.filter(
            stripe_payment_intent_id=payment_intent_id
        ).first()
        
        if payment:
            refund_amount = float(charge.get('amount_refunded', 0)) / 100
            payment.status = 'refunded'
            payment.refund_amount = refund_amount
            payment.refunded_at = timezone.now()
            payment.save()
            
            if payment.enrollment:
                payment.enrollment.status = 'inactive'
                payment.enrollment.save()
            
            send_payment_refund_email(payment.user, payment.course, payment, refund_amount)
            print(f"✅ Payment {payment.id} marked as refunded")


def handle_dispute_created(dispute):
    """Handle payment dispute created"""
    charge_id = dispute.get('charge')
    if charge_id:
        try:
            charge = stripe.Charge.retrieve(charge_id)
            payment_intent_id = charge.get('payment_intent')
            
            if payment_intent_id:
                payment = Payment.objects.filter(
                    stripe_payment_intent_id=payment_intent_id
                ).first()
                
                if payment:
                    payment.status = 'disputed'
                    payment.dispute_reason = dispute.get('reason', '')
                    payment.save()
                    
                    site_settings = get_site_settings_for_email()
                    subject = f'Payment Dispute - {payment.course.title}'
                    message = f'Payment {payment.id} has been disputed.'
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [site_settings.get('contact_email', 'info@aiga.ac')],
                        fail_silently=True,
                    )
                    print(f"✅ Payment {payment.id} marked as disputed")
        except stripe.error.StripeError as e:
            print(f"Error handling dispute: {str(e)}")


def handle_payment_canceled(payment_intent):
    """Handle payment intent canceled"""
    payment = Payment.objects.filter(
        stripe_payment_intent_id=payment_intent['id']
    ).first()
    
    if payment and payment.status == 'pending':
        payment.status = 'cancelled'
        payment.save()
        print(f"✅ Payment {payment.id} marked as cancelled")


@login_required
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
        
        if coupon.course and str(coupon.course.id) != str(course_id):
            return JsonResponse({'valid': False, 'message': 'This coupon is not valid for this course.'})
        
        course = Course.objects.get(id=course_id)
        price = float(course.discount_price or course.price)
        
        if price < float(coupon.min_purchase_amount):
            return JsonResponse({
                'valid': False, 
                'message': f'Minimum purchase amount for this coupon is £{coupon.min_purchase_amount}.'
            })
        
        discount = coupon.calculate_discount(price)
        final_price = max(0, price - discount)
        
        return JsonResponse({
            'valid': True,
            'discount': round(discount, 2),
            'final_price': round(final_price, 2),
            'original_price': price,
            'code': coupon.code,
            'message': f'Coupon applied! You save £{round(discount, 2)}.',
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