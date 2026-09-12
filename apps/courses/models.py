from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone


class CourseCategory(models.Model):
    """Course categories like Cybersecurity, AI Ethics, Cloud Security etc."""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Font Awesome icon class e.g. 'fas fa-shield-alt'")
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Course Category'
        verbose_name_plural = 'Course Categories'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def course_count(self):
        return self.courses.filter(status='published').count()
    
    @property
    def total_course_count(self):
        """Total courses in this category (all statuses)"""
        return self.courses.count()
    
    @property
    def can_delete(self):
        """Check if category can be deleted (no courses assigned)"""
        return self.courses.count() == 0


from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.core.exceptions import ValidationError


from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from tinymce.models import HTMLField  # Use TinyMCE HTMLField


class Course(models.Model):
    """Main course model"""
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all', 'All Levels'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('review', 'In Review'),
    ]
    
    BADGE_CHOICES = [
        ('none', 'None'),
        ('bestseller', '🔥 Bestseller'),
        ('trending', '📈 Trending'),
        ('new', '✨ New'),
        ('featured', '⭐ Featured Course of the Month'),
    ]
    
    # Basic Info
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    description = HTMLField(blank=True, null=True, help_text="Full course description including requirements, what you'll learn, and course details")
    short_description = models.CharField(max_length=500, blank=True, null=True, help_text="Brief description for course cards")
    
    # Media
    featured_image = models.ImageField(upload_to='course_images/', blank=True, null=True)
    featured_video = models.FileField(upload_to='course_videos/', blank=True, null=True)
    trailer_url = models.URLField(max_length=500, blank=True, null=True, help_text="YouTube/Vimeo trailer link")
    
    # Relationships
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        related_name='teaching_courses',
        null=True,
        limit_choices_to={'user_type': 'INSTRUCTOR'}
    )
    category = models.ForeignKey(
        'CourseCategory', 
        on_delete=models.SET_NULL, 
        related_name='courses',
        null=True,
        blank=True
    )
    
    # Students enrolled
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Enrollment',
        related_name='enrolled_courses',
        blank=True
    )
    
    # Pricing (GBP - British Pounds)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price in GBP (£)")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Discounted price in GBP (£)")
    is_free = models.BooleanField(default=False)
    
    # Course Details
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='all')
    duration = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., '12 Weeks' or '24 Hours'")
    language = models.CharField(max_length=50, default='English')
    # REMOVED: requirements and what_you_learn fields (now part of description)
    
    # Certification
    has_certificate = models.BooleanField(default=False)
    certificate_template = models.FileField(upload_to='certificates/', blank=True, null=True)
    
    # Status & Visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Badge System
    badge = models.CharField(
        max_length=20, 
        choices=BADGE_CHOICES, 
        default='none',
        help_text="Badge displayed on course card (Bestseller, Trending, New, or Featured)"
    )
    badge_updated_at = models.DateTimeField(blank=True, null=True, help_text="When the badge was last updated")
    
    # Featured Date Tracking
    featured_at = models.DateTimeField(blank=True, null=True, help_text="When the course was marked as featured")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
            models.Index(fields=['instructor']),
            models.Index(fields=['category']),
            models.Index(fields=['badge']),
        ]
    
    @property
    def is_featured(self):
        """Check if course is currently featured based on badge"""
        return self.badge == 'featured'
    
    @property
    def price_display(self):
        """Return formatted price in GBP"""
        if self.is_free:
            return "Free"
        if self.discount_price:
            return f"£{self.discount_price:,.2f}"
        return f"£{self.price:,.2f}"
    
    @property
    def original_price_display(self):
        """Return original price in GBP (when discount exists)"""
        if self.discount_price and not self.is_free:
            return f"£{self.price:,.2f}"
        return None
    
    def clean(self):
        """Validate that only one course is featured at a time"""
        super().clean()
        if self.badge == 'featured':
            existing_featured = Course.objects.filter(
                badge='featured'
            ).exclude(pk=self.pk).first()
            if existing_featured:
                raise ValidationError({
                    'badge': f'Only one course can be featured at a time. "{existing_featured.title}" is currently the featured course. Please remove the featured badge from that course first.'
                })
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Handle featured badge logic
        if self.badge == 'featured':
            Course.objects.filter(badge='featured').exclude(pk=self.pk).update(
                badge='none',
                badge_updated_at=None,
                featured_at=None
            )
            if not self.featured_at:
                self.featured_at = timezone.now()
        
        # Handle badge timestamp
        if self.badge != 'none' and not self.badge_updated_at:
            self.badge_updated_at = timezone.now()
        elif self.badge == 'none':
            self.badge_updated_at = None
            self.featured_at = None
        
        # Publish logic
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        # Free course logic
        if self.is_free:
            self.price = 0.00
            self.discount_price = None
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def total_lessons(self):
        return self.lessons.count()
    
    @property
    def total_students(self):
        """Count of ALL enrollments (active + completed)"""
        return self.enrollments.filter(status__in=['active', 'completed']).count()
    
    @property
    def average_rating(self):
        """Average rating from reviews"""
        from django.db.models import Avg
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0
    
    @property
    def review_count(self):
        return self.reviews.count()
    
    @property
    def total_duration(self):
        """Calculate total duration of all video lessons"""
        total = timezone.timedelta()
        for lesson in self.lessons.all():
            for content in lesson.contents.filter(content_type='video', time_duration__isnull=False):
                total += content.time_duration
        return total
    
    @property
    def is_bestseller(self):
        return self.badge == 'bestseller'
    
    @property
    def is_trending(self):
        return self.badge == 'trending'
    
    @property
    def is_new(self):
        return self.badge == 'new'
    
    @property
    def badge_display(self):
        """Return the display text for the badge"""
        badge_map = {
            'none': None,
            'bestseller': '🔥 Bestseller',
            'trending': '📈 Trending',
            'new': '✨ New',
            'featured': '⭐ Featured Course of the Month',
        }
        return badge_map.get(self.badge)
    
    @property
    def badge_css_class(self):
        """Return the CSS class for the badge"""
        css_map = {
            'none': '',
            'bestseller': 'tp-badge-hot',
            'trending': 'tp-badge-trending',
            'new': 'tp-badge-new',
            'featured': 'tp-badge-featured',
        }
        return css_map.get(self.badge, '')

        

