from django.utils import translation
from django.utils.deprecation import MiddlewareMixin


class UserLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to activate user's preferred language from their profile
    """

    def process_request(self, request):
        if request.user.is_authenticated:
            # Get user's preferred language
            user_language = getattr(request.user, 'language', 'en')

            # Activate the language
            translation.activate(user_language)
            request.LANGUAGE_CODE = user_language
