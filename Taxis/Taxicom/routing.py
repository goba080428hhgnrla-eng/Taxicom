from django.urls import path
from Taxis import consumers

websocket_urlpatterns = [
    path('ws/colectivos/', consumers.TaxiColectivoConsumer.as_asgi()),
]