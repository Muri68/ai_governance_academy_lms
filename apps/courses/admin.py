from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    CourseCategory, Course, Lesson, LessonContent, 
    Enrollment, LessonProgress, CourseReview, CourseAnnouncement, Quiz, QuizQuestion, QuizAnswer, Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizAnswerRecord, FinalExam,
    FinalExamQuestion, FinalExamAnswer, FinalExamAttempt, FinalExamAnswerRecord,
)

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    FinalExam, FinalExamQuestion, FinalExamAnswer, 
    FinalExamAttempt, FinalExamAnswerRecord
)


class FinalExamAnswerInline(admin.TabularInline):
    """Inline answers for final exam questions"""
    model = FinalExamAnswer
    extra = 4
    fields = ['answer_text', 'is_correct', 'order']
    ordering = ['order']


class FinalExamQuestionInline(admin.StackedInline):
    """Inline questions for final exam"""
    model = FinalExamQuestion
    extra = 1
    fields = ['question_text', 'question_type', 'points', 'order', 'explanation', 'is_active']
    show_change_link = True
    ordering = ['order']
    classes = ['collapse']  # Collapsed by default to keep admin clean


@admin.register(FinalExam)
class FinalExamAdmin(admin.ModelAdmin):
    """Final Exam admin configuration"""
    list_display = [
        'title', 'course', 'question_count', 'passing_score', 
        'time_limit', 'max_attempts', 'total_points', 
        'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'course__category', 'randomize_questions', 
        'randomize_answers', 'course__status'
    ]
    search_fields = [
        'title', 'course__title', 'description',
        'course__instructor__first_name', 'course__instructor__last_name'
    ]
    inlines = [FinalExamQuestionInline]
    list_select_related = ['course', 'course__instructor']
    save_on_top = True
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Exam Information', {
            'fields': ('course', 'title', 'description', 'is_active')
        }),
        ('Exam Settings', {
            'fields': ('passing_score', 'time_limit', 'max_attempts')
        }),
        ('Randomization', {
            'fields': ('randomize_questions', 'randomize_answers', 'questions_per_attempt'),
            'description': 'Configure how questions and answers are randomized for each attempt'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_count(self, obj):
        """Display number of questions"""
        count = obj.questions.count()
        active = obj.questions.filter(is_active=True).count()
        if count > 0:
            return format_html('{} <small>({} active)</small>', count, active)
        return 0
    question_count.short_description = 'Questions'
    question_count.admin_order_field = 'questions__count'
    
    def total_points(self, obj):
        """Display total points for the exam"""
        return obj.total_points
    total_points.short_description = 'Total Points'
    
    def get_queryset(self, request):
        """Optimize queryset for better performance"""
        return super().get_queryset(request).prefetch_related(
            'questions', 'questions__answers'
        )
    
    def save_model(self, request, obj, form, change):
        """Set default title if not provided"""
        if not obj.title or obj.title == "Final Examination":
            obj.title = f"Final Examination - {obj.course.title}"
        super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        """Validate questions after saving"""
        super().save_related(request, form, formsets, change)
        
        # Validate that each question has at least one correct answer
        for question in form.instance.questions.all():
            if question.question_type in ['multiple_choice', 'true_false']:
                if not question.answers.filter(is_correct=True).exists():
                    from django.contrib import messages
                    messages.warning(
                        request,
                        f'⚠️ Question "{question.question_text[:30]}..." has no correct answer marked!'
                    )


@admin.register(FinalExamQuestion)
class FinalExamQuestionAdmin(admin.ModelAdmin):
    """Final Exam Question admin configuration"""
    list_display = [
        'question_text_preview', 'exam', 'question_type', 
        'points', 'answer_count', 'correct_answer_count', 
        'order', 'is_active'
    ]
    list_filter = [
        'question_type', 'is_active', 'exam__course__category',
        'exam__is_active'
    ]
    search_fields = [
        'question_text', 'exam__title', 'exam__course__title'
    ]
    inlines = [FinalExamAnswerInline]
    list_select_related = ['exam', 'exam__course']
    save_on_top = True
    ordering = ['exam', 'order']
    
    def question_text_preview(self, obj):
        """Show truncated question text"""
        return obj.question_text[:60] + ('...' if len(obj.question_text) > 60 else '')
    question_text_preview.short_description = 'Question'
    
    def answer_count(self, obj):
        """Count total answers"""
        return obj.answers.count()
    answer_count.short_description = 'Answers'
    
    def correct_answer_count(self, obj):
        """Count correct answers"""
        count = obj.answers.filter(is_correct=True).count()
        if count == 0:
            return format_html('<span style="color: #ef4444;">⚠️ {}</span>', count)
        elif count == 1:
            return format_html('<span style="color: #10b981;">✓ {}</span>', count)
        else:
            return format_html('<span style="color: #f59e0b;">{}</span>', count)
    correct_answer_count.short_description = 'Correct'
    
    def save_related(self, request, form, formsets, change):
        """Validate answers"""
        super().save_related(request, form, formsets, change)
        
        question = form.instance
        if question.question_type in ['multiple_choice', 'true_false']:
            correct_count = question.answers.filter(is_correct=True).count()
            if correct_count == 0:
                from django.contrib import messages
                messages.warning(request, '⚠️ This question has no correct answer marked!')
            elif correct_count > 1 and question.question_type == 'true_false':
                from django.contrib import messages
                messages.warning(request, '⚠️ True/False question should have exactly one correct answer!')


@admin.register(FinalExamAnswer)
class FinalExamAnswerAdmin(admin.ModelAdmin):
    """Final Exam Answer admin configuration"""
    list_display = [
        'answer_text_preview', 'question', 'exam_title', 
        'is_correct', 'order'
    ]
    list_filter = ['is_correct', 'question__exam']
    search_fields = [
        'answer_text', 'question__question_text', 
        'question__exam__title'
    ]
    list_select_related = ['question', 'question__exam', 'question__exam__course']
    
    def answer_text_preview(self, obj):
        """Show truncated answer text"""
        return obj.answer_text[:60] + ('...' if len(obj.answer_text) > 60 else '')
    answer_text_preview.short_description = 'Answer'
    
    def exam_title(self, obj):
        """Show exam title"""
        return obj.question.exam.title
    exam_title.short_description = 'Exam'


@admin.register(FinalExamAttempt)
class FinalExamAttemptAdmin(admin.ModelAdmin):
    """Final Exam Attempt admin configuration"""
    list_display = [
        'student', 'exam', 'percentage', 'passed', 
        'time_taken_display', 'started_at', 'completed_at'
    ]
    list_filter = [
        'passed', 'exam', 'started_at', 'exam__course'
    ]
    search_fields = [
        'student__email', 'student__first_name', 
        'student__last_name', 'exam__title', 'exam__course__title'
    ]
    list_select_related = ['student', 'exam', 'exam__course']
    readonly_fields = [
        'score', 'passed', 'started_at', 'completed_at', 'time_taken'
    ]
    date_hierarchy = 'started_at'
    
    def percentage(self, obj):
        """Show percentage with color"""
        color = '#10b981' if obj.passed else '#ef4444'
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}%</span>',
            color, obj.percentage
        )
    percentage.short_description = 'Score'
    
    def time_taken_display(self, obj):
        """Format time taken nicely"""
        if obj.time_taken:
            total_seconds = int(obj.time_taken.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"
        return '-'
    time_taken_display.short_description = 'Time Taken'
    
    def has_add_permission(self, request):
        """Prevent manual creation of attempts"""
        return False


@admin.register(FinalExamAnswerRecord)
class FinalExamAnswerRecordAdmin(admin.ModelAdmin):
    """Final Exam Answer Record admin configuration"""
    list_display = [
        'attempt_student', 'question_preview', 'selected_answer', 
        'is_correct', 'points_earned'
    ]
    list_filter = ['is_correct', 'attempt__exam', 'attempt__passed']
    search_fields = [
        'attempt__student__email', 'question__question_text',
        'selected_answer__answer_text'
    ]
    list_select_related = [
        'attempt', 'attempt__student', 'question', 'selected_answer'
    ]
    readonly_fields = [
        'attempt', 'question', 'selected_answer', 
        'text_answer', 'is_correct', 'points_earned'
    ]
    
    def attempt_student(self, obj):
        """Show student name"""
        return obj.attempt.student.get_full_name()
    attempt_student.short_description = 'Student'
    
    def question_preview(self, obj):
        """Show truncated question"""
        return obj.question.question_text[:50] + ('...' if len(obj.question.question_text) > 50 else '')
    question_preview.short_description = 'Question'
    
    def has_add_permission(self, request):
        """Prevent manual creation of answer records"""
        return False


# admin.py
from django.contrib import admin
from .models import Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizAnswerRecord

class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 4

class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1
    inlines = [QuizAnswerInline]

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'passing_score', 'is_active', 'question_count']
    list_filter = ['is_active', 'lesson']
    inlines = [QuizQuestionInline]

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'question_type', 'points', 'is_active']
    inlines = [QuizAnswerInline]

