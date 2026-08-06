from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.utils.crypto import get_random_string
from django.db.models import Count, Q
from apps.accounts.decorators import admin_required
from apps.accounts.models import CustomUser, InstructorProfile, StudentProfile, AdminProfile
from apps.accounts.forms import InstructorCreationForm
import string
import json
from apps.courses.models import Course, FeaturedCourse, TopPick, CourseCategory, Lesson, LessonContent, Enrollment, CourseReview


from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncMonth
from django.template.loader import render_to_string


import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.utils.crypto import get_random_string
from django.db.models import Count, Q, Avg, Sum
from django.db.models.functions import TruncMonth
from apps.accounts.decorators import admin_required
from apps.accounts.models import CustomUser, InstructorProfile, StudentProfile, AdminProfile
from apps.accounts.forms import InstructorCreationForm
from apps.courses.models import Course, CourseCategory, Lesson, LessonContent, Enrollment, CourseReview
from apps.payments.models import Payment
from apps.frontend.models import SiteReview
import string
import uuid
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from apps.dashboard.models import SiteSetting, SiteFileSetting, FAQ
import os


def _get_course(course_id):
    """Helper to get course by UUID or integer ID"""
    try:
        uid = uuid.UUID(str(course_id))
        return get_object_or_404(Course, id=uid)
    except (ValueError, AttributeError):
        return get_object_or_404(Course, id=int(course_id))


