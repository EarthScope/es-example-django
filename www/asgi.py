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

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'www.settings')
django_asgi_app = get_asgi_application()

import kafka_example.channels.routing  # noqa


def create_app():
    return ProtocolTypeRouter({
        "http": AsgiHandler(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                kafka_example.channels.routing.websocket_urlpatterns
            )
        ),
        "channel": ChannelNameRouter(
            kafka_example.channels.routing.channelname_patterns
        ),
    })

application = create_app()