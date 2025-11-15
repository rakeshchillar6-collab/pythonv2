# common/managers/site_manager.py
from django.db import models
from django.core.exceptions import ImproperlyConfigured

class SiteManager(models.Manager):
    """
    A custom model manager that automatically filters querysets by the site
    associated with the current request.

    This is a critical component for enforcing multi-tenant data isolation.
    """
    def get_queryset(self, site=None):
        if site is None:
            # In a real application, you might raise an error or have a different
            # default behavior depending on the context (e.g., admin vs. API).
            # For now, we return an empty queryset if the site is not provided.
            return super().get_queryset().none()

        return super().get_queryset().filter(site=site)

    def from_request(self, request):
        """
        A helper method to get a site-filtered queryset directly from a request.
        """
        if not hasattr(request, 'site') or request.site is None:
             raise ImproperlyConfigured(
                "SiteManager requires a 'site' attribute on the request object. "
                "Ensure SiteMiddleware is installed and configured correctly."
            )
        return self.get_queryset(site=request.site)
