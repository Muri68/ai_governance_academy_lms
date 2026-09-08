from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
import re
from django.utils.text import slugify
from apps.courses.models import Course


class Category(models.Model):
    """Blog categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class (e.g., 'fa-robot')")
    color = models.CharField(max_length=20, default='#ad7a49', help_text="Category color")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})
    
    @property
    def published_post_count(self):
        return self.posts.filter(status='published').count()


class Tag(models.Model):
    """Blog tags"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('blog:tag_detail', kwargs={'slug': self.slug})
    
    @property
    def published_post_count(self):
        return self.posts.filter(status='published').count()


class Post(models.Model):
    """Blog posts"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    related_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='blog_posts')
    
    excerpt = models.TextField(max_length=500, help_text="Short summary shown in blog listing")
    content = models.TextField(help_text="Blog post content (supports HTML from TinyMCE)")
    
    featured_image = models.ImageField(upload_to='blog/images/%Y/%m/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    
    meta_title = models.CharField(max_length=200, blank=True, help_text="SEO title (optional)")
    meta_description = models.TextField(max_length=300, blank=True, help_text="SEO description (optional)")
    meta_keywords = models.CharField(max_length=200, blank=True, help_text="Comma separated keywords")
    
    views_count = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=0, help_text="Reading time in minutes")
    
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['slug']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        else:
            self.slug = slugify(self.slug)
        
        # Calculate reading time properly
        if not self.reading_time:
            # Remove HTML tags and get plain text
            plain_text = re.sub(r'<[^>]+>', ' ', self.content)
            # Remove extra whitespace
            plain_text = ' '.join(plain_text.split())
            # Count words
            word_count = len(plain_text.split())
            # Calculate reading time (200 words per minute)
            self.reading_time = max(1, round(word_count / 200))
        
        # Set published_at when publishing
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self):
        return self.status == 'published' and self.published_at and self.published_at <= timezone.now()
    
    @property
    def word_count(self):
        import re
        plain_text = re.sub(r'<[^>]+>', ' ', self.content)
        plain_text = ' '.join(plain_text.split())
        return len(plain_text.split())
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    @property
    def related_posts(self):
        """Get related posts based on tags and category"""
        if not self.tags.exists() and not self.category:
            return Post.objects.none()
        
        related = Post.objects.filter(
            status='published',
            published_at__isnull=False
        ).exclude(id=self.id)
        
        if self.category:
            related = related.filter(category=self.category)
        
        if self.tags.exists():
            related = related.filter(tags__in=self.tags.all())
        
        return related.distinct()[:3]


class Comment(models.Model):
    """Blog comments"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.email} on {self.post.title}"
    
    @property
    def is_reply(self):
        return self.parent is not None