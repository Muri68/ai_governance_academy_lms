from django.utils import timezone
from pyexpat.errors import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, DetailView, ListView
from apps.courses.models import Course, CourseCategory, Enrollment, Lesson, LessonContent, CourseReview, LessonProgress
from django.db.models import Avg, Count, Q

from apps.frontend.models import ContactMessage, SiteReview


class IndexView(TemplateView):
    template_name = 'frontend/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Welcome to Our LMS'
        
        # Get ALL published courses (no limit)
        all_courses = Course.objects.filter(
            status='published'
        ).select_related('instructor', 'category').prefetch_related('reviews')
        
        context['all_courses_count'] = all_courses.count()
        context['display_courses'] = all_courses[:6]
        
        # FIXED: Get ALL active categories (even without courses)
        context['categories'] = CourseCategory.objects.filter(
            is_active=True
        )
        
        # For debugging - you can remove this later
        print(f"Total active categories: {context['categories'].count()}")
        for cat in context['categories']:
            print(f"Category: {cat.name}, ID: {cat.id}, Slug: {cat.slug}")
        
        # FIXED: Featured courses - use badge='featured' instead of is_featured=True
        context['featured_courses'] = Course.objects.filter(
            status='published', badge='featured'
        ).select_related('instructor', 'category')[:6]
        
        # Free courses
        context['free_courses'] = Course.objects.filter(
            status='published', is_free=True
        ).select_related('instructor', 'category')[:6]
        
        context['site_reviews'] = SiteReview.objects.filter(
            is_approved=True
        ).select_related('user').order_by('-created_at')[:10]
        
        context['user_has_review'] = self.request.user.is_authenticated and SiteReview.objects.filter(
            user=self.request.user
        ).exists()
        
        context['total_courses'] = Course.objects.filter(status='published').count()
        
        return context


class AboutView(TemplateView):
    template_name = 'frontend/about.html'


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from apps.courses.models import Course, CourseCategory, Lesson, LessonContent, Enrollment, LessonProgress, CourseReview