class Lesson(models.Model):
    """Individual lessons within a course"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_free_preview = models.BooleanField(default=False, help_text="Allow non-enrolled students to preview")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['order', 'created_at']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.order}. {self.title}"
    
    @property
    def content_count(self):
        return self.contents.count()


# class LessonContent(models.Model):
#     """Content items within a lesson (video, text, PDF, quiz)"""
#     CONTENT_TYPE_CHOICES = [
#         ('video', 'Video'),
#         ('video_url', 'Video URL (YouTube/Vimeo)'),
#         ('text', 'Text/Article'),
#         ('pdf', 'PDF Document'),
#         ('quiz', 'Quiz/Assessment'),
#         ('assignment', 'Assignment'),
#         ('code', 'Code Exercise'),
#         ('slides', 'Presentation Slides'),
#     ]
    
#     lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='contents')
#     content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
#     title = models.CharField(max_length=300, blank=True, null=True)
#     order = models.PositiveIntegerField(default=0)
    
#     # Media fields
#     thumbnail = models.ImageField(upload_to='lesson_thumbnails/', blank=True, null=True)
#     video_file = models.FileField(upload_to='lesson_videos/', blank=True, null=True, help_text="Upload video file")
#     video_url = models.URLField(max_length=500, blank=True, null=True, help_text="YouTube/Vimeo embed URL")
#     pdf_file = models.FileField(upload_to='lesson_pdfs/', blank=True, null=True, help_text="Upload PDF document")
#     text_content = models.TextField(blank=True, null=True, help_text="Rich text content for text/quiz types")
#     allow_download = models.BooleanField(default=False, help_text="Allow students to download this content")
    
#     # Video duration (for video types)
#     time_duration = models.DurationField(blank=True, null=True, help_text="e.g., 00:15:30 for 15 minutes 30 seconds")
#     duration_minutes = models.PositiveIntegerField(blank=True, null=True, help_text="Duration in minutes")
    
#     # For quiz types
#     quiz_data = models.JSONField(blank=True, null=True, help_text="Quiz questions and answers in JSON format")
#     passing_score = models.PositiveIntegerField(default=60, help_text="Passing percentage for quizzes")
    
#     # For assignment types
#     assignment_instructions = models.TextField(blank=True, null=True)
#     max_score = models.PositiveIntegerField(default=100)
    
#     # Settings
#     is_preview = models.BooleanField(default=False, help_text="Allow preview without enrollment")
#     is_required = models.BooleanField(default=True, help_text="Must complete to finish lesson")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         verbose_name = 'Lesson Content'
#         verbose_name_plural = 'Lesson Contents'
#         ordering = ['order']
    
#     def __str__(self):
#         return f"{self.lesson.title} - {self.get_content_type_display()}"
    
#     @property
#     def content_type_icon(self):
#         """Return appropriate icon for content type"""
#         icons = {
#             'video': 'fas fa-play-circle',
#             'video_url': 'fas fa-link',
#             'text': 'fas fa-file-alt',
#             'pdf': 'fas fa-file-pdf',
#             'quiz': 'fas fa-question-circle',
#             'assignment': 'fas fa-tasks',
#             'code': 'fas fa-code',
#             'slides': 'fas fa-desktop',
#         }
#         return icons.get(self.content_type, 'fas fa-file')
    
#     @property
#     def has_content(self):
#         """Check if content has any material"""
#         if self.content_type in ['video', 'video_url']:
#             return bool(self.video_file or self.video_url)
#         elif self.content_type == 'pdf':
#             return bool(self.pdf_file)
#         elif self.content_type in ['text', 'quiz', 'code']:
#             return bool(self.text_content)
#         return True

class LessonContent(models.Model):
    """Content items within a lesson (video, text, PDF)"""
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('video_url', 'Video URL (YouTube/Vimeo)'),
        ('text', 'Text/Article'),
        ('pdf', 'PDF Document'),
        ('assignment', 'Assignment'),
        ('code', 'Code Exercise'),
        ('slides', 'Presentation Slides'),
    ]
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='contents')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    title = models.CharField(max_length=300, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    
    # Media fields
    thumbnail = models.ImageField(upload_to='lesson_thumbnails/', blank=True, null=True)
    video_file = models.FileField(upload_to='lesson_videos/', blank=True, null=True, help_text="Upload video file")
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="YouTube/Vimeo embed URL")
    pdf_file = models.FileField(upload_to='lesson_pdfs/', blank=True, null=True, help_text="Upload PDF document")
    text_content = models.TextField(blank=True, null=True, help_text="Rich text content for text/code types")
    allow_download = models.BooleanField(default=False, help_text="Allow students to download this content")
    
    # Video duration (for video types)
    time_duration = models.DurationField(blank=True, null=True, help_text="e.g., 00:15:30 for 15 minutes 30 seconds")
    duration_minutes = models.PositiveIntegerField(blank=True, null=True, help_text="Duration in minutes")
    
    # For assignment types
    assignment_instructions = models.TextField(blank=True, null=True)
    max_score = models.PositiveIntegerField(default=100)
    
    # Settings
    is_preview = models.BooleanField(default=False, help_text="Allow preview without enrollment")
    is_required = models.BooleanField(default=True, help_text="Must complete to finish lesson")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Lesson Content'
        verbose_name_plural = 'Lesson Contents'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.lesson.title} - {self.get_content_type_display()}"
    
    @property
    def content_type_icon(self):
        """Return appropriate icon for content type"""
        icons = {
            'video': 'fas fa-play-circle',
            'video_url': 'fas fa-link',
            'text': 'fas fa-file-alt',
            'pdf': 'fas fa-file-pdf',
            'assignment': 'fas fa-tasks',
            'code': 'fas fa-code',
            'slides': 'fas fa-desktop',
        }
        return icons.get(self.content_type, 'fas fa-file')
    
    @property
    def has_content(self):
        """Check if content has any material"""
        if self.content_type in ['video', 'video_url']:
            return bool(self.video_file or self.video_url)
        elif self.content_type == 'pdf':
            return bool(self.pdf_file)
        elif self.content_type in ['text', 'code']:
            return bool(self.text_content)
        return True




class Enrollment(models.Model):
    """Track student enrollment in courses"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('paused', 'Paused'),
    ]
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    progress_percentage = models.PositiveIntegerField(default=0)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_accessed = models.DateTimeField(auto_now=True)
    certificate_issued = models.BooleanField(default=False)
    certificate_url = models.URLField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.email} - {self.course.title}"
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def completed_lessons(self):
        """Return number of completed lessons"""
        return self.progress.filter(completed=True).count()


