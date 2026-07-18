import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import Taxicom.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Taxicom.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            Taxicom.routing.websocket_urlpatterns
        )
    ),
})