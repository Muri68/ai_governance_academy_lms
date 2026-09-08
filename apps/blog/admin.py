from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import Post, Category, Tag, Comment


class PostAdminForm(forms.ModelForm):
    """Form with TinyMCE widget for content"""
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'tinymce-editor',
                'data-tinymce': 'true',
                'rows': 20,
            }),
            'excerpt': forms.Textarea(attrs={'rows': 3}),
        }
    
    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/tinymce@6.8.3/skins/ui/oxide/skin.min.css',)
        }
        js = (
            'https://cdn.jsdelivr.net/npm/tinymce@6.8.3/tinymce.min.js',
            'js/tinymce_config.js',
        )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'published_post_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    
    def published_post_count(self, obj):
        return obj.published_post_count
    published_post_count.short_description = 'Posts'
    published_post_count.admin_order_field = 'posts'  # Allow sorting


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'published_post_count']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    
    def published_post_count(self, obj):
        return obj.published_post_count
    published_post_count.short_description = 'Posts'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ['title', 'author', 'category', 'status', 'is_featured', 'published_at', 'views_count', 'thumbnail_preview']
    list_filter = ['status', 'is_featured', 'category', 'created_at']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    readonly_fields = ['views_count', 'reading_time', 'created_at', 'updated_at']
    date_hierarchy = 'published_at'
    list_editable = ['is_featured', 'status']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'author', 'excerpt', 'content', 'featured_image')
        }),
        ('Organization', {
            'fields': ('category', 'tags', 'related_course', 'is_featured')
        }),
        ('Publishing', {
            'fields': ('status', 'published_at')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('views_count', 'reading_time'),
            'classes': ('collapse',)
        }),
    )
    
    def thumbnail_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" width="60" height="40" style="object-fit: cover;" />', obj.featured_image.url)
        return "No image"
    thumbnail_preview.short_description = 'Featured Image'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'category')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'content_preview', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['content', 'author__email', 'post__title']
    list_editable = ['is_approved']
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Comment'