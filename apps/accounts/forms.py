from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from .models import CustomUser, StudentProfile, InstructorProfile
import string


class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Enter your First Name',
            'id': 'id_first_name'
        })
    )
    last_name = forms.CharField(
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Enter your Last Name',
            'id': 'id_last_name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Enter your Email',
            'id': 'id_email'
        })
    )
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create password',
            'id': 'id_password1',
            'autocomplete': 'new-password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'id': 'id_password2',
            'autocomplete': 'new-password'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError('This email address is already registered.')
        return email
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            return ' '.join(word.capitalize() for word in first_name.strip().split())
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            return ' '.join(word.capitalize() for word in last_name.strip().split())
        return last_name
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = CustomUser.UserType.STUDENT
        user.email = self.cleaned_data['email'].lower()
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create student profile
            student_id = f"STU{user.date_joined.strftime('%Y%m%d')}{str(user.id)[:8].upper()}"
            StudentProfile.objects.create(user=user, student_id=student_id)
        return user


class InstructorCreationForm(forms.ModelForm):
    department = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter department',
            'id': 'id_department'
        })
    )
    expertise = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe areas of expertise and specialization',
            'id': 'id_expertise'
        }), 
        required=True
    )
    qualification = forms.CharField(
        max_length=200, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter highest qualification',
            'id': 'id_qualification'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter instructor email',
                'id': 'id_email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name',
                'id': 'id_first_name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name',
                'id': 'id_last_name'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def generate_random_password(self, length=12):
        """
        Generate a secure random password with letters, digits, and special characters.
        """
        characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|"
        return get_random_string(length, characters)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = CustomUser.UserType.INSTRUCTOR
        user.email = self.cleaned_data['email'].lower()
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        # Generate random password using the custom method
        password = self.generate_random_password()
        user.set_password(password)
        
        if commit:
            user.save()
            # Create instructor profile
            instructor_id = f"INS{user.date_joined.strftime('%Y%m%d')}{str(user.id)[:8].upper()}"
            InstructorProfile.objects.create(
                user=user,
                instructor_id=instructor_id,
                department=self.cleaned_data['department'],
                expertise=self.cleaned_data['expertise'],
                qualification=self.cleaned_data['qualification']
            )
        return user, password


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email', 
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'class': 'form-control p-3',
            'placeholder': 'example@gmail.com',
            'id': 'id_username'
        })
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control p-3',
            'placeholder': 'Enter your password',
            'id': 'id_password',
            'autocomplete': 'current-password'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            return username.lower()
        return username
    
    def confirm_login_allowed(self, user):
        """
        Check if user is allowed to login.
        Override to add custom checks.
        """
        if not user.is_active:
            raise forms.ValidationError(
                'This account is inactive.',
                code='inactive',
            )
        
        # Check if account is locked
        if hasattr(user, 'locked_until') and user.locked_until:
            from django.utils import timezone
            if user.locked_until > timezone.now():
                raise forms.ValidationError(
                    'Account is temporarily locked due to too many failed attempts. Please try again later.',
                    code='locked',
                )