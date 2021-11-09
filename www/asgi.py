"""
ASGI config for www project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
from channels.http import AsgiHandler
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from django.core.asgi import get_asgi_application
from django.conf import settings
import logging

LOG = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'www.settings')
django_asgi_app = get_asgi_application()

def create_app():
    app_options = {
        "http": AsgiHandler(),
    }
    if 'kafka_example' in settings.INSTALLED_APPS:
        import kafka_example.channels.routing  # noqa
        app_options.update({
            "websocket": AuthMiddlewareStack(
                URLRouter(
                    kafka_example.channels.routing.websocket_urlpatterns
                )
            ),
            "channel": ChannelNameRouter(
                kafka_example.channels.routing.channelname_patterns
            ),
        })
    return ProtocolTypeRouter(app_options)

application = create_app()