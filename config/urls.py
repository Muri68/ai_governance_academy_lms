"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('accounts/', include('allauth.urls')),    
    path('tinymce/', include('tinymce.urls')),
    
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('courses/', include('apps.courses.urls', namespace='courses')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
    path('', include('apps.frontend.urls', namespace='frontend')),
]

# Custom error handlers
handler404 = 'apps.frontend.views.error_404'
handler500 = 'apps.frontend.views.error_500'
handler503 = 'apps.frontend.views.error_503'
handler401 = 'apps.frontend.views.error_401'
handler403 = 'apps.frontend.views.error_403'

# Only use static() helper in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # In production, serve media files through Django (not ideal but works)
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
    
    

# Add this at the END of your urlpatterns, before any catch-all
from django.conf import settings

if settings.DEBUG:
    from django.urls import path
    from apps.frontend.views import error_404, error_500, error_503, error_401, error_403
    
    # Error page testing URLs
    urlpatterns += [
        # Direct error page views
        path('test-404/', error_404, {'exception': None}, name='test_404'),
        path('test-500/', error_500, name='test_500'),
        path('test-503/', error_503, name='test_503'),
        path('test-401/', error_401, name='test_401'),
        path('test-403/', error_403, {'exception': None}, name='test_403'),
    ]
    
    # Trigger real errors
    def trigger_500_error(request):
        raise Exception("Test 500 error!")
    
    def trigger_403_error(request):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Test 403 error!")
    
    def trigger_404_error(request):
        from django.http import Http404
        raise Http404("Test 404 error!")
    
    urlpatterns += [
        path('trigger-500/', trigger_500_error, name='trigger_500'),
        path('trigger-403/', trigger_403_error, name='trigger_403'),
        path('trigger-404/', trigger_404_error, name='trigger_404'),
    ]