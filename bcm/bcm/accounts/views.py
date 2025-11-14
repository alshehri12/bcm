from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import UserLoginForm, CustomPasswordResetForm, CustomSetPasswordForm


class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'accounts/login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dashboard:home')


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view"""
    template_name = 'accounts/password_reset.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view"""
    template_name = 'accounts/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


def set_language(request):
    """
    Handle language switching for both authenticated and unauthenticated users.

    This view is called when users click the English/Arabic language switcher buttons
    on the login page or in the navigation bar. It handles language preference in three ways:
    1. Session storage (for immediate effect and unauthenticated users)
    2. Cookie storage (for persistence across sessions)
    3. Database storage (for authenticated users)

    The three-tier storage ensures:
    - Immediate language switch on the current page
    - Language persists across browser sessions (via cookie)
    - Logged-in users see their preference on all devices (via database)

    Args:
        request (HttpRequest): The HTTP request containing language preference in POST data

    POST Parameters:
        language (str): The selected language code ('en' or 'ar')
        next (str): Optional URL to redirect to after language change

    Returns:
        HttpResponseRedirect: Redirects back to the page the user came from

    Process Flow:
        1. Validate POST request and language code
        2. Activate language for current request
        3. Store in session (picked up by UserLanguageMiddleware)
        4. Store in cookie (1 year expiry for long-term persistence)
        5. If user is logged in, save to User model in database
        6. Redirect back to original page with new language active

    Security:
        - Only accepts 'en' and 'ar' to prevent injection attacks
        - Uses Django's translation.activate() for safe language activation
        - Validates language before storing in session/cookie/database

    Example:
        Form on login page:
        <form method="post" action="{% url 'accounts:set_language' %}">
            {% csrf_token %}
            <input type="hidden" name="next" value="{% url 'accounts:login' %}">
            <button type="submit" name="language" value="ar">العربية</button>
        </form>
    """
    from django.utils import translation
    from django.http import HttpResponseRedirect

    # Django's standard session key for language (used by LocaleMiddleware)
    LANGUAGE_SESSION_KEY = '_language'

    if request.method == 'POST':
        # Get the selected language from POST data (default to English)
        language = request.POST.get('language', 'en')

        # Only process valid language codes to prevent security issues
        if language in ['en', 'ar']:
            # Step 1: Activate language for the current request immediately
            # This ensures the redirect response shows the new language
            translation.activate(language)

            # Step 2: Prepare redirect response
            # Redirect to the 'next' URL if provided, otherwise go back to referer
            next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
            response = HttpResponseRedirect(next_url)

            # Step 3: Store language in session
            # This is picked up by UserLanguageMiddleware on the next request
            # and by Django's built-in LocaleMiddleware
            request.session[LANGUAGE_SESSION_KEY] = language

            # Step 4: Store language in a long-lived cookie
            # This ensures language preference persists even after session expires
            # Cookie lasts for 1 year (365 days)
            response.set_cookie(
                'django_language',  # Cookie name
                language,           # Cookie value ('en' or 'ar')
                max_age=365 * 24 * 60 * 60  # Expiry: 1 year in seconds
            )

            # Step 5: Save to user profile if authenticated
            # This ensures the user sees their preferred language across devices/browsers
            if request.user.is_authenticated:
                request.user.language = language
                request.user.save(update_fields=['language'])  # Only update language field for efficiency
                messages.success(request, 'Language changed successfully.')

            return response

    # If not POST or invalid language, redirect back to where they came from
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)
