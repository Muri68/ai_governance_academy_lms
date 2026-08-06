from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    CourseCategory, Course, Lesson, LessonContent, 
    Enrollment, LessonProgress, CourseReview, CourseAnnouncement
)

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
            'fields': ('level', 'duration', 'language', 'requirements', 'what_you_learn')
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


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'rating', 'title', 'is_recommended', 'created_at']
    list_filter = ['rating', 'is_recommended']
    search_fields = ['student__email', 'course__title', 'title', 'review']
    raw_id_fields = ['student', 'course']


@admin.register(CourseAnnouncement)
class CourseAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'is_pinned', 'created_at']
    list_filter = ['is_pinned']
    search_fields = ['title', 'content', 'course__title']