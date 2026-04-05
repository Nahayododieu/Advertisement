"""Add shares_count field to Advertisement"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_add_profile_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='advertisement',
            name='shares_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
