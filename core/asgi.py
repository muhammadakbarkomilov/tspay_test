import os
import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# DJANGO_SETTINGS_MODULE ni aniqlang
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 🟢 Django ilovalarini yuklash
django.setup()

# 🔄 Websocket routingni keyin chaqiring
import notification.routing

# ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notification.routing.websocket_urlpatterns
        )
    ),
})