class CoursesView(ListView):
    """All courses page with filtering"""
    model = Course
    template_name = 'frontend/courses.html'
    context_object_name = 'courses'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Course.objects.filter(status='published').select_related(
            'instructor', 'category'
        ).prefetch_related('reviews')
        
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(short_description__icontains=search)
            )
        
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        price_filter = self.request.GET.get('price')
        if price_filter == 'free':
            queryset = queryset.filter(is_free=True)
        elif price_filter == 'paid':
            queryset = queryset.filter(is_free=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Categories
        context['categories'] = CourseCategory.objects.filter(is_active=True)
        context['total_courses'] = Course.objects.filter(status='published').count()
        context['current_category'] = self.request.GET.get('category', '')
        context['current_search'] = self.request.GET.get('search', '')
        context['current_price'] = self.request.GET.get('price', '')
        
        # ===================== FEATURED COURSE =====================
        # Get featured course of the month using badge field (replaces is_featured)
        featured_course = Course.objects.filter(
            status='published',
            badge='featured'  # Use badge instead of is_featured
        ).select_related('instructor', 'category').first()
        
        # If no featured badge set, fallback to most recent published course
        if not featured_course:
            featured_course = Course.objects.filter(
                status='published'
            ).select_related('instructor', 'category').order_by('-created_at').first()
        
        context['featured_course'] = featured_course
        
        # ===================== TOP PICKS =====================
        # Get top picks (up to 3 courses with bestseller/trending/new badges)
        # Exclude the featured course from top picks
        exclude_ids = [featured_course.id] if featured_course else []
        
        # First, try to get courses with badges
        badge_courses = list(Course.objects.filter(
            status='published',
            badge__in=['bestseller', 'trending', 'new']
        ).exclude(
            id__in=exclude_ids
        ).select_related('instructor', 'category').order_by('-created_at')[:3])
        
        # Add badge course IDs to exclude list
        exclude_ids.extend([c.id for c in badge_courses])
        
        # If not enough badge courses, fill with recent published courses
        if len(badge_courses) < 3:
            # Get additional courses (excluding already selected ones)
            additional_needed = 3 - len(badge_courses)
            additional_courses = list(Course.objects.filter(
                status='published'
            ).exclude(
                id__in=exclude_ids
            ).select_related('instructor', 'category').order_by('-created_at')[:additional_needed])
            
            # Combine badge courses with additional courses
            top_picks = badge_courses + additional_courses
        else:
            top_picks = badge_courses
        
        context['top_picks'] = top_picks[:3]
        
        # ===================== ALL COURSES (for main listing) =====================
        # Exclude featured and top picks from the main course listing
        # so they don't appear twice
        featured_and_pick_ids = exclude_ids  # Already contains featured + badge course IDs
        # Also add additional course IDs that were used as top picks
        featured_and_pick_ids.extend([c.id for c in top_picks if c.id not in featured_and_pick_ids])
        
        # Store the filtered queryset for the template (optional)
        context['main_courses'] = self.get_queryset().exclude(
            id__in=featured_and_pick_ids
        ) if featured_and_pick_ids else self.get_queryset()
        
        return context


class CourseDetailView(DetailView):
    """Individual course detail page"""
    model = Course
    template_name = 'frontend/course_detail.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Course.objects.filter(
            status='published'
        ).select_related(
            'instructor', 'category'
        ).prefetch_related(
            'lessons__contents',
            'reviews__student',
            'enrollments'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        
        # Check if user is enrolled
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user,
                course=course,
                status__in=['active', 'completed']
            ).exists()
            
            # Get user's progress
            if context['is_enrolled']:
                enrollment = Enrollment.objects.get(
                    student=self.request.user,
                    course=course
                )
                context['enrollment'] = enrollment
                context['progress_percentage'] = enrollment.progress_percentage
        else:
            context['is_enrolled'] = False
        
        # Get reviews
        context['reviews'] = course.reviews.filter(
            is_approved=True
        ).select_related('student').order_by('-created_at')[:10]
        
        context['review_count'] = course.review_count
        context['average_rating'] = course.average_rating
        
        # Get lessons with content
        context['lessons'] = course.lessons.filter(
            is_published=True
        ).prefetch_related('contents').order_by('order')
        
        # Related courses (same category)
        if course.category:
            context['related_courses'] = Course.objects.filter(
                status='published',
                category=course.category
            ).exclude(
                id=course.id
            ).select_related('instructor').order_by('-created_at')[:4]
        
        # Check if featured
        context['is_featured'] = course.is_featured  # Uses the property
        
        return context