@login_required
@admin_required
@never_cache
def admin_dashboard(request):
    """Admin dashboard with real stats and revenue"""
    
    # Basic counts
    total_students = CustomUser.objects.filter(user_type='STUDENT').count()
    total_instructors = CustomUser.objects.filter(user_type='INSTRUCTOR').count()
    total_admins = CustomUser.objects.filter(user_type='ADMIN').count()
    total_courses = Course.objects.filter(status='published').count()
    total_draft_courses = Course.objects.filter(status='draft').count()
    total_archived_courses = Course.objects.filter(status='archived').count()
    active_enrollments = Enrollment.objects.filter(status='active').count()
    completed_enrollments = Enrollment.objects.filter(status='completed').count()
    
    # Top courses - count only ACTIVE enrollments
    top_courses = Course.objects.filter(status='published').annotate(
        enrollment_count=Count('enrollments', filter=Q(enrollments__status='active')),
        avg_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews')
    ).order_by('-enrollment_count')[:3]
    
    # Top instructors by students
    top_instructors = CustomUser.objects.filter(
        user_type='INSTRUCTOR', is_active=True
    ).annotate(
        course_count=Count('teaching_courses', filter=Q(teaching_courses__status='published')),
        student_count=Count('teaching_courses__enrollments', filter=Q(teaching_courses__enrollments__status='active'), distinct=True),
        avg_rating=Avg('teaching_courses__reviews__rating')
    ).filter(course_count__gt=0).order_by('-student_count')[:4]
    
    # Popular courses with completion rate
    popular_courses = Course.objects.filter(status='published').annotate(
        enrollment_count=Count('enrollments', filter=Q(enrollments__status='active')),
        completed_count=Count('enrollments', filter=Q(enrollments__status='completed')),
        avg_progress=Avg('enrollments__progress_percentage')
    ).order_by('-enrollment_count')[:4]
    
    # Revenue from actual payments
    total_revenue = float(
        Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
    )
    
    # This month's revenue
    now = timezone.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_revenue = float(
        Payment.objects.filter(
            status='completed',
            created_at__gte=this_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
    )
    
    # Last month's revenue
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    last_month_revenue = float(
        Payment.objects.filter(
            status='completed',
            created_at__gte=last_month_start,
            created_at__lt=this_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
    )
    
    # Revenue growth percentage
    if last_month_revenue > 0:
        revenue_growth = round(((this_month_revenue - last_month_revenue) / last_month_revenue) * 100, 1)
    else:
        revenue_growth = 100 if this_month_revenue > 0 else 0
    
    # Total paid enrollments
    total_paid_enrollments = Payment.objects.filter(status='completed').values('user').distinct().count()
    
    # Pending payments
    pending_payments = Payment.objects.filter(status='pending').count()
    
    # Refunded payments
    refunded_amount = float(
        Payment.objects.filter(status='refunded').aggregate(
            total=Sum('amount')
        )['total'] or 0
    )
    
    # New this month
    new_students_this_month = CustomUser.objects.filter(
        user_type='STUDENT', 
        date_joined__gte=this_month_start
    ).count()
    
    new_instructors_this_month = CustomUser.objects.filter(
        user_type='INSTRUCTOR', 
        date_joined__gte=this_month_start
    ).count()
    
    new_courses_this_month = Course.objects.filter(
        status='published',
        published_at__gte=this_month_start
    ).count()
    
    # Recent enrollments
    recent_enrollments = Enrollment.objects.filter(
        status='active'
    ).select_related('student', 'course').order_by('-enrolled_at')[:5]
    
    # Chart data - last 6 months
    chart_labels = []
    chart_enrollments = []
    chart_revenue = []
    
    for i in range(5, -1, -1):
        month_date = now.replace(day=1) - timedelta(days=i * 30)
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1)
        
        chart_labels.append(month_start.strftime('%b'))
        
        # Monthly enrollments
        count = Enrollment.objects.filter(
            enrolled_at__gte=month_start, 
            enrolled_at__lt=month_end
        ).count()
        chart_enrollments.append(count)
        
        # Monthly revenue from actual payments
        rev = float(
            Payment.objects.filter(
                status='completed',
                created_at__gte=month_start,
                created_at__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
        )
        chart_revenue.append(round(rev, 2))
    
    chart_data = {
        'labels': chart_labels,
        'enrollments': chart_enrollments,
        'revenue': chart_revenue,
    }
    
    # Category distribution
    category_distribution = CourseCategory.objects.filter(is_active=True).annotate(
        course_count=Count('courses', filter=Q(courses__status='published'))
    ).filter(course_count__gt=0).order_by('-course_count')[:6]
    
    context = {
        # Totals
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_admins': total_admins,
        'total_courses': total_courses,
        'total_draft_courses': total_draft_courses,
        'total_archived_courses': total_archived_courses,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        
        # Revenue
        'total_revenue': round(total_revenue, 2),
        'this_month_revenue': round(this_month_revenue, 2),
        'last_month_revenue': round(last_month_revenue, 2),
        'revenue_growth': revenue_growth,
        'total_paid_enrollments': total_paid_enrollments,
        'pending_payments': pending_payments,
        'refunded_amount': round(refunded_amount, 2),
        
        # Top lists
        'top_courses': top_courses,
        'top_instructors': top_instructors,
        'popular_courses': popular_courses,
        'category_distribution': category_distribution,
        
        # New this month
        'new_students_this_month': new_students_this_month,
        'new_instructors_this_month': new_instructors_this_month,
        'new_courses_this_month': new_courses_this_month,
        
        # Recent activity
        'recent_enrollments': recent_enrollments,
        
        # Chart
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'dashboard/admin/dashboard.html', context)


@login_required
@admin_required
def admin_profile(request):
    # Get or create admin profile
    profile, created = AdminProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.bio = request.POST.get('bio', user.bio)
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        
        # Handle signature upload
        if 'signature' in request.FILES:
            # Delete old signature if exists
            if profile.signature:
                profile.signature.delete(save=False)
            profile.signature = request.FILES['signature']
            messages.success(request, 'Program Director signature uploaded successfully!')
        
        # Handle signature removal
        if request.POST.get('remove_signature') == 'true':
            if profile.signature:
                profile.signature.delete(save=False)
                profile.signature = None
                messages.info(request, 'Signature removed.')
        
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard:admin_profile')
    
    context = {
        'user': request.user,
        'profile': profile,
    }
    return render(request, 'dashboard/admin/profile.html', context)


@login_required
@admin_required
def admin_change_password(request):
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard:admin_profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    
    return render(request, 'dashboard/admin/change_password.html')


@login_required
@admin_required
def create_instructor(request):
    if request.method == 'POST':
        form = InstructorCreationForm(request.POST)
        if form.is_valid():
            user, password = form.save()
            
            subject = 'Your Instructor Account - AI Governance Academy LTD'
            message = f'''
Dear {user.get_full_name()},

Your instructor account has been created.

Login Email: {user.email}
Password: {password}

Please login and change your password:
{request.build_absolute_uri('/accounts/login/')}

Best regards,
AI Governance Academy Team
'''
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                messages.success(request, f'Instructor account created for {user.email}.')
            except Exception as e:
                messages.warning(request, f'Account created but email failed. Password: {password}')
            
            return redirect('dashboard:admin_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InstructorCreationForm()
    
    return render(request, 'dashboard/admin/create_instructor.html', {'form': form})


@login_required
@admin_required
def create_admin(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        if not all([email, first_name, last_name]):
            messages.error(request, 'All fields are required.')
            return render(request, 'dashboard/admin/create_admin.html')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'dashboard/admin/create_admin.html')
        
        characters = string.ascii_letters + string.digits + "!@#$%^&*()"
        password = get_random_string(length=12, allowed_chars=characters)
        
        try:
            user = CustomUser.objects.create_user(
                email=email, password=password,
                first_name=first_name.title(), last_name=last_name.title(),
                user_type='ADMIN', is_staff=True, is_superuser=True,
                email_verified=True, is_active=True
            )
            
            admin_id = f"ADM{user.date_joined.strftime('%Y%m%d')}{str(user.id)[:8].upper()}"
            AdminProfile.objects.create(user=user, admin_id=admin_id, access_level=1)
            
            subject = 'Your Admin Account - AI Governance Academy LTD'
            message = f'''
Dear {user.get_full_name()},

Your admin account has been created.

Login Email: {user.email}
Password: {password}

Please login and change your password:
{request.build_absolute_uri('/accounts/login/')}

Best regards,
AI Governance Academy Team
'''
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                messages.success(request, f'Admin account created for {user.email}.')
            except Exception:
                messages.warning(request, f'Admin account created. Password: {password}')
            
            return redirect('dashboard:admin_dashboard')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'dashboard/admin/create_admin.html')


@login_required
@admin_required
def manage_users(request):
    users = CustomUser.objects.all().select_related(
        'student_profile', 'instructor_profile', 'admin_profile'
    ).order_by('-date_joined')
    
    context = {
        'users': users,
        'total_users': users.count(),
        'total_students': users.filter(user_type='STUDENT').count(),
        'total_instructors': users.filter(user_type='INSTRUCTOR').count(),
        'total_admins': users.filter(user_type='ADMIN').count(),
    }
    return render(request, 'dashboard/admin/users.html', context)


@login_required
@admin_required
def add_user(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        user_type = request.POST.get('user_type', '')
        is_active = request.POST.get('is_active', 'true') == 'true'
        send_credentials = request.POST.get('send_email') == 'on'
        bio = request.POST.get('bio', '').strip()
        phone = request.POST.get('phone', '').strip()
        profile_picture = request.FILES.get('profile_picture')
        
        if not all([email, first_name, last_name, user_type]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'dashboard/admin/add_user.html')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, f'A user with email {email} already exists.')
            return render(request, 'dashboard/admin/add_user.html')
        
        characters = string.ascii_letters + string.digits + "!@#$%^&*()"
        password = get_random_string(length=12, allowed_chars=characters)
        
        try:
            user = CustomUser.objects.create_user(
                email=email, password=password,
                first_name=first_name.title(), last_name=last_name.title(),
                user_type=user_type, is_active=is_active,
                email_verified=True, bio=bio,
            )
            
            if profile_picture:
                user.profile_picture = profile_picture
            user.save()
            
            # Create role-specific profile
            if user_type == 'STUDENT':
                student_id = f"STU{user.date_joined.strftime('%Y%m%d')}{str(user.id)[:8].upper()}"
                enrollment_date = request.POST.get('enrollment_date') or None
                StudentProfile.objects.create(user=user, student_id=student_id, enrollment_date=enrollment_date)
                
            elif user_type == 'INSTRUCTOR':
                instructor_id = f"INS{user.date_joined.strftime('%Y%m%d')}{str(user.id)[:8].upper()}"
                InstructorProfile.objects.create(
                    user=user, instructor_id=instructor_id,
                    department=request.POST.get('department', ''),
                    qualification=request.POST.get('qualification', ''),
                    expertise=request.POST.get('expertise', ''),
                    is_approved=True
                )
                
            elif user_type == 'ADMIN':
                admin_id = f"ADM{user.date_joined.strftime('%Y%m%d')}{str(user.id)[:8].upper()}"
                access_level = int(request.POST.get('access_level', 1))
                AdminProfile.objects.create(user=user, admin_id=admin_id, access_level=access_level)
                user.is_staff = True
                if access_level >= 3:
                    user.is_superuser = True
                user.save()
            
            # Send email if checkbox is checked
            if send_credentials:
                role_display = dict(CustomUser.UserType.choices)[user_type]
                
                # Build email context
                email_context = {
                    'user': user,
                    'password': password,
                    'role': role_display,
                    'login_url': request.build_absolute_uri('/accounts/login/'),
                    'site_url': request.build_absolute_uri('/'),
                }
                
                # Try to render template
                try:
                    html_message = render_to_string('emails/welcome_email.html', email_context)
                    plain_message = f'''
WELCOME TO AI GOVERNANCE ACADEMY

Dear {user.get_full_name()},

Your {role_display.lower()} account has been created.

LOGIN CREDENTIALS:
Email: {user.email}
Password: {password}

Please change your password after your first login.

Login here: {request.build_absolute_uri('/accounts/login/')}

Need help? Contact us at support@aiga.com
'''
                except Exception as template_error:
                    # Fallback if template not found
                    print(f"Template error: {template_error}")
                    html_message = None
                    plain_message = f'''
WELCOME TO AI GOVERNANCE ACADEMY

Dear {user.get_full_name()},

Your {role_display.lower()} account has been created.

LOGIN CREDENTIALS:
Email: {user.email}
Password: {password}

Please change your password after your first login.

Login here: {request.build_absolute_uri('/accounts/login/')}
'''
                
                subject = f'Welcome to AI Governance Academy - Your {role_display} Account'
                
                try:
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    messages.success(request, f'{role_display} account created! Login credentials sent to {user.email}.')
                except Exception as email_error:
                    print(f"Email send error: {email_error}")
                    messages.warning(request, f'Account created but email failed to send. Password: {password}')
            else:
                messages.success(request, f'{role_display} account created successfully!')
            
            return redirect('dashboard:manage_users')
            
        except Exception as e:
            print(f"User creation error: {e}")
            messages.error(request, f'Error creating user: {str(e)}')
    
    return render(request, 'dashboard/admin/add_user.html')


@login_required
@admin_required
def manage_instructors(request):
    """Display all instructors with their course and student counts"""
    from apps.courses.models import Course, Enrollment
    from django.db.models import Count, Q, Sum, Avg, OuterRef, Subquery
    
    instructors = CustomUser.objects.filter(
        user_type='INSTRUCTOR'
    ).select_related('instructor_profile').order_by('-date_joined')
    
    # Manually calculate counts for each instructor (more accurate)
    for instructor in instructors:
        # Count published courses
        instructor.course_count = Course.objects.filter(
            instructor=instructor,
            status='published'
        ).count()
        
        # Count unique active students across all courses
        instructor.total_students = Enrollment.objects.filter(
            course__instructor=instructor,
            course__status='published',
            status='active'
        ).values('student').distinct().count()
        
        # Calculate average rating
        avg = Course.objects.filter(
            instructor=instructor,
            status='published'
        ).aggregate(avg=Avg('reviews__rating'))['avg']
        instructor.avg_rating = round(avg, 1) if avg else None
    
    # Top rated
    top_rated_value = 4.8
    rated_instructors = [i for i in instructors if i.avg_rating]
    if rated_instructors:
        top_rated_value = max(i.avg_rating for i in rated_instructors)
    
    context = {
        'instructors': instructors,
        'total_instructors': instructors.count(),
        'active_instructors': instructors.filter(is_active=True).count(),
        'inactive_instructors': instructors.filter(is_active=False).count(),
        'top_rated': top_rated_value,
    }
    return render(request, 'dashboard/admin/instructors.html', context)


@login_required
@admin_required
def toggle_user_status(request, user_id):
    """Toggle user active/inactive status"""
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.email} has been {status}.')
    
    # Redirect back to the referring page
    referer = request.META.get('HTTP_REFERER', '')
    if 'instructors' in referer:
        return redirect('dashboard:manage_instructors')
    return redirect('dashboard:manage_users')


# ===================== COURSE MANAGEMENT VIEWS =====================
import json
from django.utils import timezone
from apps.courses.models import Course, CourseCategory, Lesson, LessonContent

@login_required
@admin_required
def manage_courses(request):
    """Display all courses with filters"""
    courses = Course.objects.select_related(
        'instructor', 'category'
    ).prefetch_related('enrollments', 'reviews').order_by('-created_at')
    
    context = {
        'courses': courses,
        'total_courses': courses.count(),
        'published_courses': courses.filter(status='published').count(),
        'draft_courses': courses.filter(status='draft').count(),
        'archived_courses': courses.filter(status='archived').count(),
    }
    return render(request, 'dashboard/admin/courses.html', context)


@login_required
@admin_required
def add_course(request):
    """Admin adds a new course with lessons and content"""
    if request.method == 'POST':
        return _admin_save_course(request, is_edit=False)
    
    instructors = CustomUser.objects.filter(user_type='INSTRUCTOR', is_active=True)
    context = {
        'instructors': instructors,
        'is_edit': False,
    }
    return render(request, 'dashboard/admin/add_course.html', context)


@login_required
@admin_required
def edit_course(request, course_id):
    """Admin edits an existing course"""
    course = _get_course(course_id)
    
    if request.method == 'POST':
        return _admin_save_course(request, is_edit=True, course=course)
    
    # Prepare existing lessons data
    existing_lessons = []
    for lesson in course.lessons.all().order_by('order'):
        lesson_data = {
            'id': lesson.id,
            'title': lesson.title,
            'contents': []
        }
        for content in lesson.contents.all().order_by('order'):
            lesson_data['contents'].append({
                'id': content.id,
                'type': content.content_type,
                'title': content.title or '',
                'duration': content.duration_minutes or '',
                'video_url': content.video_url or '',
                'text_content': content.text_content or '',
            })
        existing_lessons.append(lesson_data)
    
    instructors = CustomUser.objects.filter(user_type='INSTRUCTOR', is_active=True)
    
    context = {
        'course': course,
        'instructors': instructors,
        'existing_lessons_json': json.dumps(existing_lessons),
        'is_edit': True,
    }
    return render(request, 'dashboard/admin/add_course.html', context)


def _admin_save_course(request, is_edit=False, course=None):
    """Handle course creation/update logic for admin"""
    title = request.POST.get('title', '').strip()
    category_slug = request.POST.get('category', '')
    description = request.POST.get('description', '').strip()
    short_description = request.POST.get('short_description', '').strip()
    duration = request.POST.get('duration', '').strip()
    level = request.POST.get('level', 'beginner')
    price_str = request.POST.get('price', '0').strip()
    discount_price_str = request.POST.get('discount_price', '').strip()
    status = request.POST.get('status', 'draft')
    language = request.POST.get('language', 'English')
    requirements = request.POST.get('requirements', '').strip()
    what_you_learn = request.POST.get('what_you_learn', '').strip()
    has_certificate = request.POST.get('has_certificate') == 'on'
    is_free = request.POST.get('is_free') == 'on'
    trailer_url = request.POST.get('trailer_url', '').strip()
    instructor_id = request.POST.get('instructor', '')
    thumbnail = request.FILES.get('thumbnail')
    featured_video = request.FILES.get('featured_video')
    lessons_data_str = request.POST.get('lessons_data', '[]')
    
    try:
        lessons_data = json.loads(lessons_data_str)
    except json.JSONDecodeError:
        lessons_data = []
    
    if not title:
        messages.error(request, 'Course title is required.')
        if is_edit and course:
            return redirect('dashboard:edit_course', course_id=course.id)
        return redirect('dashboard:add_course')
    
    # Parse price
    if is_free:
        price = 0
    else:
        try:
            price = float(price_str.replace('$', '').replace(',', ''))
        except (ValueError, TypeError):
            price = 0
    
    discount_price = None
    if discount_price_str:
        try:
            discount_price = float(discount_price_str.replace('$', '').replace(',', ''))
        except (ValueError, TypeError):
            discount_price = None
    
    # Get instructor
    instructor = request.user  # Default to admin
    if instructor_id:
        try:
            instructor = CustomUser.objects.get(id=instructor_id)
        except CustomUser.DoesNotExist:
            pass
    
    # Get or create category
    category = None
    if category_slug:
        category, _ = CourseCategory.objects.get_or_create(
            slug=category_slug,
            defaults={'name': category_slug.replace('-', ' ').title()}
        )
    
    if is_edit and course:
        # UPDATE existing course
        course.title = title
        course.instructor = instructor
        course.category = category
        course.description = description
        course.short_description = short_description
        course.duration = duration
        course.level = level
        course.price = price
        course.discount_price = discount_price
        course.is_free = is_free
        course.status = status
        course.language = language
        course.requirements = requirements
        course.what_you_learn = what_you_learn
        course.has_certificate = has_certificate
        course.trailer_url = trailer_url
        
        if thumbnail:
            course.featured_image = thumbnail
        if featured_video:
            course.featured_video = featured_video
        
        course.save()
        
        # UPDATE lessons - preserve IDs for existing, create new ones
        _admin_update_lessons(request, course, lessons_data)
        
        messages.success(request, f'Course "{course.title}" updated successfully!')
        return redirect('dashboard:edit_course', course_id=course.id)
    
    else:
        # CREATE new course
        course = Course.objects.create(
            title=title,
            instructor=instructor,
            category=category,
            description=description,
            short_description=short_description,
            duration=duration,
            level=level,
            price=price,
            discount_price=discount_price,
            is_free=is_free,
            status=status,
            language=language,
            requirements=requirements,
            what_you_learn=what_you_learn,
            has_certificate=has_certificate,
            trailer_url=trailer_url,
            featured_image=thumbnail,
            featured_video=featured_video,
        )
        
        # Create lessons
        _admin_create_lessons(request, course, lessons_data)
        
        messages.success(request, f'Course "{course.title}" created successfully!')
        return redirect('dashboard:manage_courses')


def _admin_update_lessons(request, course, lessons_data):
    """UPDATE existing lessons - preserve IDs, update content"""
    existing_lesson_ids = set(course.lessons.values_list('id', flat=True))
    updated_lesson_ids = set()
    
    for i, lesson_data in enumerate(lessons_data):
        lesson_id = lesson_data.get('id')
        lesson_title = lesson_data.get('title', f'Lesson {i+1}')
        
        if not lesson_title:
            continue
        
        if lesson_id and lesson_id in existing_lesson_ids:
            # UPDATE existing lesson
            lesson = Lesson.objects.get(id=lesson_id, course=course)
            lesson.title = lesson_title
            lesson.order = i + 1
            lesson.save()
        else:
            # CREATE new lesson
            lesson = Lesson.objects.create(
                course=course,
                title=lesson_title,
                order=i + 1,
            )
        
        updated_lesson_ids.add(lesson.id)
        
        # Update contents for this lesson
        _admin_update_contents(request, lesson, lesson_data.get('contents', []), i)
    
    # DELETE lessons that were removed
    lessons_to_delete = existing_lesson_ids - updated_lesson_ids
    if lessons_to_delete:
        Lesson.objects.filter(id__in=lessons_to_delete).delete()


def _admin_update_contents(request, lesson, contents_data, lesson_index):
    """UPDATE existing contents - preserve IDs, update content"""
    existing_content_ids = set(lesson.contents.values_list('id', flat=True))
    updated_content_ids = set()
    
    for j, content_data in enumerate(contents_data):
        content_id = content_data.get('id')
        content_type = content_data.get('type', 'text')
        content_title = content_data.get('title', '')
        duration_str = content_data.get('duration', '')
        video_url = content_data.get('video_url', '')
        text_content = content_data.get('text_content', '')
        
        duration_minutes = None
        if duration_str and str(duration_str).strip().isdigit():
            duration_minutes = int(str(duration_str).strip())
        
        if content_id and content_id in existing_content_ids:
            # UPDATE existing content
            content = LessonContent.objects.get(id=content_id, lesson=lesson)
            content.content_type = content_type
            content.title = content_title
            content.duration_minutes = duration_minutes
            content.video_url = video_url if content_type in ['video', 'video_url'] else ''
            content.text_content = text_content if content_type in ['text', 'quiz', 'assignment', 'code'] else ''
            content.order = j + 1
            content.save()
        else:
            # CREATE new content
            content = LessonContent.objects.create(
                lesson=lesson,
                content_type=content_type,
                title=content_title,
                duration_minutes=duration_minutes,
                video_url=video_url if content_type in ['video', 'video_url'] else '',
                text_content=text_content if content_type in ['text', 'quiz', 'assignment', 'code'] else '',
                order=j + 1,
            )
        
        updated_content_ids.add(content.id)
        
        # Handle NEW file uploads only
        file_field_name = f'lesson_content_file_{lesson_index}_{j}'
        if file_field_name in request.FILES:
            uploaded_file = request.FILES[file_field_name]
            if content_type == 'video':
                content.video_file = uploaded_file
            elif content_type == 'pdf':
                content.pdf_file = uploaded_file
            elif content_type == 'slides':
                content.pdf_file = uploaded_file
            content.save()
    
    # DELETE contents that were removed
    contents_to_delete = existing_content_ids - updated_content_ids
    if contents_to_delete:
        LessonContent.objects.filter(id__in=contents_to_delete).delete()


def _admin_create_lessons(request, course, lessons_data):
    """Create lessons and contents for new courses"""
    for i, lesson_data in enumerate(lessons_data):
        lesson_title = lesson_data.get('title', f'Lesson {i+1}')
        if not lesson_title:
            continue
        
        lesson = Lesson.objects.create(
            course=course,
            title=lesson_title,
            order=i + 1,
        )
        
        for j, content_data in enumerate(lesson_data.get('contents', [])):
            content_type = content_data.get('type', 'text')
            content_title = content_data.get('title', '')
            duration_str = content_data.get('duration', '')
            video_url = content_data.get('video_url', '')
            text_content = content_data.get('text_content', '')
            
            duration_minutes = None
            if duration_str and str(duration_str).strip().isdigit():
                duration_minutes = int(str(duration_str).strip())
            
            content = LessonContent.objects.create(
                lesson=lesson,
                content_type=content_type,
                title=content_title,
                duration_minutes=duration_minutes,
                video_url=video_url if content_type in ['video', 'video_url'] else '',
                text_content=text_content if content_type in ['text', 'quiz', 'assignment', 'code'] else '',
                order=j + 1,
            )
            
            # Handle file uploads
            file_field_name = f'lesson_content_file_{i}_{j}'
            if file_field_name in request.FILES:
                uploaded_file = request.FILES[file_field_name]
                if content_type == 'video':
                    content.video_file = uploaded_file
                elif content_type == 'pdf':
                    content.pdf_file = uploaded_file
                elif content_type == 'slides':
                    content.pdf_file = uploaded_file
                content.save()


@login_required
@admin_required
def admin_course_view(request, course_id):
    """Admin view for a single course details"""
    course = get_object_or_404(
        Course.objects.select_related('instructor', 'category')
        .prefetch_related('lessons__contents', 'enrollments', 'reviews'),
        id=course_id
    )
    
    context = {
        'course': course,
        'lessons': course.lessons.filter(is_published=True).order_by('order'),
        'total_students': course.total_students,
        'average_rating': course.average_rating,
        'review_count': course.review_count,
    }
    return render(request, 'dashboard/admin/course_view.html', context)


@login_required
@admin_required
def update_course_status(request, course_id):
    """AJAX: Update course status (any admin can change status of any course)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
        except (json.JSONDecodeError, AttributeError):
            new_status = request.POST.get('status')
        
        if new_status in ['draft', 'review', 'published', 'archived']:
            course = get_object_or_404(Course, id=course_id)
            course.status = new_status
            if new_status == 'published' and not course.published_at:
                course.published_at = timezone.now()
            course.save()
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
@admin_required
def delete_course(request, course_id):
    """Delete course - only course owner or superuser can delete"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        if course.instructor == request.user or request.user.is_superuser:
            course.delete()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    return JsonResponse({'status': 'error'}, status=400)



@login_required
@admin_required
def course_students(request, course_id):
    """View all students enrolled in a specific course"""
    from apps.courses.models import Course, Enrollment
    
    course = _get_course(course_id)
    
    enrollments = Enrollment.objects.filter(
        course=course
    ).select_related(
        'student', 'student__student_profile'
    ).order_by('-enrolled_at')
    
    total_enrolled = enrollments.count()
    active_students = enrollments.filter(status='active').count()
    completed_students = enrollments.filter(status='completed').count()
    dropped_students = enrollments.filter(status='dropped').count()
    
    context = {
        'course': course,
        'enrollments': enrollments,
        'total_enrolled': total_enrolled,
        'active_students': active_students,
        'completed_students': completed_students,
        'dropped_students': dropped_students,
    }
    return render(request, 'dashboard/admin/course_students.html', context)


@login_required
@admin_required
def instructor_detail(request, user_id):
    """Detailed view of an instructor with all stats"""
    from apps.courses.models import Course, Enrollment, CourseReview
    from django.db.models import Count, Q, Avg
    
    instructor = get_object_or_404(
        CustomUser.objects.select_related('instructor_profile'),
        id=user_id, user_type='INSTRUCTOR'
    )
    
    courses = Course.objects.filter(
        instructor=instructor
    ).annotate(
        student_count=Count('enrollments', filter=Q(enrollments__status='active')),
        completed_count=Count('enrollments', filter=Q(enrollments__status='completed')),
        avg_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews')  # Renamed from review_count to total_reviews
    ).order_by('-created_at')
    
    total_earnings = 0
    paid_courses = 0
    free_courses = 0
    
    for course in courses:
        if course.is_free:
            free_courses += 1
        else:
            paid_courses += 1
            active_count = course.enrollments.filter(status='active').count()
            total_earnings += float(course.price) * active_count
    
    total_students = Enrollment.objects.filter(
        course__instructor=instructor, status='active'
    ).values('student').distinct().count()
    
    total_reviews = CourseReview.objects.filter(course__instructor=instructor).count()
    avg_rating = courses.aggregate(avg=Avg('reviews__rating'))['avg'] or 0
    
    context = {
        'instructor': instructor,
        'courses': courses,
        'total_courses': courses.count(),
        'paid_courses': paid_courses,
        'free_courses': free_courses,
        'total_earnings': round(total_earnings, 2),
        'total_students': total_students,
        'total_reviews': total_reviews,
        'average_rating': round(avg_rating, 1),
    }
    return render(request, 'dashboard/admin/instructor_detail.html', context)


@login_required
@admin_required
def student_detail(request, user_id):
    """Detailed view of a student with enrollment stats"""
    student = get_object_or_404(
        CustomUser.objects.select_related('student_profile'),
        id=user_id, user_type='STUDENT'
    )
    
    enrollments = Enrollment.objects.filter(
        student=student
    ).select_related('course__instructor', 'course__category').order_by('-enrolled_at')
    
    total_spent = 0
    paid_enrollments = 0
    free_enrollments = 0
    completed_courses = 0
    
    for enrollment in enrollments:
        if enrollment.course.is_free:
            free_enrollments += 1
        else:
            paid_enrollments += 1
            if enrollment.status == 'active':
                total_spent += float(enrollment.course.price)
        if enrollment.status == 'completed':
            completed_courses += 1
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'total_enrolled': enrollments.count(),
        'active_enrollments': enrollments.filter(status='active').count(),
        'completed_courses': completed_courses,
        'paid_enrollments': paid_enrollments,
        'free_enrollments': free_enrollments,
        'total_spent': round(total_spent, 2),
    }
    return render(request, 'dashboard/admin/student_detail.html', context)



