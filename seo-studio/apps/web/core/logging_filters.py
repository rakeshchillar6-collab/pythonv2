# core/logging_filters.py
import logging

class RequestContextFilter(logging.Filter):
    """
    A logging filter that injects request-specific context into log records.
    """
    def filter(self, record):
        # This uses thread-local storage behind the scenes to get the current request
        from .middleware import get_current_request

        request = get_current_request()

        if request:
            record.request_id = getattr(request, 'request_id', 'N/A')
            record.user_id = getattr(request.user, 'id', 'anonymous')
            record.site_id = getattr(request.site, 'id', 'N/A')
        else:
            record.request_id = 'N/A'
            record.user_id = 'N/A'
            record.site_id = 'N/A'

        return True