class CourseDetailView(DetailView):
    """Course detail page with access control, preview, and related courses"""
    model = Course
    template_name = 'frontend/course_detail.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Course.objects.filter(status='published').select_related(
            'instructor', 'instructor__instructor_profile', 'category'
        ).prefetch_related(
            'lessons__contents',
            'reviews__student',
            'enrollments'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user
        
        # ===================== LESSONS & PREVIEW =====================
        context['lessons'] = course.lessons.filter(
            is_published=True
        ).prefetch_related('contents').order_by('order')
        
        # Get preview/intro content (first few lessons or marked as preview)
        context['preview_lessons'] = course.lessons.filter(
            is_published=True,
            is_free_preview=True  # You need this field in Lesson model
        ).prefetch_related('contents').order_by('order')[:3]
        
        # If no preview lessons marked, take first 2 lessons as preview
        if not context['preview_lessons']:
            context['preview_lessons'] = course.lessons.filter(
                is_published=True
            ).prefetch_related('contents').order_by('order')[:2]
        
        # Get individual preview contents
        context['preview_contents'] = LessonContent.objects.filter(
            lesson__course=course,
            lesson__is_published=True,
            is_preview=True
        ).select_related('lesson').order_by('lesson__order', 'order')[:5]
        
        # ===================== ACCESS CONTROL =====================
        context['is_instructor_or_admin'] = (
            user.is_authenticated and 
            (
                user == course.instructor or 
                getattr(user, 'user_type', None) == 'ADMIN' or 
                user.is_superuser or 
                user.is_staff
            )
        )
        
        if user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=user, 
                course=course,
                status__in=['active', 'completed']
            ).exists()
        else:
            context['is_enrolled'] = False
        
        # IMPORTANT: Only enrolled users or instructor/admin can access content
        # No preview access for non-enrolled users
        context['can_access_content'] = (
            context['is_enrolled'] or 
            context['is_instructor_or_admin']
        )
        
        # ===================== COURSE INTRO / PREVIEW VIDEO =====================
        # Use trailer_url if available, otherwise first preview video
        context['intro_video_url'] = course.trailer_url
        if not context['intro_video_url']:
            # Try to find first preview video content
            first_preview = LessonContent.objects.filter(
                lesson__course=course,
                lesson__is_published=True,
                is_preview=True,
                content_type='video'
            ).first()
            if first_preview and first_preview.video_url:
                context['intro_video_url'] = first_preview.video_url
        
        # ===================== REVIEWS =====================
        context['reviews'] = course.reviews.select_related(
            'student'
        ).order_by('-created_at')[:10]
        context['review_count'] = course.review_count
        context['average_rating'] = course.average_rating
        
        # ===================== RELATED COURSES =====================
        # First try: same category
        if course.category:
            context['related_courses'] = Course.objects.filter(
                status='published',
                category=course.category
            ).exclude(id=course.id).select_related(
                'instructor', 'category'
            ).order_by('-created_at')[:4]
        
        # If no category courses, try: same instructor
        if not context.get('related_courses') and course.instructor:
            context['related_courses'] = Course.objects.filter(
                status='published',
                instructor=course.instructor
            ).exclude(id=course.id).select_related(
                'instructor', 'category'
            ).order_by('-created_at')[:4]
        
        # If still no courses, try: similar level
        if not context.get('related_courses'):
            context['related_courses'] = Course.objects.filter(
                status='published',
                level=course.level
            ).exclude(id=course.id).select_related(
                'instructor', 'category'
            ).order_by('-created_at')[:4]
        
        # Final fallback: recent published courses
        if not context.get('related_courses'):
            context['related_courses'] = Course.objects.filter(
                status='published'
            ).exclude(id=course.id).select_related(
                'instructor', 'category'
            ).order_by('-created_at')[:4]
        
        context['related_courses'] = context.get('related_courses', [])
        
        # Section title based on what we found
        if course.category and context['related_courses'] and context['related_courses'][0].category == course.category:
            context['related_title'] = f'More Courses in {course.category.name}'
        elif course.instructor and context['related_courses'] and context['related_courses'][0].instructor == course.instructor:
            context['related_title'] = f'More from {course.instructor.get_full_name()}'
        else:
            context['related_title'] = 'Similar Courses You Might Like'
        
        # ===================== LEARNING OUTCOMES =====================
        if course.what_you_learn:
            context['learning_outcomes'] = [
                line.strip('• -') for line in course.what_you_learn.split('\n') if line.strip()
            ]
        else:
            context['learning_outcomes'] = [
                "Understand core concepts and principles",
                "Apply practical skills in real-world scenarios",
                "Master industry-standard tools and techniques",
                "Build a portfolio of projects",
                "Prepare for relevant certifications",
            ]
        
        # ===================== INSTRUCTOR COURSES =====================
        if course.instructor:
            context['instructor_courses'] = Course.objects.filter(
                instructor=course.instructor, 
                status='published'
            ).exclude(id=course.id)[:4]
        
        return context


