from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

# Django's session key for language (used by LocaleMiddleware)
LANGUAGE_SESSION_KEY = '_language'


class UserLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to activate user's preferred language from their profile or session
    """

    def process_request(self, request):
        # First priority: Authenticated user's saved language preference
        if request.user.is_authenticated:
            user_language = getattr(request.user, 'language', None)
            if user_language:
                translation.activate(user_language)
                request.LANGUAGE_CODE = user_language
                return

        # Second priority: Session language (for unauthenticated users)
        session_language = request.session.get(LANGUAGE_SESSION_KEY)
        if session_language:
            translation.activate(session_language)
            request.LANGUAGE_CODE = session_language
            return

        # Third priority: Cookie language (fallback)
        cookie_language = request.COOKIES.get('django_language')
        if cookie_language and cookie_language in ['en', 'ar']:
            translation.activate(cookie_language)
            request.LANGUAGE_CODE = cookie_language
