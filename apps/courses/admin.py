from django.contrib import admin
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
        return obj.course_count
    course_count.short_description = 'Courses'
    course_count.admin_order_field = 'courses__count'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'category', 'status', 'price', 'get_students', 'get_rating', 'created_at']
    list_filter = ['status', 'level', 'category', 'is_featured', 'is_free', 'has_certificate']
    search_fields = ['title', 'description', 'instructor__email', 'instructor__first_name', 'instructor__last_name']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'published_at']
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
        ('Status & Visibility', {
            'fields': ('status', 'is_featured', 'has_certificate', 'certificate_template')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_students(self, obj):
        return obj.total_students
    get_students.short_description = 'Students'
    get_students.admin_order_field = 'enrollments__count'
    
    def get_rating(self, obj):
        avg = obj.average_rating
        return f"{avg}★" if avg else "—"
    get_rating.short_description = 'Rating'


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