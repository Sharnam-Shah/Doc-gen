"""
ASGI config for legal_doc_generator project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

# Ensure DJANGO_SETTINGS_MODULE is set before importing Django ASGI components
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_doc_generator.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import OriginValidator

# Import websocket_urlpatterns after settings are configured
django_asgi_app = get_asgi_application()

# Import routing after the Django application is initialized to ensure the app
# registry is ready before modules that define models are imported.
from generator.routing import websocket_urlpatterns
from django.conf import settings

# Configure WebSocket origin validation. In development we allow all origins
# (CORS_ALLOW_ALL_ORIGINS). In production you should set the WS_ALLOWED_ORIGINS
# env var (comma-separated) or set CORS_ALLOWED_ORIGINS in Django settings.
def _build_ws_application():
    # If CORS_ALLOW_ALL_ORIGINS is truthy, skip OriginValidator (allow all)
    if getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False):
        return AuthMiddlewareStack(URLRouter(websocket_urlpatterns))

    # First, check for an explicit env var
    env_origins = os.environ.get('WS_ALLOWED_ORIGINS')
    if env_origins:
        allowed = [o.strip() for o in env_origins.split(',') if o.strip()]
    else:
        allowed = getattr(settings, 'CORS_ALLOWED_ORIGINS', []) or []

    # If no allowed origins are configured, fall back to allowing all (safer for dev)
    if not allowed:
        return AuthMiddlewareStack(URLRouter(websocket_urlpatterns))

    # Use OriginValidator to restrict websocket connections to known origins
    return OriginValidator(
        AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
        allowed
    )

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": _build_ws_application(),
})
