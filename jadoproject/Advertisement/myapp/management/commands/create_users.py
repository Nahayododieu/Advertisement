from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create an admin (superuser) and a regular customer user with default credentials.'

    def add_arguments(self, parser):
        parser.add_argument('--admin-username', default='siteadmin', help='Admin username')
        parser.add_argument('--admin-email', default='admin@example.com', help='Admin email')
        parser.add_argument('--admin-password', default='Admin@12345', help='Admin password')
        parser.add_argument('--user-username', default='customer', help='Customer username')
        parser.add_argument('--user-email', default='customer@example.com', help='Customer email')
        parser.add_argument('--user-password', default='Customer@123', help='Customer password')

    def handle(self, *args, **options):
        User = get_user_model()

        admin_username = options['admin_username']
        admin_email = options['admin_email']
        admin_password = options['admin_password']

        user_username = options['user_username']
        user_email = options['user_email']
        user_password = options['user_password']

        # Create admin/superuser
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(username=admin_username, email=admin_email, password=admin_password)
            self.stdout.write(self.style.SUCCESS(f'Created superuser: {admin_username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser "{admin_username}" already exists'))

        # Create regular user
        if not User.objects.filter(username=user_username).exists():
            user = User.objects.create_user(username=user_username, email=user_email, password=user_password)
            # Ensure regular user is not staff/superuser
            user.is_staff = False
            user.is_superuser = False
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created regular user: {user_username}'))
        else:
            self.stdout.write(self.style.WARNING(f'User "{user_username}" already exists'))

        self.stdout.write('Default credentials:')
        self.stdout.write(f'  Admin -> username: {admin_username}  password: {admin_password}')
        self.stdout.write(f'  User  -> username: {user_username}  password: {user_password}')
        self.stdout.write(self.style.NOTICE('Run this command with custom flags to change credentials if needed.'))
