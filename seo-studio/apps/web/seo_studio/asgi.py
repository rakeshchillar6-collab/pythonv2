# seo_studio/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import editor.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seo_studio.settings.dev')

# The default get_asgi_application() handles HTTP requests.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            editor.routing.websocket_urlpatterns
        )
    ),
})
