from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
from django.utils import timezone
import logging
import time

logger = logging.getLogger('myapp.security')

class LoginRateLimitMiddleware:
    """
    Middleware to rate limit login attempts to prevent brute force attacks.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == reverse('login') and request.method == 'POST':
            ip = self.get_client_ip(request)
            cache_key = f'login_attempts_{ip}'
            
            # Get current attempts
            attempts = cache.get(cache_key, 0)
            
            # Check if blocked
            if attempts >= 5:  # Allow 5 attempts
                logger.warning(f'Blocked login attempt from IP {ip} - too many attempts')
                return HttpResponseForbidden('Too many login attempts. Try again later.')
            
            # Increment attempts
            cache.set(cache_key, attempts + 1, 300)  # 5 minutes timeout

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SingleSessionMiddleware:
    """
    Middleware to ensure only one active session per user.
    Logs out other sessions when a user logs in.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get current session key
            current_session_key = request.session.session_key
            
            # Delete other sessions for this user
            sessions = Session.objects.filter(
                expire_date__gte=timezone.now()
            )
            
            for session in sessions:
                data = session.get_decoded()
                if data.get('_auth_user_id') == str(request.user.id):
                    if session.session_key != current_session_key:
                        logger.info(f'Logged out other session for user {request.user.username}')
                        session.delete()
        
        response = self.get_response(request)
        return response