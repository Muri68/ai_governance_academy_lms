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
        
        # Get active categories with course count
        context['categories'] = CourseCategory.objects.filter(
            is_active=True
        ).annotate(
            published_courses=Count('courses', filter=Q(courses__status='published'))
        ).filter(published_courses__gt=0)[:6]
        
        # Get published courses grouped by category for tabs
        context['all_courses'] = Course.objects.filter(
            status='published'
        ).select_related('instructor', 'category').prefetch_related('reviews')[:6]
        
        # Featured courses
        context['featured_courses'] = Course.objects.filter(
            status='published', is_featured=True
        ).select_related('instructor', 'category')[:6]
        
        # Free courses
        context['free_courses'] = Course.objects.filter(
            status='published', is_free=True
        ).select_related('instructor', 'category')[:6]
        
        context['site_reviews'] = SiteReview.objects.filter(is_approved=True).select_related('user').order_by('-created_at')[:10]
        context['user_has_review'] = self.request.user.is_authenticated and SiteReview.objects.filter(user=self.request.user).exists()
        
        # Total course count
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
        context['categories'] = CourseCategory.objects.filter(is_active=True)
        context['total_courses'] = Course.objects.filter(status='published').count()
        context['current_category'] = self.request.GET.get('category', '')
        context['current_search'] = self.request.GET.get('search', '')
        context['current_price'] = self.request.GET.get('price', '')
        return context


class CourseDetailView(DetailView):
    """Course detail page"""
    model = Course
    template_name = 'frontend/course_detail.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Course.objects.filter(status='published').select_related(
            'instructor', 'category'
        ).prefetch_related(
            'lessons__contents',
            'reviews__student',
            'enrollments'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        
        context['lessons'] = course.lessons.filter(is_published=True).prefetch_related('contents').order_by('order')
        context['reviews'] = course.reviews.select_related('student').order_by('-created_at')[:10]
        context['review_count'] = course.review_count
        context['average_rating'] = course.average_rating
        
        if course.category:
            context['related_courses'] = Course.objects.filter(
                status='published', category=course.category
            ).exclude(id=course.id).select_related('instructor', 'category')[:4]
        else:
            context['related_courses'] = Course.objects.filter(
                status='published'
            ).exclude(id=course.id).select_related('instructor', 'category')[:4]
        
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user, course=course,
                status__in=['active', 'completed']
            ).exists()
        else:
            context['is_enrolled'] = False
        
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
        
        if course.instructor:
            context['instructor_courses'] = Course.objects.filter(
                instructor=course.instructor, status='published'
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