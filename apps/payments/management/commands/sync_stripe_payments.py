from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.payments.models import Payment
from apps.courses.models import Course, Enrollment
import stripe
from django.conf import settings
from datetime import datetime, timedelta

stripe.api_key = settings.STRIPE_SECRET_KEY

User = get_user_model()


class Command(BaseCommand):
    help = 'Sync pending payments with Stripe to update their status'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Check payments from the last N hours (default: 24)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Check all pending payments regardless of time'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        check_all = options['all']
        
        self.stdout.write(self.style.SUCCESS('🔄 Starting Stripe payment sync...'))
        
        # Get pending payments
        if check_all:
            pending_payments = Payment.objects.filter(status='pending')
            self.stdout.write('Checking ALL pending payments')
        else:
            time_threshold = timezone.now() - timedelta(hours=hours)
            pending_payments = Payment.objects.filter(
                status='pending',
                created_at__gte=time_threshold
            )
            self.stdout.write(f'Checking pending payments from last {hours} hours')
        
        self.stdout.write(f'Found {pending_payments.count()} pending payments')
        
        updated_count = 0
        failed_count = 0
        error_count = 0
        
        for payment in pending_payments:
            self.stdout.write(f'\n--- Processing Payment {payment.id} ---')
            self.stdout.write(f'User: {payment.user.email}')
            self.stdout.write(f'Course: {payment.course.title if payment.course else "N/A"}')
            self.stdout.write(f'Amount: £{payment.amount}')
            self.stdout.write(f'Created: {payment.created_at}')
            
            # Try to find the Stripe session
            session = None
            
            # Method 1: Check by session ID
            if payment.stripe_session_id:
                try:
                    session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
                    self.stdout.write(f'Found session: {session.id}')
                except stripe.error.StripeError as e:
                    self.stdout.write(f'Could not retrieve session: {str(e)}')
            
            # Method 2: If no session found, search recent checkout sessions
            if not session:
                try:
                    # Search for recent checkout sessions for this user
                    sessions = stripe.checkout.Session.list(
                        limit=10,
                        customer_email=payment.user.email,
                        created={'gte': int((payment.created_at - timedelta(hours=2)).timestamp())}
                    )
                    
                    for s in sessions.data:  # Note: .data to get list
                        # Check if this session matches our payment
                        session_metadata = s.metadata or {}
                        if str(session_metadata.get('user_id')) == str(payment.user.id) and \
                           str(session_metadata.get('course_id')) == str(payment.course.id):
                            session = s
                            self.stdout.write(f'Found matching session: {session.id}')
                            break
                except stripe.error.StripeError as e:
                    self.stdout.write(f'Error searching sessions: {str(e)}')
            
            # Process the session if found
            if session:
                # Use attribute access instead of .get()
                payment_status = session.payment_status if hasattr(session, 'payment_status') else None
                self.stdout.write(f'Stripe payment status: {payment_status}')
                
                if payment_status == 'paid':
                    try:
                        # Update payment
                        payment.status = 'completed'
                        if session.payment_intent:
                            payment.stripe_payment_intent_id = session.payment_intent
                        if hasattr(session, 'receipt_url') and session.receipt_url:
                            payment.receipt_url = session.receipt_url
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
                            
                            self.stdout.write(self.style.SUCCESS(
                                f'✅ Payment {payment.id} marked as completed'
                            ))
                            self.stdout.write(self.style.SUCCESS(
                                f'✅ Enrollment {"created" if created else "updated"} for {payment.user.email}'
                            ))
                            
                            # Try to send email
                            try:
                                from apps.payments.views import send_payment_success_email
                                send_payment_success_email(payment.user, payment.course, payment)
                                self.stdout.write(self.style.SUCCESS('✅ Success email sent'))
                            except Exception as e:
                                self.stdout.write(f'⚠️ Could not send email: {str(e)}')
                            
                            updated_count += 1
                        else:
                            self.stdout.write(self.style.WARNING('⚠️ Missing course or user for payment'))
                    
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(self.style.ERROR(f'❌ Error updating payment: {str(e)}'))
                
                elif payment_status == 'unpaid' or payment_status is None:
                    # Check payment intent
                    payment_intent_id = session.payment_intent if hasattr(session, 'payment_intent') else None
                    
                    if payment_intent_id:
                        try:
                            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                            if payment_intent.status == 'succeeded':
                                # Payment succeeded
                                payment.status = 'completed'
                                payment.stripe_payment_intent_id = payment_intent.id
                                payment.save()
                                
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
                                    
                                    self.stdout.write(self.style.SUCCESS(
                                        f'✅ Payment {payment.id} marked as completed (from payment intent)'
                                    ))
                                    
                                    try:
                                        from apps.payments.views import send_payment_success_email
                                        send_payment_success_email(payment.user, payment.course, payment)
                                        self.stdout.write(self.style.SUCCESS('✅ Success email sent'))
                                    except Exception as e:
                                        self.stdout.write(f'⚠️ Could not send email: {str(e)}')
                                    
                                    updated_count += 1
                            else:
                                # Payment failed
                                payment.status = 'failed'
                                payment.save()
                                failed_count += 1
                                self.stdout.write(self.style.WARNING(
                                    f'⚠️ Payment {payment.id} marked as failed'
                                ))
                        except stripe.error.StripeError as e:
                            self.stdout.write(f'Error retrieving payment intent: {str(e)}')
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'⚠️ Payment {payment.id} has no payment intent'
                        ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'⚠️ No Stripe session found for payment {payment.id}'
                ))
                
                # Check if payment is too old (more than 24 hours)
                if payment.created_at < timezone.now() - timedelta(hours=24):
                    payment.status = 'expired'
                    payment.save()
                    self.stdout.write(self.style.WARNING(
                        f'⚠️ Payment {payment.id} marked as expired (older than 24 hours)'
                    ))
                    failed_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✅ Sync completed!'))
        self.stdout.write(f'Updated to completed: {updated_count}')
        self.stdout.write(f'Marked as failed/expired: {failed_count}')
        self.stdout.write(f'Errors encountered: {error_count}')
        self.stdout.write('='*50)