@login_required
def course_learning(request, slug):
    """Main course learning page"""
    course = get_object_or_404(
        Course.objects.prefetch_related('lessons__contents'),
        slug=slug,
        status='published'
    )
    
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    
    if not enrollment:
        enrollment = Enrollment.objects.create(student=request.user, course=course, status='active')
        messages.success(request, f'You have been enrolled in {course.title}! Start learning!')
    elif enrollment.status == 'completed':
        messages.info(request, f'You have completed {course.title}. Feel free to review!')
    elif enrollment.status != 'active':
        enrollment.status = 'active'
        enrollment.save()
        messages.success(request, f'Welcome back to {course.title}!')
    
    enrollment.last_accessed = timezone.now()
    enrollment.save()
    
    lessons = course.lessons.filter(is_published=True).order_by('order')
    
    lesson_id = request.GET.get('lesson')
    current_lesson = None
    
    if lesson_id:
        try:
            current_lesson = lessons.get(id=lesson_id)
        except Lesson.DoesNotExist:
            current_lesson = lessons.first() if lessons.exists() else None
    elif lessons.exists():
        current_lesson = lessons.first()
    
    lesson_contents = []
    if current_lesson:
        lesson_contents = current_lesson.contents.all().order_by('order')
    
    content_id = request.GET.get('content')
    current_content = None
    if current_lesson:
        if content_id:
            try:
                current_content = current_lesson.contents.get(id=content_id)
            except (LessonContent.DoesNotExist, ValueError):
                current_content = lesson_contents.first() if lesson_contents.exists() else None
        else:
            current_content = lesson_contents.first() if lesson_contents.exists() else None
    
    lesson_progress = {}
    completed_lesson_ids = set()
    
    if enrollment:
        for prog in LessonProgress.objects.filter(student=request.user, enrollment=enrollment):
            lesson_progress[prog.lesson_id] = prog
            if prog.completed:
                completed_lesson_ids.add(prog.lesson_id)
    
    total_lessons = lessons.count()
    completed_lessons = len(completed_lesson_ids)
    progress_percentage = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0
    
    enrollment.progress_percentage = progress_percentage
    enrollment.save()
    
    prev_lesson = None
    next_lesson = None
    if current_lesson and lessons.exists():
        lesson_list = list(lessons)
        try:
            idx = lesson_list.index(current_lesson)
            if idx > 0: prev_lesson = lesson_list[idx - 1]
            if idx < len(lesson_list) - 1: next_lesson = lesson_list[idx + 1]
        except ValueError:
            pass
    
    context = {
        'course': course, 'enrollment': enrollment, 'lessons': lessons,
        'current_lesson': current_lesson, 'lesson_contents': lesson_contents,
        'current_content': current_content,
        'lesson_progress': lesson_progress, 'completed_lesson_ids': completed_lesson_ids,
        'prev_lesson': prev_lesson, 'next_lesson': next_lesson,
        'progress_percentage': progress_percentage,
        'completed_lessons': completed_lessons, 'total_lessons': total_lessons,
    }
    return render(request, 'courses/learning.html', context)


def course_content_detail(request, slug, content_id):
    """AJAX endpoint for single content"""
    course = get_object_or_404(Course, slug=slug, status='published')
    content = get_object_or_404(LessonContent, id=content_id, lesson__course=course)
    lesson = content.lesson
    
    is_enrolled = request.user == course.instructor or Enrollment.objects.filter(
        student=request.user, course=course, status__in=['active', 'completed']
    ).exists()
    
    if not is_enrolled:
        return JsonResponse({'success': False, 'error': 'Not enrolled'}, status=403)
    
    data = {
        'success': True,
        'content_id': content.id,
        'content_title': content.title or content.get_content_type_display(),
        'content_type': content.content_type,
        'content_type_display': content.get_content_type_display(),
        'lesson_id': lesson.id,
        'lesson_title': lesson.title,
        'lesson_order': lesson.order,
        'text_content': content.text_content,
        'video_url': content.video_url,
        'video_file_url': content.video_file.url if content.video_file else None,
        'pdf_url': content.pdf_file.url if content.pdf_file else None,
        'duration_minutes': content.duration_minutes,
        'max_score': content.max_score,
        'quiz_data': content.quiz_data,
        'is_completed': LessonProgress.objects.filter(student=request.user, lesson=lesson, completed=True).exists(),
    }
    return JsonResponse(data)


class ContactView(TemplateView):
    template_name = 'frontend/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if name and email and subject and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
        else:
            messages.error(request, 'Please fill in all required fields.')
        
        return redirect(request.path)
    
    
    
