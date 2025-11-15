# core/middleware.py
import uuid
import threading
from django.utils.deprecation import MiddlewareMixin
from .models import Site

_thread_locals = threading.local()

def get_current_request():
    """Returns the current request object from thread-local storage."""
    return getattr(_thread_locals, 'request', None)

class RequestIdMiddleware(MiddlewareMixin):
    """
    Injects a unique request_id and stores the request in thread-local storage.
    """
    def process_request(self, request):
        request.request_id = str(uuid.uuid4())
        _thread_locals.request = request

    def process_response(self, request, response):
        # Clean up to prevent memory leaks
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response

class SiteMiddleware(MiddlewareMixin):
    """
    Attaches the current site to the request object based on the user.
    This simplifies getting the current site in views and other middleware.
    """
    def process_request(self, request):
        request.site = None
        if request.user.is_authenticated and request.user.organization_id:
            site = Site.objects.filter(organization=request.user.organization).first()
            if not site and not request.path.startswith('/admin'):
                 from django.http import HttpResponseForbidden
                 return HttpResponseForbidden("Site configuration error: No site found for your organization.")
            request.site = site
