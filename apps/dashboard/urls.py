from django.urls import path, include
from .views import student_views, instructor_views, admin_views
from . import viewss

app_name = 'dashboard'

urlpatterns = [
    path('reviews/', admin_views.manage_reviews, name='manage_reviews'),
    
    # Student URLs
    path('student/dashboard/', student_views.student_dashboard, name='student_dashboard'),
    path('student/profile/', student_views.student_profile, name='student_profile'),
    path('student/courses/', student_views.student_courses, name='student_courses'),
    
    path('student/certificates/', student_views.student_certificates, name='student_certificates'),
    path('student/reviews/', student_views.student_reviews, name='student_reviews'),
    
    # Instructor URLs
    path('instructor/dashboard/', instructor_views.instructor_dashboard, name='instructor_dashboard'),
    path('instructor/profile/', instructor_views.instructor_profile, name='instructor_profile'),
    path('instructor/courses/', instructor_views.instructor_courses, name='instructor_courses'),
    path('instructor/courses/add/', instructor_views.instructor_add_course, name='instructor_add_course'),
    path('instructor/courses/<str:course_id>/edit/', instructor_views.instructor_edit_course, name='instructor_edit_course'),
    path('instructor/courses/<str:course_id>/students/', instructor_views.instructor_course_students, name='instructor_course_students'),
    path('instructor/course/<int:course_id>/analytics/', instructor_views.instructor_course_analytics, name='instructor_course_analytics'),
    path('instructor/change-password/', instructor_views.instructor_change_password, name='instructor_change_password'),
    
    # Instructor Dashboard URLs
    path('reviews/', instructor_views.instructor_reviews, name='instructor_reviews'),
    path('earnings/', instructor_views.instructor_earnings, name='instructor_earnings'),
    path('announcements/', instructor_views.instructor_announcements, name='instructor_announcements'),
    path('course/<int:course_id>/student/<uuid:student_id>/', instructor_views.instructor_student_detail, name='instructor_student_detail'),
    
    # Admin URLs
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/profile/', admin_views.admin_profile, name='admin_profile'),
    path('admin/change-password/', admin_views.admin_change_password, name='admin_change_password'),
    path('admin/create-instructor/', admin_views.create_instructor, name='create_instructor'),
    path('admin/create-admin/', admin_views.create_admin, name='create_admin'),
    path('admin/manage-users/', admin_views.manage_users, name='manage_users'),
    path('admin/add-user/', admin_views.add_user, name='add_user'),
    path('admin/instructors/', admin_views.manage_instructors, name='manage_instructors'),
    path('admin/toggle-user/<uuid:user_id>/', admin_views.toggle_user_status, name='toggle_user_status'),
    
    # Admin Course Management URLs
    path('admin/courses/', admin_views.manage_courses, name='manage_courses'),
    path('admin/courses/add/', admin_views.add_course, name='add_course'),
    path('admin/courses/<str:course_id>/', admin_views.admin_course_view, name='admin_course_view'),
    path('admin/courses/<str:course_id>/edit/', admin_views.edit_course, name='edit_course'),
    path('admin/courses/<str:course_id>/update-status/', admin_views.update_course_status, name='update_course_status'),
    path('admin/courses/<str:course_id>/delete/', admin_views.delete_course, name='delete_course'),
    
    path('admin/course/<str:course_id>/students/', admin_views.course_students, name='course_students'),
    path('admin/instructor/<uuid:user_id>/', admin_views.instructor_detail, name='instructor_detail'),
    path('admin/student/<uuid:user_id>/', admin_views.student_detail, name='student_detail'),
    
    path('admin/payments/', admin_views.admin_payments, name='admin_payments'),
    path('admin/enrollments/', admin_views.admin_enrollments, name='admin_enrollments'),
    path('admin/enrollment/<int:enrollment_id>/update-status/', admin_views.update_enrollment_status, name='update_enrollment_status'),
    
    path('settings/', admin_views.site_settings, name='site_settings'),
    path('settings/<str:setting_type>/', admin_views.site_settings, name='site_settings_type'),
    
    
    
    # Contact Messages
    path('messages/', admin_views.contact_messages, name='contact_messages'),
    path('messages/<int:message_id>/', admin_views.contact_message_detail, name='contact_message_detail'),
    path('messages/<int:message_id>/<str:action>/', admin_views.contact_message_action, name='contact_message_action'),
    
    # Newsletter
    path('newsletter/', admin_views.newsletter_dashboard, name='newsletter_dashboard'),
    path('newsletter/compose/', admin_views.newsletter_compose, name='newsletter_compose'),
    path('newsletter/campaign/<int:campaign_id>/', admin_views.newsletter_campaign_detail, name='newsletter_campaign_detail'),
    path('newsletter/subscriber/<int:subscriber_id>/delete/', admin_views.delete_subscriber, name='delete_subscriber'),
    
    path('test-email/', viewss.test_email, name='test_email'),
        
]