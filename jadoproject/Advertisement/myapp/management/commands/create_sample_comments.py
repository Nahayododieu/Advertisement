from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Advertisement, Comment

class Command(BaseCommand):
    help = 'Create sample comments and replies for testing'

    def handle(self, *args, **options):
        # Get some users and ads
        try:
            users = User.objects.filter(is_staff=False)[:3]
            ads = Advertisement.objects.filter(status='active')[:2]

            if not users or not ads:
                self.stdout.write(self.style.WARNING('Not enough data to create sample comments'))
                return

            comments_created = 0

            for ad in ads:
                # Create main comments
                for i, user in enumerate(users):
                    comment = Comment.objects.create(
                        ad=ad,
                        user=user,
                        text=f"This is a sample comment #{i+1} on {ad.title}. What do you think about this advertisement?"
                    )
                    comments_created += 1
                    self.stdout.write(f'Created comment: {comment}')

                    # Create replies to some comments
                    if i < 2:  # Create replies for first 2 comments
                        for j, reply_user in enumerate(users):
                            if reply_user != user:  # Don't reply to self
                                reply = Comment.objects.create(
                                    ad=ad,
                                    user=reply_user,
                                    parent=comment,
                                    text=f"Thanks for the comment! I agree with you about {ad.title}. Here are my thoughts..."
                                )
                                comments_created += 1
                                self.stdout.write(f'Created reply: {reply}')

                                # Create nested replies (replies to replies)
                                if j == 0:  # Create one nested reply
                                    nested_reply = Comment.objects.create(
                                        ad=ad,
                                        user=user,
                                        parent=reply,
                                        text=f"You're welcome! Glad you found it helpful. The {ad.title} looks really promising."
                                    )
                                    comments_created += 1
                                    self.stdout.write(f'Created nested reply: {nested_reply}')

            self.stdout.write(self.style.SUCCESS(f'Successfully created {comments_created} sample comments and replies'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample comments: {e}'))