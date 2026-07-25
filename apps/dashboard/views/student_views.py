import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from apps.accounts.decorators import student_required
from apps.courses.models import Enrollment, LessonProgress


# views.py - Updated student_dashboard view

logger = logging.getLogger(__name__)


@login_required
@never_cache
def student_dashboard(request):
    """Student dashboard with real stats, courses, certificates, and activity"""
    
    # Get the student profile
    try:
        profile = request.user.student_profile
    except:
        # If no profile exists, redirect to profile setup
        messages.warning(request, 'Please complete your profile setup first.')
        return redirect('dashboard:student_profile')
    
    # ===== GET ENROLLMENTS =====
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related(
        'course', 
        'course__instructor', 
        'course__category'
    ).prefetch_related(
        'course__lessons',
        'course__reviews',
        'progress',
        'progress__lesson'
    ).order_by('-enrolled_at')
    
    # ===== UPDATE PROGRESS PERCENTAGES =====
    for enrollment in enrollments:
        total_lessons = enrollment.course.lessons.count()
        if total_lessons > 0:
            completed = enrollment.progress.filter(completed=True).count()
            progress = int((completed / total_lessons) * 100)
            
            # Update progress if changed
            if enrollment.progress_percentage != progress:
                enrollment.progress_percentage = progress
                enrollment.save(update_fields=['progress_percentage'])
            
            # Auto-complete enrollment if 100% complete
            if progress >= 100 and enrollment.status == 'active':
                enrollment.status = 'completed'
                enrollment.completed_at = timezone.now()
                enrollment.save()
    
    # ===== CALCULATE STATS =====
    active_count = enrollments.filter(status='active').count()
    completed_count = enrollments.filter(status='completed').count()
    
    # Calculate total hours learned from completed lessons
    total_minutes = 0
    for enrollment in enrollments.filter(status='completed'):
        for progress in enrollment.progress.filter(completed=True):
            # Get all content for the lesson
            for content in progress.lesson.contents.filter(content_type__in=['video', 'video_url']):
                if content.duration_minutes:
                    total_minutes += content.duration_minutes
    
    total_hours = round(total_minutes / 60, 1)
    
    # ===== BUILD ENROLLED COURSES DATA =====
    enrolled_courses = []
    for enrollment in enrollments[:6]:  # Show latest 6 on dashboard
        course = enrollment.course
        rating = course.average_rating or 0
        
        completed_lessons = enrollment.progress.filter(completed=True).count()
        total_lessons = course.lessons.count()
        
        enrolled_courses.append({
            'id': course.id,
            'slug': course.slug,
            'title': course.title,
            'description': course.short_description or course.description or '',
            'duration': course.duration or 'Self-paced',
            'modules': total_lessons,
            'completed_lessons': completed_lessons,
            'rating': rating,
            'review_count': course.review_count,
            'completed': enrollment.status == 'completed',
            'progress': enrollment.progress_percentage,
            'image': course.featured_image.url if course.featured_image else None,
            'enrollment': enrollment,
        })
    
    # ===== GET CERTIFICATES =====
    certificates = []
    completed_enrollments = enrollments.filter(status='completed')
    
    for enrollment in completed_enrollments:
        if enrollment.course.has_certificate:
            # Generate certificate if not already issued
            if not enrollment.certificate_issued:
                enrollment.certificate_issued = True
                # Generate a certificate URL (you can implement actual PDF generation)
                enrollment.certificate_url = f"/certificates/{enrollment.id}/"
                enrollment.save()
            
            certificates.append({
                'course_title': enrollment.course.title,
                'course_slug': enrollment.course.slug,
                'issued_date': enrollment.completed_at or enrollment.enrolled_at,
                'certificate_url': enrollment.certificate_url,
                'course': enrollment.course,
                'enrollment_id': enrollment.id,
            })
    
    # Only show latest 6 certificates on dashboard
    recent_certificates = certificates[:6]
    total_certificates = len(certificates)
    
    # ===== GET ALL ACTIVITIES =====
    all_activities = []
    
    # Get all lesson progress for this student
    progress_entries = LessonProgress.objects.filter(
        student=request.user
    ).select_related(
        'lesson', 
        'lesson__course'
    ).order_by('-last_accessed')
    
    for progress in progress_entries:
        if progress.lesson:
            course = progress.lesson.course
            all_activities.append({
                'course_title': course.title if course else 'Unknown Course',
                'course_slug': course.slug if course else '',
                'lesson_title': progress.lesson.title,
                'action': 'Completed' if progress.completed else 'Viewed',
                'timestamp': progress.last_accessed or progress.completed_at or timezone.now(),
                'course': course,
                'progress': progress,
            })
    
    # If no progress entries, add enrollment activities
    if not all_activities:
        for enrollment in enrollments[:10]:
            all_activities.append({
                'course_title': enrollment.course.title,
                'course_slug': enrollment.course.slug,
                'lesson_title': 'Course enrolled',
                'action': 'Enrolled',
                'timestamp': enrollment.enrolled_at,
                'course': enrollment.course,
                'progress': None,
            })
    
    # ===== UPDATE PROFILE COUNTS =====
    profile.courses_enrolled = active_count
    profile.completed_courses = completed_count
    profile.save()
    
    # ===== CONTEXT =====
    context = {
        'user': request.user,
        'profile': profile,
        'enrolled_count': active_count,
        'completed_count': completed_count,
        'total_hours': total_hours,
        'enrolled_courses': enrolled_courses,
        'certificates': recent_certificates,
        'all_activities': all_activities,  # ALL activities for the datatable
        'total_activities': len(all_activities),
        'total_certificates': total_certificates,
        'has_more_certificates': total_certificates > 6,
        # Additional data that might be useful
        'enrollments': enrollments,
        'completed_enrollments': completed_enrollments,
    }
    
    return render(request, 'dashboard/student/dashboard.html', context)


