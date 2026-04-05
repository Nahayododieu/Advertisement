import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Advertisement.settings')
django.setup()

from django.template.loader import get_template

try:
    get_template('myapp/advertisement_detail.html')
    print('TEMPLATE_PARSE_OK')
except Exception:
    print('TEMPLATE_PARSE_ERROR')
    raise
