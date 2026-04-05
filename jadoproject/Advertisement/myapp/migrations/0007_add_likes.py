"""Add likes many-to-many field to Advertisement"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_add_shares_count'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='advertisement',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_ads', to=settings.AUTH_USER_MODEL),
        ),
    ]