@login_required
@student_required
def student_certificates(request):
    """Student certificates page - shows all certificates"""
    profile = request.user.student_profile
    
    # Get all completed enrollments with certificates
    enrollments = Enrollment.objects.filter(
        student=request.user,
        status='completed'
    ).select_related('course').order_by('-completed_at')
    
    certificates = []
    for enrollment in enrollments:
        if enrollment.course.has_certificate:
            if not enrollment.certificate_url:
                enrollment.certificate_issued = True
                enrollment.certificate_url = f"/certificates/{enrollment.id}/"
                enrollment.save()
            
            certificates.append({
                'course_title': enrollment.course.title,
                'course_slug': enrollment.course.slug,
                'issued_date': enrollment.completed_at or enrollment.enrolled_at,
                'certificate_url': enrollment.certificate_url,
                'course': enrollment.course,
                'enrollment_id': enrollment.id,
            })
    
    context = {
        'user': request.user,
        'profile': profile,
        'certificates': certificates,
        'total_certificates': len(certificates),
    }
    return render(request, 'dashboard/student/certificates.html', context)


@login_required
@student_required
def student_profile(request):
    """Student profile page"""
    profile = request.user.student_profile
    
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.bio = request.POST.get('bio', user.bio)
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard:student_profile')
    
    context = {
        'user': request.user,
        'profile': profile,
    }
    return render(request, 'dashboard/student/profile.html', context)


@login_required
@student_required
def student_courses(request):
    """Display student's enrolled courses with real data"""
    profile = request.user.student_profile
    
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related(
        'course', 'course__instructor', 'course__category'
    ).prefetch_related(
        'course__lessons__contents', 'course__reviews', 'progress__lesson__contents'
    ).order_by('-enrolled_at')
    
    # Auto-complete enrollments that have 100% progress
    for enrollment in enrollments:
        if enrollment.progress_percentage >= 100 and enrollment.status == 'active':
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()
            enrollment.save()
    
    # Calculate total hours learned
    total_minutes = 0
    for enrollment in enrollments:
        for progress in enrollment.progress.filter(completed=True):
            for content in progress.lesson.contents.filter(content_type__in=['video', 'video_url']):
                if content.duration_minutes:
                    total_minutes += content.duration_minutes
    
    total_hours = round(total_minutes / 60, 1)
    
    # Update profile counts
    active_count = enrollments.filter(status='active').count()
    completed_count = enrollments.filter(status='completed').count()
    
    if profile.courses_enrolled != active_count:
        profile.courses_enrolled = active_count
    if profile.completed_courses != completed_count:
        profile.completed_courses = completed_count
    profile.save()
    
    # Build course data
    enrolled_courses = []
    for enrollment in enrollments:
        course = enrollment.course
        enrolled_courses.append({
            'id': course.id,
            'slug': course.slug,
            'title': course.title,
            'description': course.short_description or course.description or '',
            'duration': course.duration or 'Self-paced',
            'modules': course.lessons.count(),
            'rating': course.average_rating or 4.5,
            'review_count': course.review_count,
            'completed': enrollment.status == 'completed',
            'progress': enrollment.progress_percentage,
            'image': course.featured_image.url if course.featured_image else None,
            'status': enrollment.status,
        })
    
    context = {
        'profile': profile,
        'enrolled_courses': enrolled_courses,
        'total_enrolled': active_count,
        'total_completed': completed_count,
        'total_hours': total_hours,
    }
    return render(request, 'dashboard/student/courses.html', context)


@login_required
@student_required
def student_certificates(request):
    """Display student's earned certificates"""
    from apps.courses.models import Enrollment
    
    # Get completed enrollments
    completed_enrollments = Enrollment.objects.filter(
        student=request.user,
        status='completed'
    ).select_related('course', 'course__instructor').order_by('-completed_at')
    
    context = {
        'certificates': completed_enrollments,
        'total_certificates': completed_enrollments.count(),
    }
    return render(request, 'dashboard/student/certificates.html', context)


@login_required
@student_required
def student_reviews(request):
    """Display all reviews written by the student"""
    from apps.courses.models import CourseReview
    
    reviews = CourseReview.objects.filter(
        student=request.user
    ).select_related('course').order_by('-created_at')
    
    context = {
        'reviews': reviews,
        'total_reviews': reviews.count(),
    }
    return render(request, 'dashboard/student/reviews.html', context)