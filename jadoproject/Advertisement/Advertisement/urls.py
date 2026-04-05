"""
URL configuration for Advertisement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from myapp.views import CustomLogoutView

urlpatterns = [
    # Admin logout override (redirects to landing instead of admin logout page)
    path('admin-portal-7c2e9f3a5b1d6e4f/logout/', CustomLogoutView.as_view(), name='admin-logout'),

    # Hidden admin path
    path('admin-portal-7c2e9f3a5b1d6e4f/', admin.site.urls),

    # App URLs
    path('', include('myapp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)