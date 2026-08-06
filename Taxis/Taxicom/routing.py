from django.urls import re_path
from Taxis import consumers

websocket_urlpatterns = [
    re_path(r'^ws/colectivos/$', consumers.TaxiColectivoConsumer.as_asgi()),
]