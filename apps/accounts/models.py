from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
import uuid


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class UserType(models.TextChoices):
        STUDENT = 'STUDENT', _('Student')
        INSTRUCTOR = 'INSTRUCTOR', _('Instructor')
        ADMIN = 'ADMIN', _('Admin')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.STUDENT,
    )
    
    # Profile fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # Account status
    is_active = models.BooleanField(default=False)  # Changed to False - requires email verification
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    
    # Email verification
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_token_created = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Security fields
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return self.first_name
    
    @property
    def is_student(self):
        return self.user_type == self.UserType.STUDENT
    
    @property
    def is_instructor(self):
        return self.user_type == self.UserType.INSTRUCTOR
    
    @property
    def is_admin_user(self):
        return self.user_type == self.UserType.ADMIN
    
    def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save()
    
    def generate_verification_token(self):
        """Generate a unique verification token"""
        from django.utils.crypto import get_random_string
        self.verification_token = get_random_string(64)
        self.verification_token_created = timezone.now()
        self.save()
        return self.verification_token
    
    def verify_email(self, token):
        """Verify email with token"""
        if self.verification_token == token:
            # Check if token is not expired (48 hours)
            if self.verification_token_created:
                expiry_time = self.verification_token_created + timezone.timedelta(hours=48)
                if timezone.now() <= expiry_time:
                    self.email_verified = True
                    self.is_verified = True
                    self.is_active = True
                    self.verification_token = None
                    self.verification_token_created = None
                    self.save()
                    return True
        return False


# Rest of your models remain the same...
class StudentProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    student_id = models.CharField(max_length=20, unique=True)
    enrollment_date = models.DateField(null=True, blank=True)
    courses_enrolled = models.IntegerField(default=0)
    completed_courses = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = _('student profile')
        verbose_name_plural = _('student profiles')
    
    def __str__(self):
        return f"Student: {self.user.email}"


class InstructorProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='instructor_profile'
    )
    instructor_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)
    expertise = models.TextField(blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    years_of_experience = models.IntegerField(default=0)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True, help_text="Instructor's digital signature for certificates")
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('instructor profile')
        verbose_name_plural = _('instructor profiles')
    
    def __str__(self):
        return f"Instructor: {self.user.email}"


class AdminProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='admin_profile'
    )
    admin_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)
    access_level = models.IntegerField(default=1)
    
    class Meta:
        verbose_name = _('admin profile')
        verbose_name_plural = _('admin profiles')
    
    def __str__(self):
        return f"Admin: {self.user.email}"