# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.courses.models import Course


class CourseSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = "https"
    
    def items(self):
        return Course.objects.filter(status='published')
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        try:
            return reverse('frontend:course_detail', args=[obj.slug])
        except:
            return reverse('courses:course_detail', args=[obj.slug])


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "weekly"
    protocol = "https"
    
    def items(self):
        return [
            'frontend:index',
            'frontend:about',
            'frontend:contact',
            'frontend:courses',
            'frontend:privacy',
            'frontend:terms',
            'frontend:faq',
        ]
    
    def location(self, item):
        return reverse(item)