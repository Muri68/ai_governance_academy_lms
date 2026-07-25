from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('courses/', views.CoursesView.as_view(), name='courses'),
    path('course/<slug:slug>/', views.course_learning, name='course_learning'),
    path('course/<slug:slug>/detail/', views.CourseDetailView.as_view(), name='course_detail'),
    path('course/<slug:slug>/content/<int:content_id>/', views.course_content_detail, name='course_content_detail'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy'),
    path('terms/', views.TermsConditionsView.as_view(), name='terms'),
    path('faq/', views.FAQView.as_view(), name='faq'),
    
    path('submit-site-review/', views.submit_site_review, name='submit_site_review'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('unsubscribe/', views.unsubscribe_newsletter, name='unsubscribe_newsletter'),
]