@login_required
@admin_required
def admin_payments(request):
    """Admin view: See all payments across the platform"""
    from apps.payments.models import Payment
    from django.db.models import Sum, Count, Q
    
    payments = Payment.objects.select_related(
        'user', 'course', 'enrollment'
    ).order_by('-created_at')
    
    # Stats
    total_revenue = payments.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    context = {
        'payments': payments,
        'total_payments': payments.count(),
        'completed_payments': payments.filter(status='completed').count(),
        'pending_payments': payments.filter(status='pending').count(),
        'failed_payments': payments.filter(status='failed').count(),
        'refunded_payments': payments.filter(status='refunded').count(),
        'total_revenue': round(total_revenue, 2),
    }
    return render(request, 'dashboard/admin/payments.html', context)



@login_required
@admin_required
def admin_enrollments(request):
    """Admin view: See all course enrollments"""
    from apps.courses.models import Enrollment, Course
    from django.db.models import Count, Q
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    course_filter = request.GET.get('course', '')
    search_query = request.GET.get('search', '')
    
    enrollments = Enrollment.objects.select_related(
        'student', 'student__student_profile', 'course', 'course__instructor'
    ).prefetch_related('progress').order_by('-enrolled_at')
    
    # Apply filters
    if status_filter:
        enrollments = enrollments.filter(status=status_filter)
    
    if course_filter:
        enrollments = enrollments.filter(course_id=course_filter)
    
    if search_query:
        enrollments = enrollments.filter(
            Q(student__email__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(course__title__icontains=search_query)
        )
    
    # Stats
    total_enrollments = enrollments.count()
    active_enrollments = enrollments.filter(status='active').count()
    completed_enrollments = enrollments.filter(status='completed').count()
    dropped_enrollments = enrollments.filter(status='dropped').count()
    
    # Get all courses for filter dropdown
    courses = Course.objects.filter(status='published').order_by('title')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(enrollments, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'enrollments': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'dropped_enrollments': dropped_enrollments,
        'courses': courses,
        'current_status': status_filter,
        'current_course': course_filter,
        'current_search': search_query,
    }
    return render(request, 'dashboard/admin/enrollments.html', context)


@login_required
@admin_required
def update_enrollment_status(request, enrollment_id):
    """AJAX: Update enrollment status"""
    if request.method == 'POST':
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        new_status = request.POST.get('status')
        
        if new_status in ['active', 'completed', 'dropped', 'paused']:
            enrollment.status = new_status
            if new_status == 'completed':
                enrollment.completed_at = timezone.now()
                enrollment.progress_percentage = 100
            enrollment.save()
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)



