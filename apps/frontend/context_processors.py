from apps.dashboard.models import SiteSetting, SiteFileSetting
from apps.frontend.models import ContactMessage,SiteReview, NewsletterSubscriber
from apps.courses.models import Course  # Adjust import based on your app structure
from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()


def site_settings(request):
    """Make site settings available in all templates"""
    settings = {}
    for s in SiteSetting.objects.all():
        settings[s.key] = s.value
    
    # Site name splitting
    site_name = settings.get('site_name', 'AI GOVERNANCE ACADEMY')
    words = site_name.strip().split()
    if len(words) <= 2:
        name_line1 = ' '.join(words[:len(words)//2]) if len(words) > 1 else words[0]
        name_line2 = ' '.join(words[len(words)//2:]) if len(words) > 1 else ''
    elif len(words) == 3:
        name_line1 = ' '.join(words[:2])
        name_line2 = words[2]
    else:
        mid = len(words) // 2
        name_line1 = ' '.join(words[:mid])
        name_line2 = ' '.join(words[mid:])
    if 'ACADEMY' in name_line1.upper() and 'ACADEMY' in name_line2.upper():
        name_line1 = name_line1.replace('Academy', '').replace('ACADEMY', '').strip()
    
    # Get file URLs from SiteFileSetting model
    def get_file_url(key):
        """Helper function to get file URL from SiteFileSetting"""
        try:
            file_setting = SiteFileSetting.objects.get(key=key)
            if file_setting.file:
                return file_setting.file.url
        except SiteFileSetting.DoesNotExist:
            pass
        return None
    
    favicon_url = get_file_url('favicon')
    site_logo_url = get_file_url('site_logo')
    dashboard_logo_url = get_file_url('dashboard_logo')
    
    # Get admin sidebar counts
    admin_counts = {}
    if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
        try:
            admin_counts['total_courses'] = Course.objects.count()
        except:
            admin_counts['total_courses'] = 0
        
        try:
            # Count instructors (users with instructor role/profile)
            from apps.accounts.models import InstructorProfile  # Adjust import
            admin_counts['total_instructors'] = InstructorProfile.objects.count()
        except:
            try:
                admin_counts['total_instructors'] = User.objects.filter(role='instructor').count()
            except:
                admin_counts['total_instructors'] = 0
        
        try:
            admin_counts['total_users'] = User.objects.count()
        except:
            admin_counts['total_users'] = 0
        
        try:
            admin_counts['unread_messages'] = ContactMessage.objects.filter(is_read=False).count()
        except:
            admin_counts['unread_messages'] = 0
        
        try:
            admin_counts['pending_reviews_count'] = SiteReview.objects.filter(is_approved=False).count()
        except:
            admin_counts['pending_reviews_count'] = 0
    
    return {
        'site_settings': settings,
        'site_name': site_name,
        'site_name_line1': name_line1,
        'site_name_line2': name_line2,
        'site_tagline': settings.get('site_tagline', 'AI Ethics & Compliance Platform'),
        'contact_email': settings.get('contact_email', 'info@aiga.com'),
        'contact_phone': settings.get('contact_phone', '+1 (223) 456-6000'),
        'office_address': settings.get('office_address', ''),
        'facebook_url': settings.get('facebook_url', '#'),
        'twitter_url': settings.get('twitter_url', '#'),
        'linkedin_url': settings.get('linkedin_url', '#'),
        'instagram_url': settings.get('instagram_url', '#'),
        'youtube_url': settings.get('youtube_url', '#'),
        'map_embed_url': settings.get('map_embed_url', ''),
        'footer_text': settings.get('footer_text', ''),
        'meta_title': settings.get('meta_title', ''),
        'meta_description': settings.get('meta_description', ''),
        'meta_keywords': settings.get('meta_keywords', ''),
        'google_analytics': settings.get('google_analytics', ''),
        'site_logo_url': site_logo_url,
        'dashboard_logo_url': dashboard_logo_url,
        'favicon_url': favicon_url,
        'primary_color': settings.get('primary_color', '#ad7a49'),
        'about_us': settings.get('about_us', ''),
        'privacy_policy': settings.get('privacy_policy', ''),
        'terms_conditions': settings.get('terms_conditions', ''),
        # Admin sidebar counts
        'total_courses': admin_counts.get('total_courses', 0),
        'total_instructors': admin_counts.get('total_instructors', 0),
        'total_users': admin_counts.get('total_users', 0),
        'unread_messages_count': admin_counts.get('unread_messages', 0),
        'pending_reviews_count': admin_counts.get('pending_reviews_count', 0),
    }