class LessonProgress(models.Model):
    """Track student progress on individual lessons"""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='progress')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    time_spent = models.DurationField(default=timezone.timedelta)
    last_accessed = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Lesson Progress'
        verbose_name_plural = 'Lesson Progress'
        unique_together = ['student', 'lesson']
    
    def __str__(self):
        return f"{self.student.email} - {self.lesson.title}"


class CourseReview(models.Model):
    """Student reviews and ratings for courses"""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200, blank=True, null=True)
    review = models.TextField(blank=True, null=True)
    is_recommended = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Course Review'
        verbose_name_plural = 'Course Reviews'
        unique_together = ['student', 'course']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.email} - {self.course.title} ({self.rating}★)"


class CourseAnnouncement(models.Model):
    """Announcements for enrolled students"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=300)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Course Announcement'
        verbose_name_plural = 'Course Announcements'
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    



class FeaturedCourse(models.Model):
    """Featured Course of the Month - Only ONE active at a time"""
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE,
        related_name='featured_entries'
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def clean(self):
        if self.is_active:
            # Ensure only one active featured course
            active = FeaturedCourse.objects.filter(
                is_active=True
            ).exclude(pk=self.pk).exists()
            if active:
                raise ValidationError(
                    'Only one course can be featured at a time.'
                )


class TopPick(models.Model):
    """Top Picks of the Month - Multiple courses allowed"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='top_picks'
    )
    position = models.PositiveIntegerField(default=0)  # For ordering
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['position']
        unique_together = ['course', 'is_active']  # Avoid duplicates



