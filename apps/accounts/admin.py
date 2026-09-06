from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, StudentProfile, InstructorProfile, AdminProfile


# ===================== INLINES =====================

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'user'
    fields = ('student_id', 'enrollment_date', 'courses_enrolled', 'completed_courses')
    readonly_fields = ('enrollment_date',)


class InstructorProfileInline(admin.StackedInline):
    model = InstructorProfile
    can_delete = False
    verbose_name_plural = 'Instructor Profile'
    fk_name = 'user'
    fields = ('instructor_id', 'department', 'is_approved', 'signature')


class AdminProfileInline(admin.StackedInline):
    model = AdminProfile
    can_delete = False
    verbose_name_plural = 'Admin Profile'
    fk_name = 'user'
    fields = ('admin_id', 'department', 'access_level', 'signature')


# ===================== CUSTOM USER ADMIN =====================

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'email_verified', 'date_joined')
    list_filter = ('user_type', 'is_active', 'email_verified', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'bio', 'profile_picture')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'user_type', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Security'), {'fields': ('failed_login_attempts', 'locked_until', 'password_changed_at', 'email_verified')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    def get_inlines(self, request, obj=None):
        """Show profile inline based on user type"""
        if obj:
            if obj.user_type == 'STUDENT':
                return [StudentProfileInline]
            elif obj.user_type == 'INSTRUCTOR':
                return [InstructorProfileInline]
            elif obj.user_type == 'ADMIN':
                return [AdminProfileInline]
        return []
    
    actions = ['activate_users', 'deactivate_users', 'verify_emails']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) successfully activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) successfully deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    def verify_emails(self, request, queryset):
        updated = queryset.update(email_verified=True)
        self.message_user(request, f'{updated} user(s) email verified.')
    verify_emails.short_description = "Verify emails for selected users"


# ===================== STUDENT PROFILE ADMIN =====================

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'get_email', 'enrollment_date', 'courses_enrolled', 'completed_courses')
    list_filter = ('enrollment_date',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'student_id')
    ordering = ('-enrollment_date',)
    raw_id_fields = ('user',)
    autocomplete_fields = ('user',)
    
    fieldsets = (
        (_('User Information'), {
            'fields': ('user', 'student_id')
        }),
        (_('Enrollment Details'), {
            'fields': ('enrollment_date', 'courses_enrolled', 'completed_courses')
        }),
    )
    
    readonly_fields = ('enrollment_date',)
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'


# ===================== INSTRUCTOR PROFILE ADMIN =====================

@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'instructor_id', 'get_email', 'department', 'is_approved', 'get_date_joined')
    list_filter = ('is_approved', 'department')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'instructor_id', 'department')
    ordering = ('user__email',)
    raw_id_fields = ('user',)
    autocomplete_fields = ('user',)
    
    fieldsets = (
        (_('User Information'), {
            'fields': ('user', 'instructor_id')
        }),
        (_('Instructor Details'), {
            'fields': ('department', 'bio', 'is_approved')
        }),
        (_('Certificate Signature'), {
            'fields': ('signature',),
            'description': 'Upload your digital signature for course certificates. Use a transparent PNG for best results.'
        }),
    )
    
    actions = ['approve_instructors', 'unapprove_instructors']
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_date_joined(self, obj):
        return obj.user.date_joined
    get_date_joined.short_description = 'Date Joined'
    get_date_joined.admin_order_field = 'user__date_joined'
    
    def approve_instructors(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} instructor(s) approved.')
    approve_instructors.short_description = "Approve selected instructors"
    
    def unapprove_instructors(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} instructor(s) unapproved.')
    unapprove_instructors.short_description = "Unapprove selected instructors"


# ===================== ADMIN PROFILE ADMIN =====================

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'admin_id', 'get_email', 'department', 'access_level', 'get_date_joined')
    list_filter = ('access_level', 'department')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'admin_id', 'department')
    ordering = ('user__email',)
    raw_id_fields = ('user',)
    autocomplete_fields = ('user',)
    
    fieldsets = (
        (_('User Information'), {
            'fields': ('user', 'admin_id')
        }),
        (_('Admin Details'), {
            'fields': ('department', 'access_level')
        }),
        (_('Certificate Signature'), {
            'fields': ('signature',),
            'description': 'Upload the Program Director\'s digital signature for course completion certificates. Use a transparent PNG with dark ink for best results on dark certificate backgrounds.'
        }),
    )
    
    readonly_fields = ('admin_id',)
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_date_joined(self, obj):
        return obj.user.date_joined
    get_date_joined.short_description = 'Date Joined'
    get_date_joined.admin_order_field = 'user__date_joined'
    
    def save_model(self, request, obj, form, change):
        """Auto-generate admin_id if not set"""
        if not obj.admin_id:
            last_admin = AdminProfile.objects.order_by('-id').first()
            if last_admin and last_admin.admin_id and last_admin.admin_id.startswith('ADM-'):
                try:
                    last_num = int(last_admin.admin_id.split('-')[1])
                    obj.admin_id = f'ADM-{last_num + 1:04d}'
                except (ValueError, IndexError):
                    obj.admin_id = 'ADM-0001'
            else:
                obj.admin_id = 'ADM-0001'
        super().save_model(request, obj, form, change)