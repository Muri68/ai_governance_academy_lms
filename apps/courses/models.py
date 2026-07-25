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
    
    # Basic Info
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
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
        CourseCategory, 
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
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_free = models.BooleanField(default=False)
    
    # Course Details
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='all')
    duration = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., '12 Weeks' or '24 Hours'")
    language = models.CharField(max_length=50, default='English')
    requirements = models.TextField(blank=True, null=True, help_text="Prerequisites for the course")
    what_you_learn = models.TextField(blank=True, null=True, help_text="Learning outcomes (one per line)")
    
    # Certification
    has_certificate = models.BooleanField(default=False)
    certificate_template = models.FileField(upload_to='certificates/', blank=True, null=True)
    
    # Status & Visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    
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
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        if self.is_free:
            self.price = 0.00
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def total_lessons(self):
        return self.lessons.count()
    
    @property
    def total_students(self):
        """Count of active enrollments"""
        return self.enrollments.filter(status='active').count()
    
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
    def progress_percentage(self):
        """Overall course completion percentage"""
        total = self.lessons.count()
        if total == 0:
            return 0
        return 0  # Per-student calculation would go here
    
    @property
    def total_students(self):
        """Count of ALL enrollments (active + completed)"""
        return self.enrollments.filter(status__in=['active', 'completed']).count()


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


class LessonContent(models.Model):
    """Content items within a lesson (video, text, PDF, quiz)"""
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('video_url', 'Video URL (YouTube/Vimeo)'),
        ('text', 'Text/Article'),
        ('pdf', 'PDF Document'),
        ('quiz', 'Quiz/Assessment'),
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
    text_content = models.TextField(blank=True, null=True, help_text="Rich text content for text/quiz types")
    allow_download = models.BooleanField(default=False, help_text="Allow students to download this content")
    
    # Video duration (for video types)
    time_duration = models.DurationField(blank=True, null=True, help_text="e.g., 00:15:30 for 15 minutes 30 seconds")
    duration_minutes = models.PositiveIntegerField(blank=True, null=True, help_text="Duration in minutes")
    
    # For quiz types
    quiz_data = models.JSONField(blank=True, null=True, help_text="Quiz questions and answers in JSON format")
    passing_score = models.PositiveIntegerField(default=60, help_text="Passing percentage for quizzes")
    
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
            'quiz': 'fas fa-question-circle',
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
        elif self.content_type in ['text', 'quiz', 'code']:
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