class Quiz(models.Model):
    """Quiz associated with a lesson"""
    lesson = models.ForeignKey(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='quizzes',
        help_text="The lesson this quiz belongs to"
    )
    title = models.CharField(max_length=300, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    passing_score = models.PositiveIntegerField(default=60, help_text="Passing percentage")
    allow_retake = models.BooleanField(default=True)
    time_limit = models.PositiveIntegerField(blank=True, null=True, help_text="Time limit in minutes")
    randomize_questions = models.BooleanField(default=True, help_text="Randomize question order for each attempt")
    randomize_answers = models.BooleanField(default=True, help_text="Randomize answer options for each question")
    questions_per_attempt = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        help_text="Number of random questions to show (leave empty to show all)"
    )
    show_correct_answers = models.BooleanField(default=True, help_text="Show correct answers after submission")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Quiz: {self.title or f'Lesson {self.lesson.order}'}"
    
    @property
    def question_count(self):
        return self.questions.count()
    
    @property
    def total_points(self):
        return self.questions.aggregate(total=models.Sum('points'))['total'] or 0
    
    def get_randomized_questions(self, user=None):
        """Get randomized questions for a quiz attempt"""
        questions = list(self.questions.filter(is_active=True))
        
        # Randomize question order
        if self.randomize_questions:
            import random
            random.shuffle(questions)
        
        # Select subset if questions_per_attempt is set
        if self.questions_per_attempt and self.questions_per_attempt < len(questions):
            import random
            questions = random.sample(questions, self.questions_per_attempt)
        
        # Randomize answers within each question
        if self.randomize_answers:
            for question in questions:
                question.randomized_answers = question.get_randomized_answers()
        else:
            for question in questions:
                question.randomized_answers = list(question.answers.all())
        
        return questions


class QuizQuestion(models.Model):
    """Individual question in a quiz"""
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True, null=True, help_text="Explanation shown after answering")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"
    
    @property
    def correct_answer(self):
        return self.answers.filter(is_correct=True).first()
    
    def get_randomized_answers(self):
        """Get answers in random order"""
        import random
        answers = list(self.answers.all())
        if self.quiz.randomize_answers:
            random.shuffle(answers)
        return answers


class QuizAnswer(models.Model):
    """Possible answer for a quiz question"""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.answer_text[:50]} ({'Correct' if self.is_correct else 'Wrong'})"


