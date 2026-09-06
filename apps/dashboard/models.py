from django.db import models


class SiteSetting(models.Model):
    """Site-wide settings managed by super admin (text-based settings)"""
    SETTING_TYPES = [
        ('general', 'General'),
        ('branding', 'Branding'),
        ('content', 'Content Pages'),
        ('about', 'About Us Content'),
        ('contact', 'Contact Info'),
        ('social', 'Social Media'),
        ('seo', 'SEO'),
        ('faq', 'FAQ Management'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True, null=True)
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='general')
    description = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'
        ordering = ['setting_type', 'key']
    
    def __str__(self):
        return f"{self.get_setting_type_display()} - {self.key}"
    
    @classmethod
    def get_setting(cls, key, default=''):
        """Get a setting value by key"""
        # Check file settings first
        try:
            from apps.dashboard.models import SiteFileSetting
            file_setting = SiteFileSetting.objects.get(key=key)
            if file_setting.file:
                return file_setting.file.url
        except (SiteFileSetting.DoesNotExist, ImportError):
            pass
        
        # Fall back to text settings
        setting = cls.objects.filter(key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set_setting(cls, key, value, setting_type='general', description=''):
        """Set a setting value"""
        setting, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'setting_type': setting_type,
                'description': description
            }
        )
        return setting


class SiteFileSetting(models.Model):
    """Site-wide file settings like logos, favicon, etc."""
    key = models.CharField(max_length=100, unique=True)
    file = models.FileField(upload_to='site_settings/', blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site File Setting'
        verbose_name_plural = 'Site File Settings'
        ordering = ['key']
    
    def __str__(self):
        return f"File Setting: {self.key}"
    
    def file_url(self):
        """Returns the file URL if file exists"""
        if self.file:
            return self.file.url
        return None
    
    def file_name(self):
        """Returns just the file name"""
        if self.file:
            return self.file.name.split('/')[-1]
        return None
    
    
class FAQ(models.Model):
    """Frequently Asked Questions"""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('courses', 'Courses'),
        ('payment', 'Payment'),
        ('technical', 'Technical'),
        ('certificates', 'Certificates'),
    ]
    
    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['category', 'order']
    
    def __str__(self):
        return self.question[:80]