import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from apps.dashboard.models import SiteSetting, SiteFileSetting, FAQ


@login_required
@staff_member_required
def site_settings(request, setting_type='general'):
    """Site settings page - admin only"""
    
    setting_types = SiteSetting.SETTING_TYPES
    
    if request.method == 'POST':
        action = request.POST.get('action', 'save_settings')
        
        # Handle FAQ actions
        if setting_type == 'faq':
            if action == 'add_faq':
                FAQ.objects.create(
                    question=request.POST.get('question', ''),
                    answer=request.POST.get('answer', ''),
                    category=request.POST.get('faq_category', 'general'),
                    order=request.POST.get('order', 0),
                    is_active=request.POST.get('is_active') == 'on',
                )
                messages.success(request, 'FAQ added successfully!')
                
            elif action == 'update_faq':
                faq_id = request.POST.get('faq_id')
                if faq_id:
                    faq = get_object_or_404(FAQ, id=faq_id)
                    faq.question = request.POST.get('question', faq.question)
                    faq.answer = request.POST.get('answer', faq.answer)
                    faq.category = request.POST.get('faq_category', faq.category)
                    faq.order = int(request.POST.get('order', faq.order))
                    faq.is_active = request.POST.get('is_active') == 'on'
                    faq.save()
                    messages.success(request, 'FAQ updated successfully!')
                    
            elif action == 'delete_faq':
                faq_id = request.POST.get('faq_id')
                if faq_id:
                    FAQ.objects.filter(id=faq_id).delete()
                    messages.success(request, 'FAQ deleted successfully!')
            
            return redirect('dashboard:site_settings_type', setting_type='faq')
        
        # Handle file uploads
        file_fields = ['site_logo', 'dashboard_logo', 'favicon']
        for file_key in file_fields:
            if file_key in request.FILES:
                try:
                    old_file_setting = SiteFileSetting.objects.get(key=file_key)
                    if old_file_setting.file:
                        if os.path.isfile(old_file_setting.file.path):
                            os.remove(old_file_setting.file.path)
                except SiteFileSetting.DoesNotExist:
                    pass
                
                file_setting, created = SiteFileSetting.objects.update_or_create(
                    key=file_key,
                    defaults={'description': file_key.replace('_', ' ').title()}
                )
                file_setting.file = request.FILES[file_key]
                file_setting.save()
        
        # Handle text settings
        excluded_keys = ['csrfmiddlewaretoken', 'setting_type', 'action', 
                        'faq_category', 'faq_id', 'question', 'answer', 
                        'order', 'is_active'] + file_fields
        
        for key, value in request.POST.items():
            if key not in excluded_keys and value:
                SiteSetting.objects.update_or_create(
                    key=key,
                    defaults={
                        'value': value,
                        'setting_type': setting_type,
                        'description': key.replace('_', ' ').title()
                    }
                )
        
        setting_type_display = dict(setting_types).get(setting_type, 'Settings')
        messages.success(request, f'{setting_type_display} updated successfully!')
        return redirect('dashboard:site_settings_type', setting_type=setting_type)
    
    # GET request - Load current settings
    context_settings = {}
    
    # Load text settings
    settings_qs = SiteSetting.objects.filter(setting_type=setting_type)
    for setting in settings_qs:
        context_settings[setting.key] = setting.value
    
    # Load file settings (only for branding section)
    if setting_type == 'branding':
        file_settings = SiteFileSetting.objects.all()
        for file_setting in file_settings:
            context_settings[file_setting.key] = file_setting.file
    
    # Get FAQs for FAQ setting type
    faqs = []
    if setting_type == 'faq':
        faqs = FAQ.objects.all().order_by('category', 'order')
    
    context = {
        'settings': context_settings,
        'setting_type': setting_type,
        'setting_types': setting_types,
        'setting_type_display': dict(setting_types).get(setting_type, 'General'),
        'faqs': faqs,
        'faq_categories': FAQ.CATEGORY_CHOICES if setting_type == 'faq' else [],
    }
    return render(request, 'dashboard/admin/settings.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Count, Q
from django.http import JsonResponse
from apps.frontend.models import ContactMessage, ContactReply, NewsletterSubscriber, NewsletterCampaign, SiteReview

def superadmin_required(view_func):
    """Decorator for views that require superuser access"""
    return user_passes_test(lambda u: u.is_superuser or u.is_staff)(view_func)


@login_required
@superadmin_required
def contact_messages(request):
    """View all contact messages"""
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'unread':
        messages_list = ContactMessage.objects.filter(status='unread')
    elif status_filter == 'read':
        messages_list = ContactMessage.objects.filter(status='read')
    elif status_filter == 'replied':
        messages_list = ContactMessage.objects.filter(status='replied')
    elif status_filter == 'archived':
        messages_list = ContactMessage.objects.filter(status='archived')
    else:
        messages_list = ContactMessage.objects.all()
    
    # Count messages by status
    unread_count = ContactMessage.objects.filter(status='unread').count()
    read_count = ContactMessage.objects.filter(status='read').count()
    replied_count = ContactMessage.objects.filter(status='replied').count()
    total_count = ContactMessage.objects.count()
    
    context = {
        'messages_list': messages_list,
        'status_filter': status_filter,
        'unread_count': unread_count,
        'read_count': read_count,
        'replied_count': replied_count,
        'total_count': total_count,
    }
    return render(request, 'dashboard/admin/contact_messages.html', context)


@login_required
@superadmin_required
def contact_message_detail(request, message_id):
    """View and reply to a specific contact message"""
    contact_message = get_object_or_404(ContactMessage, id=message_id)
    
    # Mark as read if unread
    if not contact_message.is_read:
        contact_message.mark_as_read()
    
    if request.method == 'POST':
        reply_subject = request.POST.get('subject', f"Re: {contact_message.subject or 'Your Message'}")
        reply_message = request.POST.get('message', '')
        
        if reply_message:
            # Save reply to database
            ContactReply.objects.create(
                contact_message=contact_message,
                subject=reply_subject,
                message=reply_message,
                sent_by=request.user
            )
            
            # Send email
            try:
                html_message = render_to_string('emails/contact_reply.html', {
                    'name': contact_message.name,
                    'original_message': contact_message.message,
                    'reply_message': reply_message,
                    'site_name': 'AI Governance Academy'
                })
                
                plain_message = strip_tags(html_message)
                
                email = EmailMultiAlternatives(
                    subject=reply_subject,
                    body=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[contact_message.email],
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
                
                contact_message.mark_as_replied()
                messages.success(request, f'Reply sent successfully to {contact_message.email}')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')
            
            return redirect('dashboard:contact_messages')
    
    # Get all replies for this message
    replies = contact_message.replies.all()
    
    context = {
        'contact_message': contact_message,
        'replies': replies,
    }
    return render(request, 'dashboard/admin/contact_message_detail.html', context)


@login_required
@superadmin_required
def contact_message_action(request, message_id, action):
    """Perform actions on contact messages"""
    contact_message = get_object_or_404(ContactMessage, id=message_id)
    
    if action == 'archive':
        contact_message.status = 'archived'
        contact_message.save()
        messages.success(request, 'Message archived successfully')
    elif action == 'mark_unread':
        contact_message.status = 'unread'
        contact_message.is_read = False
        contact_message.save()
        messages.success(request, 'Message marked as unread')
    elif action == 'delete':
        contact_message.delete()
        messages.success(request, 'Message deleted successfully')
    
    return redirect('dashboard:contact_messages')


@login_required
@superadmin_required
def newsletter_dashboard(request):
    """Newsletter management dashboard"""
    subscribers = NewsletterSubscriber.objects.filter(is_active=True)
    subscribers_count = subscribers.count()
    total_subscribers = NewsletterSubscriber.objects.count()
    unsubscribed_count = NewsletterSubscriber.objects.filter(is_active=False).count()
    
    campaigns = NewsletterCampaign.objects.all().order_by('-created_at')[:10]
    
    context = {
        'subscribers': subscribers,
        'subscribers_count': subscribers_count,
        'total_subscribers': total_subscribers,
        'unsubscribed_count': unsubscribed_count,
        'campaigns': campaigns,
    }
    return render(request, 'dashboard/admin/newsletter_dashboard.html', context)


@login_required
@superadmin_required
def newsletter_compose(request):
    """Compose and send newsletter"""
    if request.method == 'POST':
        subject = request.POST.get('subject', '')
        content = request.POST.get('content', '')
        recipient_type = request.POST.get('recipient_type', 'all')
        
        if not subject or not content:
            messages.error(request, 'Subject and content are required')
            return redirect('dashboard:newsletter_compose')
        
        # Get recipients
        if recipient_type == 'active':
            recipients = NewsletterSubscriber.objects.filter(is_active=True)
        else:
            recipients = NewsletterSubscriber.objects.all()
        
        recipient_emails = list(recipients.values_list('email', flat=True))
        
        if not recipient_emails:
            messages.warning(request, 'No subscribers to send to')
            return redirect('dashboard:newsletter_compose')
        
        # Create campaign record
        campaign = NewsletterCampaign.objects.create(
            subject=subject,
            content=content,
            recipients_count=len(recipient_emails),
            status='sending',
            created_by=request.user
        )
        
        # Send emails (in production, use Celery or background task)
        success_count = 0
        fail_count = 0
        
        for email in recipient_emails:
            try:
                html_message = render_to_string('emails/newsletter.html', {
                    'content': content,
                    'subscriber_email': email,
                    'site_name': 'AI Governance Academy',
                    'unsubscribe_url': f"{settings.SITE_URL}/unsubscribe/?email={email}"
                })
                
                plain_message = strip_tags(html_message)
                
                email_msg = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                email_msg.attach_alternative(html_message, "text/html")
                email_msg.send()
                success_count += 1
            except Exception as e:
                fail_count += 1
        
        # Update campaign
        campaign.sent_count = success_count
        campaign.status = 'sent'
        campaign.sent_at = timezone.now()
        campaign.save()
        
        messages.success(request, f'Newsletter sent successfully! Sent: {success_count}, Failed: {fail_count}')
        return redirect('dashboard:newsletter_dashboard')
    
    # Get subscriber counts for the compose page
    active_count = NewsletterSubscriber.objects.filter(is_active=True).count()
    total_count = NewsletterSubscriber.objects.count()
    
    context = {
        'active_count': active_count,
        'total_count': total_count,
    }
    return render(request, 'dashboard/admin/newsletter_compose.html', context)


@login_required
@superadmin_required
def newsletter_campaign_detail(request, campaign_id):
    """View newsletter campaign details"""
    campaign = get_object_or_404(NewsletterCampaign, id=campaign_id)
    
    context = {
        'campaign': campaign,
    }
    return render(request, 'dashboard/admin/newsletter_campaign_detail.html', context)


@login_required
@superadmin_required
def delete_subscriber(request, subscriber_id):
    """Delete a newsletter subscriber"""
    if request.method == 'POST':
        subscriber = get_object_or_404(NewsletterSubscriber, id=subscriber_id)
        subscriber.delete()
        messages.success(request, 'Subscriber deleted successfully')
    return redirect('dashboard:newsletter_dashboard')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg
from apps.frontend.models import SiteReview


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def manage_reviews(request):
    """Manage and approve site reviews"""
    status_filter = request.GET.get('status', 'pending')
    
    if status_filter == 'approved':
        reviews = SiteReview.objects.filter(is_approved=True)
    elif status_filter == 'all':
        reviews = SiteReview.objects.all()
    else:
        reviews = SiteReview.objects.filter(is_approved=False)
    
    # Handle POST actions
    if request.method == 'POST':
        action = request.POST.get('action')
        review_id = request.POST.get('review_id')
        
        # Handle adding new review (admin-created)
        if action == 'add_review':
            rating = request.POST.get('rating', 5)
            review_text = request.POST.get('review_text', '')
            reviewer_name = request.POST.get('reviewer_name', '')
            reviewer_email = request.POST.get('reviewer_email', '')
            designation = request.POST.get('designation', '')
            company = request.POST.get('company', '')
            
            if review_text and reviewer_name:
                SiteReview.objects.create(
                    reviewer_name=reviewer_name,
                    reviewer_email=reviewer_email,
                    designation=designation,
                    company=company,
                    rating=int(rating),
                    review_text=review_text,
                    is_approved=True,  # Auto-approve admin-created reviews
                    source='admin',
                )
                messages.success(request, 'Review added successfully!')
            else:
                messages.error(request, 'Please fill in all required fields.')
            
            return redirect(f'/dashboard/reviews/?status={status_filter}')
        
        # Handle review actions (approve/unapprove/delete)
        if review_id:
            review = get_object_or_404(SiteReview, id=review_id)
            
            if action == 'approve':
                review.is_approved = True
                review.save()
                messages.success(request, 'Review approved successfully!')
            elif action == 'unapprove':
                review.is_approved = False
                review.save()
                messages.success(request, 'Review unapproved successfully!')
            elif action == 'delete':
                reviewer_name = review.get_reviewer_name()
                review.delete()
                messages.success(request, f'Review by {reviewer_name} deleted successfully!')
        
        return redirect(f'/dashboard/reviews/?status={status_filter}')
    
    # Counts
    pending_count = SiteReview.objects.filter(is_approved=False).count()
    approved_count = SiteReview.objects.filter(is_approved=True).count()
    total_count = SiteReview.objects.count()
    
    # Average rating
    avg_rating = SiteReview.objects.filter(is_approved=True).aggregate(
        avg=Avg('rating')
    )['avg'] or 0
    
    context = {
        'reviews': reviews,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'total_count': total_count,
        'avg_rating': round(avg_rating, 1),
    }
    return render(request, 'dashboard/admin/manage_reviews.html', context)





# views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages

@staff_member_required
def manage_featured_courses(request):
    """Dedicated page for managing featured course and top picks"""
    
    # Get all published courses for selection
    available_courses = Course.objects.filter(
        status='published'
    ).select_related('instructor')
    
    # Get current featured course
    current_featured = FeaturedCourse.objects.filter(
        is_active=True
    ).select_related('course').first()
    
    # Get current top picks
    current_top_picks = TopPick.objects.filter(
        is_active=True
    ).select_related('course').order_by('position')
    
    # Get recent featured history
    featured_history = FeaturedCourse.objects.all().select_related(
        'course'
    )[:10]
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'set_featured':
            course_id = request.POST.get('course_id')
            end_date = request.POST.get('end_date')
            
            try:
                course = Course.objects.get(id=course_id)
                
                # Deactivate current featured course
                FeaturedCourse.objects.filter(
                    is_active=True
                ).update(is_active=False)
                
                # Create new featured course
                featured = FeaturedCourse.objects.create(
                    course=course,
                    end_date=end_date if end_date else None,
                    created_by=request.user
                )
                
                # Update course badge
                course.badge = 'featured'
                course.save()
                
                messages.success(request, f'"{course.title}" is now featured!')
                
            except Course.DoesNotExist:
                messages.error(request, 'Course not found.')
        
        elif action == 'remove_featured':
            FeaturedCourse.objects.filter(
                is_active=True
            ).update(is_active=False)
            
            # Reset badge for previously featured course
            if current_featured:
                current_featured.course.badge = 'none'
                current_featured.course.save()
            
            messages.success(request, 'Featured course removed.')
        
        elif action == 'add_top_pick':
            course_id = request.POST.get('course_id')
            position = request.POST.get('position', 0)
            
            try:
                course = Course.objects.get(id=course_id)
                
                # Check if already in top picks
                if not TopPick.objects.filter(
                    course=course, 
                    is_active=True
                ).exists():
                    TopPick.objects.create(
                        course=course,
                        position=position
                    )
                    messages.success(request, f'"{course.title}" added to Top Picks!')
                else:
                    messages.warning(request, 'This course is already in Top Picks.')
                    
            except Course.DoesNotExist:
                messages.error(request, 'Course not found.')
        
        elif action == 'remove_top_pick':
            pick_id = request.POST.get('pick_id')
            TopPick.objects.filter(id=pick_id).delete()
            messages.success(request, 'Removed from Top Picks.')
        
        elif action == 'reorder_top_picks':
            order = request.POST.getlist('order[]')
            for position, pick_id in enumerate(order):
                TopPick.objects.filter(id=pick_id).update(position=position)
            messages.success(request, 'Order updated!')
        
        return redirect('dashboard:manage_featured')
    
    context = {
        'available_courses': available_courses,
        'current_featured': current_featured,
        'current_top_picks': current_top_picks,
        'featured_history': featured_history,
    }
    return render(request, 'dashboard/admin/manage_featured.html', context)