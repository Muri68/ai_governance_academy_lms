from django.db import models
from django.utils import timezone
from django.conf import settings

class ContactMessage(models.Model):
    """Contact form submissions"""
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=300, blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    is_read = models.BooleanField(default=False)
    replied_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.email} - {self.created_at.strftime('%b %d, %Y')}"
    
    def mark_as_read(self):
        self.is_read = True
        self.status = 'read'
        self.save()
    
    def mark_as_replied(self):
        self.status = 'replied'
        self.replied_at = timezone.now()
        self.save()


# models.py - Update ContactReply
class ContactReply(models.Model):
    """Replies to contact messages"""
    contact_message = models.ForeignKey(ContactMessage, on_delete=models.CASCADE, related_name='replies')
    subject = models.CharField(max_length=300)
    message = models.TextField()
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Contact Reply'
        verbose_name_plural = 'Contact Replies'
        ordering = ['-sent_at']
    
    def __str__(self):
        sent_by_name = self.sent_by.get_full_name() if self.sent_by else 'System'
        return f"Reply to {self.contact_message.name} by {sent_by_name} - {self.sent_at.strftime('%b %d, %Y')}"
    
    def get_sender_name(self):
        """Get sender name safely"""
        if self.sent_by:
            return self.sent_by.get_full_name() or self.sent_by.email
        return 'System'


class NewsletterSubscriber(models.Model):
    """Newsletter subscribers"""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email
    
    def unsubscribe(self):
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()


class NewsletterCampaign(models.Model):
    """Newsletter campaigns sent to subscribers"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    subject = models.CharField(max_length=300)
    content = models.TextField()
    recipients_count = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Newsletter Campaign'
        verbose_name_plural = 'Newsletter Campaigns'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.created_at.strftime('%b %d, %Y')}"
  
    
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class SiteReview(models.Model):
    """Site reviews - can be created by admin or by logged-in users"""
    
    # Make user optional for admin-created reviews
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        related_name='site_reviews',
        null=True,
        blank=True,
        help_text="Leave empty if creating a review on behalf of someone (admin only)"
    )
    
    # For admin-created reviews without a user account
    reviewer_name = models.CharField(
        max_length=150, 
        blank=True, 
        null=True,
        help_text="Required if no user is selected (for non-registered reviewers)"
    )
    reviewer_email = models.EmailField(
        blank=True, 
        null=True,
        help_text="Optional email for non-registered reviewers"
    )
    
    # Reviewer details
    designation = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        help_text="e.g., Product Designer, USA"
    )
    company = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Company or organization name"
    )
    
    # Avatar for non-registered users
    avatar = models.ImageField(
        upload_to='site_reviews/avatars/', 
        blank=True, 
        null=True,
        help_text="Upload avatar for non-registered reviewers"
    )
    
    # Rating
    rating = models.PositiveIntegerField(
        default=5, 
        choices=[(i, i) for i in range(1, 6)]
    )
    
    # Review content
    review_text = models.TextField()
    review_title = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Optional title for the review"
    )
    
    # Approval status
    is_approved = models.BooleanField(
        default=False, 
        help_text="Admin must approve before displaying"
    )
    
    # Featured review
    is_featured = models.BooleanField(
        default=False,
        help_text="Show this review prominently"
    )
    
    # Source tracking
    SOURCE_CHOICES = [
        ('user', 'Submitted by User'),
        ('admin', 'Created by Admin'),
        ('imported', 'Imported'),
    ]
    source = models.CharField(
        max_length=20, 
        choices=SOURCE_CHOICES, 
        default='user',
        help_text="How this review was created"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Review'
        verbose_name_plural = 'Site Reviews'
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['is_approved']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['source']),
        ]
    
    def __str__(self):
        name = self.get_reviewer_name()
        return f"{name} - {self.rating}★"
    
    def clean(self):
        """Validate that either user or reviewer_name is provided"""
        super().clean()
        if not self.user and not self.reviewer_name:
            raise ValidationError({
                'reviewer_name': 'Either select a user or provide a reviewer name.',
                'user': 'Either select a user or provide a reviewer name.'
            })
        
        # Ensure user-created reviews are unique per user
        if self.user and self.source == 'user':
            existing = SiteReview.objects.filter(
                user=self.user,
                source='user'
            ).exclude(pk=self.pk).first()
            if existing:
                raise ValidationError({
                    'user': f'This user has already submitted a review. One review per user is allowed.'
                })
    
    def save(self, *args, **kwargs):
        # Auto-set source based on user
        if self.user and not self.source:
            self.source = 'user'
        elif not self.user:
            self.source = 'admin'
        
        # Auto-approve admin-created reviews
        if self.source == 'admin' and not self.is_approved:
            self.is_approved = True
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_reviewer_name(self):
        """Returns the best available name for the reviewer"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.reviewer_name or "Anonymous"
    
    def get_reviewer_email(self):
        """Returns the best available email for the reviewer"""
        if self.user:
            return self.user.email
        return self.reviewer_email or ""
    
    def get_avatar_url(self):
        """Returns the avatar URL if available"""
        if self.user and hasattr(self.user, 'profile_picture') and self.user.profile_picture:
            return self.user.profile_picture.url
        if self.avatar:
            return self.avatar.url
        return None
    
    def get_initials(self):
        """Returns initials for avatar placeholder"""
        name = self.get_reviewer_name()
        if name and name != "Anonymous":
            parts = name.split()
            if len(parts) >= 2:
                return f"{parts[0][0]}{parts[1][0]}".upper()
            return parts[0][0].upper()
        return "?"
    
    @property
    def rating_stars(self):
        """Returns filled and empty stars for display"""
        return list(range(self.rating)), list(range(5 - self.rating))
    
    @classmethod
    def get_approved_reviews(cls):
        """Get all approved reviews for display"""
        return cls.objects.filter(is_approved=True).select_related('user')
    
    @classmethod
    def get_featured_reviews(cls):
        """Get featured reviews for homepage"""
        return cls.objects.filter(
            is_approved=True, 
            is_featured=True
        ).select_related('user')[:3]