# apps/dashboard/forms.py

from django import forms
from django.contrib.auth import get_user_model

from apps.accounts.models import InstructorProfile, AdminProfile

User = get_user_model()


class InstructorEditForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        max_length=500,
    )
    profile_picture = forms.ImageField(required=False)
    is_active = forms.BooleanField(required=False)

    # Profile fields
    department = forms.CharField(max_length=100, required=False)
    expertise = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
    )
    qualification = forms.CharField(max_length=200, required=False)
    years_of_experience = forms.IntegerField(min_value=0, required=False, initial=0)
    is_approved = forms.BooleanField(required=False)
    signature = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = []  # We handle fields manually

    def __init__(self, *args, **kwargs):
        self.instructor_profile = kwargs.pop('instructor_profile', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            self.fields['email'].initial = self.instance.email
            self.fields['phone'].initial = self.instance.phone
            self.fields['bio'].initial = self.instance.bio
            self.fields['is_active'].initial = self.instance.is_active

            if self.instructor_profile:
                self.fields['department'].initial = self.instructor_profile.department
                self.fields['expertise'].initial = self.instructor_profile.expertise
                self.fields['qualification'].initial = self.instructor_profile.qualification
                self.fields['years_of_experience'].initial = self.instructor_profile.years_of_experience
                self.fields['is_approved'].initial = self.instructor_profile.is_approved

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone') or None
        if phone:
            qs = User.objects.filter(phone=phone)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('A user with this phone already exists.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone') or None
        user.bio = self.cleaned_data.get('bio', '')
        user.is_active = self.cleaned_data.get('is_active', False)
        if self.cleaned_data.get('profile_picture'):
            user.profile_picture = self.cleaned_data['profile_picture']

        if commit:
            user.save()

            profile = self.instructor_profile
            if profile:
                profile.department = self.cleaned_data.get('department', '')
                profile.expertise = self.cleaned_data.get('expertise', '')
                profile.qualification = self.cleaned_data.get('qualification', '')
                profile.years_of_experience = self.cleaned_data.get('years_of_experience') or 0
                profile.is_approved = self.cleaned_data.get('is_approved', False)
                if self.cleaned_data.get('signature'):
                    profile.signature = self.cleaned_data['signature']
                profile.save()
        return user


class AdminEditForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        max_length=500,
    )
    profile_picture = forms.ImageField(required=False)
    is_active = forms.BooleanField(required=False)
    is_staff = forms.BooleanField(required=False)

    # Profile fields
    department = forms.CharField(max_length=100, required=False)
    access_level = forms.IntegerField(
        min_value=1, max_value=3, required=False, initial=1,
        help_text="1=Basic, 2=Manager, 3=Super Admin",
    )
    signature = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = []

    def __init__(self, *args, **kwargs):
        self.admin_profile = kwargs.pop('admin_profile', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            self.fields['email'].initial = self.instance.email
            self.fields['phone'].initial = self.instance.phone
            self.fields['bio'].initial = self.instance.bio
            self.fields['is_active'].initial = self.instance.is_active
            self.fields['is_staff'].initial = self.instance.is_staff

            if self.admin_profile:
                self.fields['department'].initial = self.admin_profile.department
                self.fields['access_level'].initial = self.admin_profile.access_level

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone') or None
        if phone:
            qs = User.objects.filter(phone=phone)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('A user with this phone already exists.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone') or None
        user.bio = self.cleaned_data.get('bio', '')
        user.is_active = self.cleaned_data.get('is_active', False)
        user.is_staff = self.cleaned_data.get('is_staff', False)
        if self.cleaned_data.get('profile_picture'):
            user.profile_picture = self.cleaned_data['profile_picture']

        if commit:
            user.save()

            profile = self.admin_profile
            if profile:
                profile.department = self.cleaned_data.get('department', '')
                profile.access_level = self.cleaned_data.get('access_level') or 1
                if self.cleaned_data.get('signature'):
                    profile.signature = self.cleaned_data['signature']
                profile.save()
        return user