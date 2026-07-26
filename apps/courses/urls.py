from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course Learning
    path('learn/<slug:course_slug>/', views.course_learning, name='course_learning'),
    
    # AJAX Content Loading
    path('learn/<slug:course_slug>/lesson/<int:lesson_id>/content/<int:content_id>/', 
         views.load_lesson_content, name='load_lesson_content'),
    
    # AJAX Actions
    path('learn/<slug:course_slug>/lesson/<int:lesson_id>/complete/', 
         views.mark_lesson_complete, name='mark_complete'),
    path('learn/<slug:course_slug>/lesson/<int:lesson_id>/save-notes/', 
         views.save_lesson_notes, name='save_notes'),
    
    # File Serving
    path('learn/<slug:course_slug>/file/<int:content_id>/', 
         views.serve_protected_file, name='serve_file'),
    
    # Reviews
    path('learn/<slug:course_slug>/review/', 
         views.submit_review, name='submit_review'),
    
    # Certificates
    path('certificate/<int:enrollment_id>/download/', 
         views.view_certificate, name='view_certificate'),
    path('verify/<str:cert_id>/', 
         views.verify_certificate, name='verify_certificate'),
]