class QuizAttempt(models.Model):
    """Student's attempt at a quiz"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.quiz.title} - {self.score}%"
    
    @property
    def percentage(self):
        if self.quiz.total_points > 0:
            return round((float(self.score) / self.quiz.total_points) * 100, 2)
        return 0
    
    def save(self, *args, **kwargs):
        if self.completed_at and not self.pk:
            # Check if passed based on quiz's passing score
            self.passed = self.percentage >= self.quiz.passing_score
            
            # If passed, mark the lesson as complete
            if self.passed:
                from django.utils import timezone
                LessonProgress.objects.update_or_create(
                    student=self.student,
                    lesson=self.quiz.lesson,
                    defaults={
                        'completed': True,
                        'completed_at': timezone.now(),
                    }
                )
        super().save(*args, **kwargs)


class QuizAnswerRecord(models.Model):
    """Student's answer to a specific question in an attempt"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answer_records')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(QuizAnswer, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.attempt.student.get_full_name()} - Q{self.question.order}"




class FinalExam(models.Model):
    """Final examination required for course completion and certificate"""
    course = models.OneToOneField(
        Course, 
        on_delete=models.CASCADE, 
        related_name='final_exam',
        help_text="The course this final exam belongs to"
    )
    title = models.CharField(max_length=300, default="Final Examination")
    description = models.TextField(blank=True, null=True)
    passing_score = models.PositiveIntegerField(default=70, help_text="Passing percentage for final exam")
    time_limit = models.PositiveIntegerField(default=30, help_text="Time limit in minutes")
    max_attempts = models.PositiveIntegerField(default=3, help_text="Maximum number of attempts allowed")
    randomize_questions = models.BooleanField(default=True)
    randomize_answers = models.BooleanField(default=True)
    questions_per_attempt = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Number of random questions per attempt (leave empty for all)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Final Exam'
        verbose_name_plural = 'Final Exams'
    
    def __str__(self):
        return f"Final Exam: {self.course.title}"
    
    @property
    def question_count(self):
        return self.questions.count()
    
    @property
    def total_points(self):
        return self.questions.aggregate(total=models.Sum('points'))['total'] or 0
    
    def get_randomized_questions(self, user=None):
        """Get randomized questions for exam attempt"""
        import random
        questions = list(self.questions.filter(is_active=True))
        
        if self.randomize_questions:
            random.shuffle(questions)
        
        if self.questions_per_attempt and self.questions_per_attempt < len(questions):
            questions = random.sample(questions, self.questions_per_attempt)
        
        if self.randomize_answers:
            for question in questions:
                question.randomized_answers = question.get_randomized_answers()
        else:
            for question in questions:
                question.randomized_answers = list(question.answers.all())
        
        return questions


class FinalExamQuestion(models.Model):
    """Questions for final exam"""
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]
    
    exam = models.ForeignKey(FinalExam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Exam Q{self.order}: {self.question_text[:50]}"
    
    def get_randomized_answers(self):
        import random
        answers = list(self.answers.all())
        if self.exam.randomize_answers:
            random.shuffle(answers)
        return answers


class FinalExamAnswer(models.Model):
    """Answers for final exam questions"""
    question = models.ForeignKey(FinalExamQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.answer_text[:50]} ({'Correct' if self.is_correct else 'Wrong'})"


class FinalExamAttempt(models.Model):
    """Student's attempt at final exam"""
    exam = models.ForeignKey(FinalExam, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='final_exam_attempts')
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    time_taken = models.DurationField(blank=True, null=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.exam.title} - {self.score}%"
    
    @property
    def percentage(self):
        if self.exam.total_points > 0:
            return round((float(self.score) / self.exam.total_points) * 100, 2)
        return 0
    
    @property
    def remaining_attempts(self):
        if not self.exam.max_attempts:
            return None
        used = self.exam.attempts.filter(student=self.student).count()
        return max(0, self.exam.max_attempts - used)


class FinalExamAnswerRecord(models.Model):
    """Student's answer to a specific final exam question"""
    attempt = models.ForeignKey(FinalExamAttempt, on_delete=models.CASCADE, related_name='answer_records')
    question = models.ForeignKey(FinalExamQuestion, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(FinalExamAnswer, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.attempt.student.get_full_name()} - Exam Q{self.question.order}"