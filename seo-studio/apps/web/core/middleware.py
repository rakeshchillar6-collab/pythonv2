# core/middleware.py
from django.utils.deprecation import MiddlewareMixin
from .models import Site

class SiteMiddleware(MiddlewareMixin):
    """
    Attaches the current site to the request object based on the user.
    This simplifies getting the current site in views and other middleware.
    """
    def process_request(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'organization') and request.user.organization:
            # A simple approach: attach the first site found for the user's organization.
            # A more complex app might determine the site from the hostname or a URL path.
            site = Site.objects.filter(organization=request.user.organization).first()
            request.site = site
        else:
            request.site = None
