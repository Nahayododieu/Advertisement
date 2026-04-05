from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Advertisement, Share

class Command(BaseCommand):
    help = 'Create sample shares for testing'

    def handle(self, *args, **options):
        # Get some users and ads
        try:
            users = User.objects.filter(is_staff=False)[:3]
            ads = Advertisement.objects.filter(status='active')[:2]

            if not users or not ads:
                self.stdout.write(self.style.WARNING('Not enough data to create sample shares'))
                return

            share_methods = ['facebook', 'twitter', 'whatsapp', 'link']
            shares_created = 0

            for user in users:
                for ad in ads:
                    for method in share_methods[:2]:  # Create 2 shares per user per ad
                        share, created = Share.objects.get_or_create(
                            user=user,
                            advertisement=ad,
                            share_method=method,
                            defaults={
                                'ip_address': '127.0.0.1',
                                'user_agent': 'Sample User Agent'
                            }
                        )
                        if created:
                            shares_created += 1
                            self.stdout.write(f'Created share: {share}')

            self.stdout.write(self.style.SUCCESS(f'Successfully created {shares_created} sample shares'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample shares: {e}'))