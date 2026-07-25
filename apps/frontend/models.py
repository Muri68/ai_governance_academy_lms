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
  
    
class SiteReview(models.Model):
    """Site reviews from users who have used the platform"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='site_reviews')
    rating = models.PositiveIntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    review_text = models.TextField()
    designation = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Product Designer, USA")
    is_approved = models.BooleanField(default=False, help_text="Admin must approve before displaying")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Review'
        verbose_name_plural = 'Site Reviews'
        ordering = ['-created_at']
        unique_together = ['user']  # One review per user
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.rating}★"