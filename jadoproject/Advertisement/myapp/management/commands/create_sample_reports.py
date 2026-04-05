from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Advertisement, Report

class Command(BaseCommand):
    help = 'Create sample reports for testing'

    def handle(self, *args, **options):
        # Get some users and ads
        try:
            reporter = User.objects.filter(is_staff=False).first()
            admin = User.objects.filter(is_staff=True).first()
            ad = Advertisement.objects.filter(status='active').first()

            if not all([reporter, admin, ad]):
                self.stdout.write(self.style.WARNING('Not enough data to create sample reports'))
                return

            # Create sample reports
            reports_data = [
                {
                    'reporter': reporter,
                    'advertisement': ad,
                    'report_type': 'spam',
                    'description': 'This advertisement appears to be spam content.',
                    'status': 'pending'
                },
                {
                    'reporter': reporter,
                    'advertisement': ad,
                    'report_type': 'inappropriate',
                    'description': 'The content of this ad is inappropriate.',
                    'status': 'investigating'
                }
            ]

            for report_data in reports_data:
                report, created = Report.objects.get_or_create(
                    reporter=report_data['reporter'],
                    advertisement=report_data['advertisement'],
                    defaults=report_data
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created report: {report}'))
                else:
                    self.stdout.write(f'Report already exists: {report}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample reports: {e}'))