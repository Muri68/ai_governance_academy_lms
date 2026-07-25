from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Create superadmin with all required fields'

    def handle(self, *args, **kwargs):
        email = 'admin@aiga.com'
        password = 'Admin@123456'
        
        if CustomUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'Superadmin {email} already exists'))
            # Update existing superadmin
            user = CustomUser.objects.get(email=email)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.is_verified = True
            user.email_verified = True
            user.user_type = 'ADMIN'
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated superadmin: {email}'))
        else:
            CustomUser.objects.create_superuser(
                email=email,
                password=password,
                first_name='Admin',
                last_name='User',
                user_type='ADMIN',
                is_active=True,
                is_verified=True,
                email_verified=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created superadmin: {email}'))
        
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Password: {password}')