@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['answer_text', 'question', 'is_correct']
    


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'percentage', 'passed', 'started_at', 'completed_at']
    list_filter = ['passed', 'quiz__lesson__course', 'started_at']
    search_fields = ['student__email', 'student__first_name', 'quiz__title']
    readonly_fields = ['score', 'passed', 'started_at', 'completed_at']
    list_select_related = ['student', 'quiz', 'quiz__lesson']


@admin.register(QuizAnswerRecord)
class QuizAnswerRecordAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question_preview', 'selected_answer', 'is_correct', 'points_earned']
    list_filter = ['is_correct', 'attempt__quiz']
    search_fields = ['attempt__student__email', 'question__question_text']
    readonly_fields = ['attempt', 'question', 'selected_answer', 'text_answer', 'is_correct', 'points_earned']
    
    def question_preview(self, obj):
        return obj.question.question_text[:30]
    question_preview.short_description = 'Question'

    



    




class LessonContentInline(admin.TabularInline):
    model = LessonContent
    extra = 0
    fields = ['content_type', 'title', 'order', 'time_duration', 'is_preview', 'is_required', 'allow_download']


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 0
    show_change_link = True
    fields = ['title', 'order', 'is_free_preview', 'is_published']


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'course_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Courses'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'instructor', 'category', 'get_badge_display',
        'status', 'price', 'get_students', 
        'get_rating', 'created_at'
    ]
    list_filter = [
        'status', 'badge', 'level', 'category', 
        'is_free', 'has_certificate'
    ]
    search_fields = [
        'title', 'description', 'instructor__email', 
        'instructor__first_name', 'instructor__last_name'
    ]
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'created_at', 'updated_at', 'published_at', 
        'badge_updated_at'
    ]
    inlines = [LessonInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'category', 'instructor')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_video', 'trailer_url')
        }),
        ('Pricing', {
            'fields': ('is_free', 'price', 'discount_price')
        }),
        ('Course Details', {
            'fields': ('level', 'duration', 'language')
        }),
        ('Badge & Featured Status', {
            'fields': ('badge', 'badge_updated_at'),
            'description': (
                '<div style="background:#f0fdf4;border:1px solid #10b981;padding:12px 16px;border-radius:8px;">'
                '<strong style="color:#10b981;">🎨 Badge Options:</strong><br>'
                '• <strong>🔥 Bestseller</strong> — For top-selling courses<br>'
                '• <strong>📈 Trending</strong> — For rapidly growing courses<br>'
                '• <strong>✨ New</strong> — For recently launched courses<br>'
                '• <strong>⭐ Featured Course of the Month</strong> — For the featured course<br>'
                '• <strong>None</strong> — No badge displayed</div>'
            )
        }),
        ('Status & Visibility', {
            'fields': ('status', 'has_certificate', 'certificate_template')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_badge_display(self, obj):
        """Display badge with icon in admin list"""
        badge_map = {
            'none': '—',
            'bestseller': '🔥 Bestseller',
            'trending': '📈 Trending',
            'new': '✨ New',
            'featured': '⭐ Featured',
        }
        return badge_map.get(obj.badge, '—')
    get_badge_display.short_description = 'Badge'
    get_badge_display.admin_order_field = 'badge'
    
    def get_students(self, obj):
        return obj.total_students
    get_students.short_description = 'Students'
    
    def get_rating(self, obj):
        avg = obj.average_rating
        return f"{avg}★" if avg else "—"
    get_rating.short_description = 'Rating'
    
    def save_model(self, request, obj, form, change):
        """Handle badge logic with admin messages"""
        try:
            is_newly_featured = False
            was_previously_featured = False
            
            if change:
                original = Course.objects.get(pk=obj.pk)
                # Check if badge changed to featured
                if obj.badge == 'featured' and original.badge != 'featured':
                    is_newly_featured = True
                # Check if featured badge is being removed
                if original.badge == 'featured' and obj.badge != 'featured':
                    was_previously_featured = True
            
            # Run the model's save method which handles the logic
            super().save_model(request, obj, form, change)
            
            if is_newly_featured:
                messages.success(
                    request,
                    f'⭐ "{obj.title}" is now the Featured Course of the Month!'
                )
            elif was_previously_featured and obj.badge != 'featured':
                messages.info(
                    request,
                    f'ℹ️ "{obj.title}" is no longer the Featured Course.'
                )
                
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    for error in errors:
                        messages.error(request, f'❌ {error}')
            else:
                messages.error(request, str(e))
    
    # ===================== BULK ACTIONS =====================
    
    @admin.action(description='🔥 Mark selected courses as Bestseller')
    def make_bestseller(self, request, queryset):
        updated = queryset.update(
            badge='bestseller',
            badge_updated_at=timezone.now()
        )
        self.message_user(request, f'✅ {updated} course(s) marked as 🔥 Bestseller.')
    
    @admin.action(description='📈 Mark selected courses as Trending')
    def make_trending(self, request, queryset):
        updated = queryset.update(
            badge='trending',
            badge_updated_at=timezone.now()
        )
        self.message_user(request, f'✅ {updated} course(s) marked as 📈 Trending.')
    
    @admin.action(description='✨ Mark selected courses as New')
    def make_new(self, request, queryset):
        updated = queryset.update(
            badge='new',
            badge_updated_at=timezone.now()
        )
        self.message_user(request, f'✅ {updated} course(s) marked as ✨ New.')
    
    @admin.action(description='⭐ Set as Featured Course of the Month')
    def make_featured(self, request, queryset):
        """Set the first selected course as featured"""
        if queryset.count() > 1:
            self.message_user(
                request,
                '⚠️ Only ONE course can be featured at a time. Using the first selected course.',
                level='WARNING'
            )
        
        course = queryset.first()
        if course:
            try:
                # The model's save method handles unfeaturing others
                course.badge = 'featured'
                course.badge_updated_at = timezone.now()
                course.save()
                self.message_user(
                    request,
                    f'⭐ "{course.title}" is now the Featured Course of the Month!'
                )
            except ValidationError as e:
                self.message_user(request, str(e), level='ERROR')
    
    @admin.action(description='🗑️ Remove badge from selected courses')
    def remove_badge(self, request, queryset):
        # Handle featured courses specially
        featured_courses = queryset.filter(badge='featured')
        for course in featured_courses:
            course.badge = 'none'
            course.save()
        
        # Bulk update non-featured courses
        other_courses = queryset.exclude(badge='featured')
        updated = other_courses.update(
            badge='none',
            badge_updated_at=None
        )
        
        total = featured_courses.count() + updated
        self.message_user(request, f'✅ Badge removed from {total} course(s).')
    
    actions = [
        'make_bestseller',
        'make_trending',
        'make_new',
        'make_featured',
        'remove_badge'
    ]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'is_published', 'created_at']
    list_filter = ['is_published', 'is_free_preview']
    search_fields = ['title', 'course__title']
    inlines = [LessonContentInline]


@admin.register(LessonContent)
class LessonContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'content_type', 'order', 'time_duration', 'is_preview', 'allow_download']
    list_filter = ['content_type', 'is_preview', 'is_required', 'allow_download']
    search_fields = ['title', 'lesson__title', 'lesson__course__title']

    def get_queryset(self, request):
        # Show quizzes associated with this content if any
        return super().get_queryset(request).prefetch_related('lesson__quizzes')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'progress_percentage', 'enrolled_at']
    list_filter = ['status']
    search_fields = ['student__email', 'student__first_name', 'student__last_name', 'course__title']
    date_hierarchy = 'enrolled_at'
    raw_id_fields = ['student', 'course']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'completed', 'completed_at']
    list_filter = ['completed']
    search_fields = ['student__email', 'lesson__title']
    raw_id_fields = ['student', 'lesson', 'enrollment']


from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'rating', 'title', 'is_recommended', 'created_at']
    list_filter = ['rating', 'is_recommended', 'course']
    search_fields = ['student__email', 'course__title', 'title', 'review']
    raw_id_fields = ['student', 'course']
    actions = ['update_rating', 'mark_as_recommended', 'mark_as_not_recommended']

    @admin.action(description="Update rating to selected stars")
    def update_rating(self, request: HttpRequest, queryset: QuerySet):
        # You can customize the star values here
        queryset.update(rating=5)  # Or any other value
        
    @admin.action(description="Mark selected reviews as recommended")
    def mark_as_recommended(self, request: HttpRequest, queryset: QuerySet):
        queryset.update(is_recommended=True)
        
    @admin.action(description="Mark selected reviews as not recommended")
    def mark_as_not_recommended(self, request: HttpRequest, queryset: QuerySet):
        queryset.update(is_recommended=False)




@admin.register(CourseAnnouncement)
class CourseAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'is_pinned', 'created_at']
    list_filter = ['is_pinned']
    search_fields = ['title', 'content', 'course__title']