from django.views.generic import TemplateView
from apps.dashboard.models import SiteSetting, FAQ


class PrivacyPolicyView(TemplateView):
    template_name = 'frontend/privacy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['privacy_content'] = SiteSetting.get_setting('privacy_policy', '')
        context['last_updated'] = SiteSetting.objects.filter(key='privacy_policy').first()
        return context


class TermsConditionsView(TemplateView):
    template_name = 'frontend/terms.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['terms_content'] = SiteSetting.get_setting('terms_conditions', '')
        context['last_updated'] = SiteSetting.objects.filter(key='terms_conditions').first()
        return context


class FAQView(TemplateView):
    template_name = 'frontend/faq.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faqs'] = FAQ.objects.filter(is_active=True).order_by('category', 'order')
        context['faq_categories'] = FAQ.CATEGORY_CHOICES
        return context
    
    
    
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import SiteReview


@login_required
def submit_site_review(request):
    """Handle site review submission - one review per user"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    
    rating = request.POST.get('rating')
    review_text = request.POST.get('review_text', '').strip()
    designation = request.POST.get('designation', '').strip()
    
    if not rating or not review_text:
        return JsonResponse({'success': False, 'message': 'Please provide both a rating and review.'})
    
    if len(review_text) < 10:
        return JsonResponse({'success': False, 'message': 'Please write at least 10 characters for your review.'})
    
    # Check if user already has a review
    existing_review = SiteReview.objects.filter(user=request.user).first()
    
    if existing_review:
        # Update existing review
        existing_review.rating = int(rating)
        existing_review.review_text = review_text
        existing_review.designation = designation
        existing_review.is_approved = False  # Re-approval needed after update
        existing_review.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Your review has been updated! It will be displayed after approval.',
            'updated': True
        })
    else:
        # Create new review
        SiteReview.objects.create(
            user=request.user,
            rating=int(rating),
            review_text=review_text,
            designation=designation,
            is_approved=False
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Thank you for your review! It will be displayed after approval by our team.',
            'updated': False
        })
        
        

from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import NewsletterSubscriber


@require_POST
def subscribe_newsletter(request):
    """AJAX endpoint for newsletter subscription"""
    email = request.POST.get('email', '').strip().lower()
    
    if not email:
        return JsonResponse({'success': False, 'message': 'Please enter your email address.'})
    
    # Basic email validation
    import re
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'})
    
    # Check if already subscribed
    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={'is_active': True}
    )
    
    if created:
        return JsonResponse({
            'success': True, 
            'message': 'Thank you for subscribing! You\'ll receive our latest updates and course announcements.',
            'new': True
        })
    else:
        if subscriber.is_active:
            return JsonResponse({
                'success': True, 
                'message': 'You\'re already subscribed! You\'ll continue receiving our updates.',
                'new': False
            })
        else:
            # Re-activate subscription
            subscriber.is_active = True
            subscriber.unsubscribed_at = None
            subscriber.save()
            return JsonResponse({
                'success': True, 
                'message': 'Welcome back! Your subscription has been reactivated.',
                'new': False
            })


@require_POST
def unsubscribe_newsletter(request):
    """AJAX endpoint for newsletter unsubscription"""
    email = request.POST.get('email', '').strip().lower()
    
    if not email:
        return JsonResponse({'success': False, 'message': 'Please enter your email address.'})
    
    try:
        subscriber = NewsletterSubscriber.objects.get(email=email, is_active=True)
        subscriber.unsubscribe()
        return JsonResponse({
            'success': True, 
            'message': 'You have been unsubscribed. We\'re sorry to see you go!'
        })
    except NewsletterSubscriber.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'This email is not subscribed to our newsletter.'
        })
        
        
        
# ERRORS PAGES
def error_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)

def error_503(request):
    return render(request, 'errors/503.html', status=503)

def error_401(request, exception=None):
    return render(request, 'errors/401.html', status=401)

def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


# In apps/frontend/views.py
def error_test_page(request):
    """Page with links to test all error pages"""
    return render(request, 'errors/test_errors.html')