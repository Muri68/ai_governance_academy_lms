from django.contrib import admin
from .models import SiteReview

from django.contrib import admin
from django.utils.html import format_html
from .models import SiteReview


@admin.register(SiteReview)
class SiteReviewAdmin(admin.ModelAdmin):
    list_display = [
        'get_reviewer_display', 'rating_display', 'designation', 
        'source', 'is_approved', 'is_featured', 'created_at'
    ]
    list_filter = ['is_approved', 'is_featured', 'source', 'rating']
    search_fields = [
        'reviewer_name', 'reviewer_email', 'review_text',
        'user__email', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'source']
    
    fieldsets = (
        ('Reviewer Information', {
            'fields': ('user', 'reviewer_name', 'reviewer_email', 'designation', 'company', 'avatar'),
            'description': 'For admin-created reviews: leave "user" empty and fill in "reviewer_name".<br>'
                           'For user-submitted reviews: select the user (reviewer_name is optional).'
        }),
        ('Review Content', {
            'fields': ('review_title', 'review_text', 'rating')
        }),
        ('Status', {
            'fields': ('is_approved', 'is_featured', 'source')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_reviewer_display(self, obj):
        """Display reviewer with avatar"""
        avatar_url = obj.get_avatar_url()
        name = obj.get_reviewer_name()
        
        if avatar_url:
            return format_html(
                '<img src="{}" style="width:30px;height:30px;border-radius:50%;margin-right:8px;vertical-align:middle;">{}',
                avatar_url, name
            )
        return name
    get_reviewer_display.short_description = 'Reviewer'
    get_reviewer_display.admin_order_field = 'user__first_name'
    
    def rating_display(self, obj):
        """Display rating as stars"""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color:#f59e0b;">{}</span>', stars)
    rating_display.short_description = 'Rating'
    
    def save_model(self, request, obj, form, change):
        """Auto-set source on save"""
        if not obj.pk:  # New review
            if obj.user:
                obj.source = 'user'
            else:
                obj.source = 'admin'
        super().save_model(request, obj, form, change)
    
    actions = ['approve_reviews', 'feature_reviews', 'unfeature_reviews']
    
    @admin.action(description='✅ Approve selected reviews')
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} review(s) approved.')
    
    @admin.action(description='⭐ Feature selected reviews')
    def feature_reviews(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} review(s) featured.')
    
    @admin.action(description='Remove feature from selected reviews')
    def unfeature_reviews(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} review(s) unfeatured.')
    

from django.contrib import admin
from .models import NewsletterSubscriber

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'subscribed_at', 'unsubscribed_at')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)
    actions = ['activate_subscribers', 'deactivate_subscribers']
    
    def activate_subscribers(self, request, queryset):
        queryset.update(is_active=True, unsubscribed_at=None)
    activate_subscribers.short_description = "Activate selected subscribers"
    
    def deactivate_subscribers(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_active=False, unsubscribed_at=timezone.now())
    deactivate_subscribers.short_description = "Deactivate selected subscribers"