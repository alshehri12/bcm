"""
Language Selection Middleware for BCM Risk Management System

This middleware automatically activates the appropriate language for each request
based on user preferences. It supports bilingual operation (English and Arabic)
with proper RTL layout for Arabic.

The middleware checks language preferences in order of priority:
1. Authenticated user's saved language preference (from User model)
2. Session language (for unauthenticated users on login page)
3. Cookie language (fallback for persistence across sessions)

This ensures that:
- Logged-in users always see their preferred language
- Login page respects language selection before authentication
- Language preference persists across browser sessions via cookies
"""

from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

# Django's session key for language (used by LocaleMiddleware)
# This is the standard key that Django's LocaleMiddleware expects
LANGUAGE_SESSION_KEY = '_language'


class UserLanguageMiddleware(MiddlewareMixin):
    """
    Custom middleware to activate user's preferred language for each request.

    This middleware runs for every request and determines which language to use
    based on a priority system. It works in conjunction with Django's built-in
    LocaleMiddleware to provide seamless bilingual support.

    Priority order (highest to lowest):
        1. Authenticated user's language field (from User model in database)
        2. Session language (set when user clicks language switcher on login page)
        3. Cookie language (persistent across sessions, set when language changes)
        4. Default language from settings.py (if none of the above are set)

    This ensures the correct language is active before any view processing occurs,
    allowing proper translation of all UI elements, messages, and content.

    Note:
        This middleware must be placed after SessionMiddleware and AuthenticationMiddleware
        in the MIDDLEWARE setting (see settings.py).
    """

    def process_request(self, request):
        """
        Process incoming request and activate the appropriate language.

        This method is called for every request before the view is executed.
        It determines the correct language to use and activates it for the current request.

        Args:
            request (HttpRequest): The incoming HTTP request object

        Returns:
            None: Middleware returns None to continue processing the request

        Side effects:
            - Activates the chosen language via translation.activate()
            - Sets request.LANGUAGE_CODE for use in templates and views
        """
        # First priority: Authenticated user's saved language preference
        # This ensures logged-in users always see their chosen language
        if request.user.is_authenticated:
            user_language = getattr(request.user, 'language', None)
            if user_language:
                translation.activate(user_language)
                request.LANGUAGE_CODE = user_language
                return

        # Second priority: Session language (for unauthenticated users)
        # This allows language selection on the login page before authentication
        session_language = request.session.get(LANGUAGE_SESSION_KEY)
        if session_language:
            translation.activate(session_language)
            request.LANGUAGE_CODE = session_language
            return

        # Third priority: Cookie language (fallback)
        # This provides persistence across sessions even when not logged in
        cookie_language = request.COOKIES.get('django_language')
        if cookie_language and cookie_language in ['en', 'ar']:
            translation.activate(cookie_language)
            request.LANGUAGE_CODE = cookie_language

        # If none of the above, Django will use LANGUAGE_CODE from settings.py (default: 'en')
