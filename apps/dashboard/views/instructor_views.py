from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from apps.accounts.decorators import instructor_required
from apps.accounts.models import CustomUser, InstructorProfile
from apps.courses.models import Course, CourseAnnouncement, CourseCategory, Lesson, LessonContent, Enrollment, CourseReview, LessonProgress
import json
from datetime import datetime, timedelta


@login_required
@instructor_required
@never_cache
def instructor_dashboard(request):
    """Instructor dashboard with real stats"""
    instructor = request.user
    
    courses = Course.objects.filter(instructor=instructor)
    total_courses = courses.count()
    published_courses = courses.filter(status='published').count()
    draft_courses = courses.filter(status='draft').count()
    
    # Get all unique students who have ever enrolled
    total_students = Enrollment.objects.filter(
        course__instructor=instructor
    ).values('student').distinct().count()
    
    # Students who have at least one active enrollment (currently learning)
    active_students = Enrollment.objects.filter(
        course__instructor=instructor,
        status='active'
    ).values('student').distinct().count()
    
    # Students who have completed at least one course
    completed_student_ids = Enrollment.objects.filter(
        course__instructor=instructor,
        status='completed'
    ).values_list('student', flat=True).distinct()
    
    active_student_ids = Enrollment.objects.filter(
        course__instructor=instructor,
        status='active'
    ).values_list('student', flat=True).distinct()
    
    # Completed only students (completed but not active in any course)
    completed_only_students = completed_student_ids.exclude(
        id__in=active_student_ids
    ).count()
    
    # All completed students (including those who are still active in other courses)
    completed_students = completed_student_ids.count()
    
    # 💰 REAL REVENUE: Calculate from actual completed payments
    from apps.payments.models import Payment  # Import your Payment model
    
    total_revenue = Payment.objects.filter(
        course__instructor=instructor,
        status='completed'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_revenue = float(total_revenue)
    
    # This month's revenue
    from django.utils import timezone
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    this_month_revenue = Payment.objects.filter(
        course__instructor=instructor,
        status='completed',
        created_at__gte=month_start
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    this_month_revenue = float(this_month_revenue)
    
    # Total paid enrollments (from completed payments)
    total_paid_enrollments = Payment.objects.filter(
        course__instructor=instructor,
        status='completed'
    ).values('enrollment').distinct().count()
    
    # Free enrollments
    free_enrollments = Enrollment.objects.filter(
        course__instructor=instructor,
        course__is_free=True,
        status__in=['active', 'completed']
    ).count()
    
    avg_rating = courses.aggregate(avg=Avg('reviews__rating'))['avg'] or 0
    total_reviews = CourseReview.objects.filter(course__instructor=instructor).count()
    
    # Calculate completion rate based on unique students
    if total_students > 0:
        completion_rate = round((completed_only_students / total_students) * 100, 1)
    else:
        completion_rate = 0
    
    # Calculate revenue per paying student
    if total_paid_enrollments > 0:
        revenue_per_student = round(total_revenue / total_paid_enrollments, 2)
    else:
        revenue_per_student = 0
    
    # Recent enrollments with payment info
    recent_enrollments = Enrollment.objects.filter(
        course__instructor=instructor
    ).select_related('student', 'course').prefetch_related('payments').order_by('-enrolled_at')[:5]
    
    # Top courses with detailed enrollment and revenue counts
    top_courses = courses.filter(status='published').annotate(
        active_students_count=Count('enrollments', filter=Q(enrollments__status='active')),
        completed_students_count=Count('enrollments', filter=Q(enrollments__status='completed')),
        total_enrollments_count=Count('enrollments'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-total_enrollments_count')[:5]
    
    # Get revenue per course for top courses
    for course in top_courses:
        course.revenue = float(
            Payment.objects.filter(
                course=course,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
        )
        course.paid_students = Payment.objects.filter(
            course=course,
            status='completed'
        ).values('enrollment').distinct().count()
    
    # Chart data for enrollment overview (last 6 months)
    chart_labels = []
    chart_enrollments = []
    chart_revenue = []
    chart_completed = []
    
    for i in range(5, -1, -1):
        month_date = now.replace(day=1) - timedelta(days=i * 30)
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1)
        
        chart_labels.append(month_start.strftime('%b'))
        
        # Total enrollments in that month
        count = Enrollment.objects.filter(
            course__instructor=instructor,
            enrolled_at__gte=month_start,
            enrolled_at__lt=month_end
        ).count()
        chart_enrollments.append(count)
        
        # Completed in that month
        completed = Enrollment.objects.filter(
            course__instructor=instructor,
            status='completed',
            completed_at__gte=month_start,
            completed_at__lt=month_end
        ).count()
        chart_completed.append(completed)
        
        # ✅ REAL Revenue from completed payments in that month
        rev = Payment.objects.filter(
            course__instructor=instructor,
            status='completed',
            created_at__gte=month_start,
            created_at__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        chart_revenue.append(float(rev))
    
    context = {
        'profile': instructor.instructor_profile,
        'total_courses': total_courses,
        'published_courses': published_courses,
        'draft_courses': draft_courses,
        'active_students': active_students,
        'completed_students': completed_students,
        'completed_only_students': completed_only_students,
        'total_students': total_students,
        'total_revenue': round(total_revenue, 2),
        'this_month_revenue': round(this_month_revenue, 2),
        'total_paid_enrollments': total_paid_enrollments,
        'free_enrollments': free_enrollments,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': total_reviews,
        'completion_rate': completion_rate,
        'revenue_per_student': revenue_per_student,
        'recent_enrollments': recent_enrollments,
        'top_courses': top_courses,
        'chart_data': json.dumps({
            'labels': chart_labels,
            'enrollments': chart_enrollments,
            'completed': chart_completed,
            'revenue': chart_revenue,
        }),
    }
    return render(request, 'dashboard/instructor/dashboard.html', context)


@login_required
@instructor_required
def instructor_profile(request):
    profile = request.user.instructor_profile
    
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.bio = request.POST.get('bio', user.bio)
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        user.save()
        
        profile.department = request.POST.get('department', profile.department)
        profile.expertise = request.POST.get('expertise', profile.expertise)
        profile.qualification = request.POST.get('qualification', profile.qualification)
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard:instructor_profile')
    
    context = {
        'user': request.user,
        'profile': profile,
    }
    return render(request, 'dashboard/instructor/profile.html', context)


@login_required
@instructor_required
def instructor_courses(request):
    courses = Course.objects.filter(
        instructor=request.user
    ).annotate(
        active_students=Count('enrollments', filter=Q(enrollments__status='active')),
        completed_students=Count('enrollments', filter=Q(enrollments__status='completed')),
        total_enrollments=Count('enrollments'),
        avg_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews'),
        lesson_count=Count('lessons')  # Changed from total_lessons to lesson_count
    ).order_by('-created_at')
    
    # Get payment data for each course
    from apps.payments.models import Payment
    for course in courses:
        course.revenue = float(
            Payment.objects.filter(
                course=course,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
        )
        course.paid_students = Payment.objects.filter(
            course=course,
            status='completed'
        ).values('enrollment').distinct().count()
    
    # Aggregate stats
    total_enrollments = sum(c.total_enrollments for c in courses)
    total_active = sum(c.active_students for c in courses)
    total_completed = sum(c.completed_students for c in courses)
    
    # Calculate average rating across all courses
    rated_courses = [c for c in courses if c.avg_rating]
    overall_avg_rating = sum(c.avg_rating for c in rated_courses) / len(rated_courses) if rated_courses else 0
    
    context = {
        'courses': courses,
        'total_courses': courses.count(),
        'published_courses': courses.filter(status='published').count(),
        'draft_courses': courses.filter(status='draft').count(),
        'archived_courses': courses.filter(status='archived').count(),
        'review_courses': courses.filter(status='review').count(),
        'total_enrollments': total_enrollments,
        'total_active': total_active,
        'total_completed': total_completed,
        'overall_avg_rating': overall_avg_rating,
    }
    return render(request, 'dashboard/instructor/courses.html', context)

import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum
from apps.accounts.decorators import instructor_required
from apps.courses.models import Course, CourseCategory, Lesson, LessonContent, Enrollment, CourseReview


@login_required
@instructor_required
def instructor_add_course(request):
    """Instructor adds a new course with lessons and content"""
    if request.method == 'POST':
        return _save_course(request, is_edit=False)
    
    context = {
        'is_edit': False,
    }
    return render(request, 'dashboard/instructor/add_course.html', context)


@login_required
@instructor_required
def instructor_edit_course(request, course_id):
    """Instructor edits an existing course"""
    course = get_object_or_404(Course, id=course_id)
    
    if course.instructor != request.user:
        messages.error(request, 'You can only edit your own courses.')
        return redirect('dashboard:instructor_courses')
    
    if request.method == 'POST':
        return _save_course(request, is_edit=True, course=course)
    
    # Prepare existing lessons data with IDs
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
    
    context = {
        'is_edit': True,
        'course': course,
        'existing_lessons_json': json.dumps(existing_lessons),
    }
    return render(request, 'dashboard/instructor/add_course.html', context)


def _save_course(request, is_edit=False, course=None):
    """Handle course creation/update logic"""
    
    # DEBUG
    print("=" * 50)
    print("DEBUG FILES keys:", list(request.FILES.keys()))
    for key, file in request.FILES.items():
        print(f"  {key}: {file.name} ({file.size} bytes)")
    print("=" * 50)
    
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
    thumbnail = request.FILES.get('thumbnail')
    featured_video = request.FILES.get('featured_video')
    lessons_data_str = request.POST.get('lessons_data', '[]')
    
    print(f"DEBUG thumbnail: {thumbnail}")
    print(f"DEBUG featured_video: {featured_video}")
    print(f"DEBUG trailer_url: '{trailer_url}'")
    
    try:
        lessons_data = json.loads(lessons_data_str)
    except json.JSONDecodeError:
        lessons_data = []
    
    if not title:
        messages.error(request, 'Course title is required.')
        if is_edit and course:
            return redirect('dashboard:instructor_edit_course', course_id=course.id)
        return redirect('dashboard:instructor_add_course')
    
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
        
        # Only update files if new ones are uploaded
        if thumbnail:
            course.featured_image = thumbnail
            print(f"DEBUG: Updating featured_image with {thumbnail.name}")
        if featured_video:
            course.featured_video = featured_video
            print(f"DEBUG: Updating featured_video with {featured_video.name}")
        
        course.save()
        print(f"DEBUG: Course saved. featured_image={course.featured_image}, featured_video={course.featured_video}, trailer_url={course.trailer_url}")
        
        # Update lessons
        _update_lessons(request, course, lessons_data)
        
        messages.success(request, f'Course "{course.title}" updated successfully!')
        return redirect('dashboard:instructor_edit_course', course_id=course.id)
    
    else:
        # CREATE new course
        course = Course.objects.create(
            title=title,
            instructor=request.user,
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
        
        print(f"DEBUG: Course created. featured_image={course.featured_image}, featured_video={course.featured_video}, trailer_url={course.trailer_url}")
        
        # Create new lessons
        _create_lessons(request, course, lessons_data)
        
        messages.success(request, f'Course "{course.title}" created successfully!')
        return redirect('dashboard:instructor_courses')


def _update_lessons(request, course, lessons_data):
    """UPDATE existing lessons - preserve IDs and files"""
    existing_lesson_ids = set(course.lessons.values_list('id', flat=True))
    updated_lesson_ids = set()
    
    for i, lesson_data in enumerate(lessons_data):
        lesson_id = lesson_data.get('id')
        lesson_title = lesson_data.get('title', f'Lesson {i+1}')
        
        if not lesson_title:
            continue
        
        if lesson_id and lesson_id in existing_lesson_ids:
            lesson = Lesson.objects.get(id=lesson_id, course=course)
            lesson.title = lesson_title
            lesson.order = i + 1
            lesson.save()
        else:
            lesson = Lesson.objects.create(
                course=course,
                title=lesson_title,
                order=i + 1,
            )
        
        updated_lesson_ids.add(lesson.id)
        _update_contents(request, lesson, lesson_data.get('contents', []), i)
    
    lessons_to_delete = existing_lesson_ids - updated_lesson_ids
    if lessons_to_delete:
        Lesson.objects.filter(id__in=lessons_to_delete).delete()


def _update_contents(request, lesson, contents_data, lesson_index):
    """UPDATE existing contents - preserve IDs and files"""
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
            content = LessonContent.objects.get(id=content_id, lesson=lesson)
            content.content_type = content_type
            content.title = content_title
            content.duration_minutes = duration_minutes
            content.video_url = video_url if content_type in ['video', 'video_url'] else ''
            content.text_content = text_content if content_type in ['text', 'quiz', 'assignment', 'code'] else ''
            content.order = j + 1
            content.save()
        else:
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
    
    contents_to_delete = existing_content_ids - updated_content_ids
    if contents_to_delete:
        LessonContent.objects.filter(id__in=contents_to_delete).delete()


def _create_lessons(request, course, lessons_data):
    """CREATE new lessons (for new courses)"""
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
@instructor_required
def instructor_course_students(request, course_id):
    """View students enrolled in instructor's course with detailed analytics"""
    course = get_object_or_404(Course, id=course_id)
    
    if course.instructor != request.user:
        messages.error(request, 'You can only view students for your own courses.')
        return redirect('dashboard:instructor_courses')
    
    # Get all enrollments with related data
    enrollments = Enrollment.objects.filter(
        course=course
    ).select_related(
        'student', 
        'student__student_profile'
    ).prefetch_related(
        'progress',
        'payments'
    ).order_by('-enrolled_at')
    
    # Calculate lesson progress for each student
    total_lessons = course.lessons.count()
    for enrollment in enrollments:
        if total_lessons > 0:
            completed_lessons = enrollment.progress.filter(completed=True).count()
            enrollment.lesson_progress = round((completed_lessons / total_lessons) * 100, 1)
            enrollment.completed_lessons_count = completed_lessons
            enrollment.total_lessons_count = total_lessons
        else:
            enrollment.lesson_progress = 0
            enrollment.completed_lessons_count = 0
            enrollment.total_lessons_count = 0
        
        # Check if student paid for this course
        enrollment.has_paid = enrollment.payments.filter(status='completed').exists()
        
        # Get last activity
        enrollment.last_activity = enrollment.progress.order_by('-last_accessed').first()
    
    # Course statistics
    from apps.payments.models import Payment
    
    total_revenue = float(
        Payment.objects.filter(
            course=course,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
    )
    
    paid_students = Payment.objects.filter(
        course=course,
        status='completed'
    ).values('user').distinct().count()
    
    # Average completion rate
    if enrollments.count() > 0:
        avg_completion = sum(e.progress_percentage for e in enrollments) / enrollments.count()
    else:
        avg_completion = 0
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    active_this_month = enrollments.filter(last_accessed__gte=thirty_days_ago).count()
    
    context = {
        'course': course,
        'enrollments': enrollments,
        'total_enrolled': enrollments.count(),
        'active_students': enrollments.filter(status='active').count(),
        'completed_students': enrollments.filter(status='completed').count(),
        'dropped_students': enrollments.filter(status='dropped').count(),
        'paused_students': enrollments.filter(status='paused').count(),
        'total_revenue': total_revenue,
        'paid_students': paid_students,
        'avg_completion': round(avg_completion, 1),
        'active_this_month': active_this_month,
        'total_lessons': total_lessons,
    }
    return render(request, 'dashboard/instructor/course_students.html', context)


@login_required
@instructor_required
def instructor_course_analytics(request, course_id):
    """Detailed analytics for a specific course"""
    course = get_object_or_404(Course, id=course_id)
    
    if course.instructor != request.user:
        messages.error(request, 'You can only view analytics for your own courses.')
        return redirect('dashboard:instructor_courses')
    
    from apps.payments.models import Payment
    
    # Get all enrollments for this course
    enrollments = Enrollment.objects.filter(course=course)
    total_enrolled = enrollments.count()
    
    # Revenue data
    total_revenue = float(
        Payment.objects.filter(
            course=course,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
    )
    
    paid_enrollments = Payment.objects.filter(
        course=course,
        status='completed'
    ).count()
    
    refunded_payments = Payment.objects.filter(
        course=course,
        status='refunded'
    ).count()
    
    # Enrollment trends (last 6 months)
    enrollment_trends = []
    revenue_trends = []
    completion_trends = []
    labels = []
    
    for i in range(5, -1, -1):
        month_date = timezone.now().replace(day=1) - timedelta(days=i * 30)
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1)
        
        labels.append(month_start.strftime('%b %Y'))
        
        # Monthly enrollments
        count = enrollments.filter(
            enrolled_at__gte=month_start,
            enrolled_at__lt=month_end
        ).count()
        enrollment_trends.append(count)
        
        # Monthly completions
        completed = enrollments.filter(
            status='completed',
            completed_at__gte=month_start,
            completed_at__lt=month_end
        ).count()
        completion_trends.append(completed)
        
        # Monthly revenue
        rev = float(
            Payment.objects.filter(
                course=course,
                status='completed',
                created_at__gte=month_start,
                created_at__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
        )
        revenue_trends.append(round(rev, 2))
    
    # Student progress distribution
    progress_ranges = {
        'not_started': enrollments.filter(progress_percentage=0).count(),
        '25_percent': enrollments.filter(progress_percentage__gt=0, progress_percentage__lte=25).count(),
        '50_percent': enrollments.filter(progress_percentage__gt=25, progress_percentage__lte=50).count(),
        '75_percent': enrollments.filter(progress_percentage__gt=50, progress_percentage__lte=75).count(),
        '100_percent': enrollments.filter(progress_percentage__gt=75, progress_percentage__lte=100).count(),
    }
    
    # Lesson completion rates
    lesson_stats = []
    for lesson in course.lessons.all().order_by('order'):
        completed_count = LessonProgress.objects.filter(
            lesson=lesson,
            completed=True,
            enrollment__course=course
        ).count()
        
        lesson_stats.append({
            'title': lesson.title,
            'order': lesson.order,
            'completed': completed_count,
            'total': total_enrolled,
            'percentage': round((completed_count / total_enrolled * 100) if total_enrolled > 0 else 0, 1)
        })
    
    # Student status distribution
    status_distribution = {
        'active': enrollments.filter(status='active').count(),
        'completed': enrollments.filter(status='completed').count(),
        'dropped': enrollments.filter(status='dropped').count(),
        'paused': enrollments.filter(status='paused').count(),
    }
    
    # Average rating and reviews
    avg_rating = course.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    total_reviews = course.reviews.count()
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = course.reviews.filter(rating=i).count()
    
    # Recent reviews
    recent_reviews = course.reviews.select_related('student').order_by('-created_at')[:5]
    
    context = {
        'course': course,
        'total_enrolled': total_enrolled,
        'total_revenue': total_revenue,
        'paid_enrollments': paid_enrollments,
        'refunded_payments': refunded_payments,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': total_reviews,
        'chart_data': json.dumps({
            'labels': labels,
            'enrollments': enrollment_trends,
            'completions': completion_trends,
            'revenue': revenue_trends,
        }),
        'progress_ranges': json.dumps(list(progress_ranges.values())),
        'progress_labels': json.dumps(['Not Started', '1-25%', '26-50%', '51-75%', '76-100%']),
        'lesson_stats': lesson_stats,
        'status_distribution': json.dumps(list(status_distribution.values())),
        'status_labels': json.dumps(['Active', 'Completed', 'Dropped', 'Paused']),
        'rating_distribution': json.dumps([rating_distribution[i] for i in range(1, 6)]),
        'recent_reviews': recent_reviews,
    }
    return render(request, 'dashboard/instructor/course_analytics.html', context)


@login_required
@instructor_required
def instructor_change_password(request):
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated successfully!')
            return redirect('dashboard:instructor_profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    
    return render(request, 'dashboard/instructor/change_password.html')



@login_required
@instructor_required
def instructor_reviews(request):
    """View all reviews for instructor's courses"""
    reviews = CourseReview.objects.filter(
        course__instructor=request.user
    ).select_related('course', 'student').order_by('-created_at')
    
    # Stats
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    rating_5 = reviews.filter(rating=5).count()
    rating_4 = reviews.filter(rating=4).count()
    rating_3 = reviews.filter(rating=3).count()
    rating_2 = reviews.filter(rating=2).count()
    rating_1 = reviews.filter(rating=1).count()
    
    # Filter by course
    course_id = request.GET.get('course')
    if course_id:
        reviews = reviews.filter(course_id=course_id)
    
    courses = Course.objects.filter(instructor=request.user, status='published')
    
    context = {
        'reviews': reviews[:50],
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1),
        'rating_5': rating_5,
        'rating_4': rating_4,
        'rating_3': rating_3,
        'rating_2': rating_2,
        'rating_1': rating_1,
        'courses': courses,
        'selected_course': course_id,
    }
    return render(request, 'dashboard/instructor/reviews.html', context)



@login_required
@instructor_required
def instructor_earnings(request):
    """View earnings and revenue details"""
    from apps.payments.models import Payment
    
    courses = Course.objects.filter(instructor=request.user)
    
    # Total earnings
    total_earnings = float(
        Payment.objects.filter(
            course__instructor=request.user,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
    )
    
    # This month earnings
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_earnings = float(
        Payment.objects.filter(
            course__instructor=request.user,
            status='completed',
            created_at__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
    )
    
    # Last month earnings
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    last_month_earnings = float(
        Payment.objects.filter(
            course__instructor=request.user,
            status='completed',
            created_at__gte=last_month_start,
            created_at__lt=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
    )
    
    # Revenue per course
    revenue_per_course = []
    for course in courses.filter(status='published'):
        rev = float(
            Payment.objects.filter(course=course, status='completed').aggregate(total=Sum('amount'))['total'] or 0
        )
        students = Payment.objects.filter(course=course, status='completed').values('user').distinct().count()
        revenue_per_course.append({
            'course': course,
            'revenue': rev,
            'students': students,
        })
    
    # Recent transactions
    recent_payments = Payment.objects.filter(
        course__instructor=request.user,
        status='completed'
    ).select_related('user', 'course').order_by('-created_at')[:20]
    
    # Monthly chart data
    chart_labels = []
    chart_data = []
    for i in range(5, -1, -1):
        month_date = now.replace(day=1) - timedelta(days=i * 30)
        m_start = month_date.replace(day=1)
        if month_date.month == 12:
            m_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
        else:
            m_end = month_date.replace(month=month_date.month + 1, day=1)
        chart_labels.append(m_start.strftime('%b'))
        rev = float(
            Payment.objects.filter(
                course__instructor=request.user,
                status='completed',
                created_at__gte=m_start,
                created_at__lt=m_end
            ).aggregate(total=Sum('amount'))['total'] or 0
        )
        chart_data.append(round(rev, 2))
    
    context = {
        'total_earnings': total_earnings,
        'month_earnings': month_earnings,
        'last_month_earnings': last_month_earnings,
        'revenue_per_course': revenue_per_course,
        'recent_payments': recent_payments,
        'chart_data': json.dumps({'labels': chart_labels, 'data': chart_data}),
    }
    return render(request, 'dashboard/instructor/earnings.html', context)



@login_required
@instructor_required
def instructor_announcements(request):
    """Manage course announcements"""
    courses = Course.objects.filter(instructor=request.user)
    
    course_id = request.GET.get('course')
    selected_course = None
    
    if course_id:
        selected_course = get_object_or_404(Course, id=course_id, instructor=request.user)
        announcements = CourseAnnouncement.objects.filter(course=selected_course).order_by('-created_at')
    else:
        announcements = CourseAnnouncement.objects.filter(course__instructor=request.user).select_related('course').order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            course_id = request.POST.get('course_id')
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            is_pinned = request.POST.get('is_pinned') == 'on'
            
            if title and content and course_id:
                course = get_object_or_404(Course, id=course_id, instructor=request.user)
                CourseAnnouncement.objects.create(
                    course=course,
                    title=title,
                    content=content,
                    is_pinned=is_pinned,
                )
                messages.success(request, 'Announcement posted successfully!')
            else:
                messages.error(request, 'Please fill in all required fields.')
        
        elif action == 'delete':
            announcement_id = request.POST.get('announcement_id')
            announcement = get_object_or_404(CourseAnnouncement, id=announcement_id, course__instructor=request.user)
            announcement.delete()
            messages.success(request, 'Announcement deleted.')
        
        return redirect(request.path + ('?course=' + course_id if course_id else ''))
    
    context = {
        'courses': courses,
        'selected_course': selected_course,
        'announcements': announcements,
    }
    return render(request, 'dashboard/instructor/announcements.html', context)



@login_required
@instructor_required
def instructor_student_detail(request, course_id, student_id):
    """View detailed progress for a specific student"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    enrollment = get_object_or_404(Enrollment, course=course, student_id=student_id)
    
    # Get all lessons with progress
    lessons = course.lessons.all().order_by('order')
    for lesson in lessons:
        progress = LessonProgress.objects.filter(
            student_id=student_id,
            lesson=lesson,
            enrollment=enrollment
        ).first()
        lesson.is_completed = progress.completed if progress else False
        lesson.time_spent = progress.time_spent if progress else None
        lesson.last_accessed = progress.last_accessed if progress else None
    
    # Overall stats
    total_lessons = lessons.count()
    completed_lessons = sum(1 for l in lessons if l.is_completed)
    
    # Activity timeline
    activities = LessonProgress.objects.filter(
        student_id=student_id,
        enrollment=enrollment
    ).select_related('lesson').order_by('-last_accessed')[:20]
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'student': enrollment.student,
        'lessons': lessons,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'progress_percent': enrollment.progress_percentage,
        'activities': activities,
    }
    return render(request, 'dashboard/instructor/student_detail.html', context)