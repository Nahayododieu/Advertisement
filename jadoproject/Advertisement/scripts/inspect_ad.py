import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','Advertisement.settings')
django.setup()
from myapp.models import Advertisement
slug='0789377617'
try:
    ad=Advertisement.objects.get(slug=slug)
    print('AD ID', ad.id)
    print('IMAGE_FIELD', bool(ad.image), repr(ad.image.name))
    try:
        print('IMAGE_URL', ad.image.url)
    except Exception as e:
        print('IMAGE_URL_ERROR', e)
    try:
        print('IMAGE_PATH', ad.image.path)
        print('FILE_EXISTS', os.path.exists(ad.image.path))
    except Exception as e:
        print('IMAGE_PATH_ERROR', e)
except Advertisement.DoesNotExist:
    print('AD_NOT_FOUND')
