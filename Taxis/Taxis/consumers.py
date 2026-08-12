import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Chofer, PerfilUsuario


class TaxiColectivoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "central_taxis_colectivos"
        self.chofer_id = None
        self.usuario_id = None
        self.grupo_personal = None

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Identifica quien se conecta (chofer o cliente) por el JWT en la
        # URL (?token=...) y lo une a su grupo personal -- asi se le puede
        # mandar una alerta SOLO a el, sin importar si es un chofer o un
        # cliente esperando respuesta.
        info = await self._resolver_usuario_desde_token()
        if info:
            self.usuario_id = info["id_usuario"]
            if info["chofer_id"]:
                self.chofer_id = info["chofer_id"]
                self.grupo_personal = f"chofer_{self.chofer_id}"
            else:
                self.grupo_personal = f"cliente_{self.usuario_id}"
            await self.channel_layer.group_add(self.grupo_personal, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        if self.chofer_id:
            await self.marcar_chofer_inactivo(self.chofer_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_chofer_desconectado",
                    "chofer_id": self.chofer_id
                }
            )

        if self.grupo_personal:
            await self.channel_layer.group_discard(self.grupo_personal, self.channel_name)

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "finalizar_turno":
            chofer_id = data.get("chofer_id")
            await self.marcar_chofer_inactivo(chofer_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_chofer_desconectado",
                    "chofer_id": chofer_id
                }
            )

    # --- HANDLERS ASÍNCRONOS DE BROADCAST ---

    async def broadcast_ubicacion(self, event):
        await self.send(text_data=json.dumps({
            "event": "ubicacion_actualizada",
            "chofer_id": event["chofer_id"],
            "lat": event["latitud"],
            "lng": event["longitud"],
            "nombre": event.get("nombre", "Chofer en Ruta"),
            "vehiculo": event.get("vehiculo", "Vehículo Activo"),
            "modalidad": event.get("modalidad", "COLECTIVO"),
            "asientos_disponibles": event["asientos_disponibles"]
        }))

    async def broadcast_chofer_desconectado(self, event):
        await self.send(text_data=json.dumps({
            "event": "chofer_desconectado",
            "chofer_id": event["chofer_id"]
        }))

    async def notificar_cliente_colectivo(self, event):
        """SOLO al chofer elegido para ese cliente de colectivo."""
        await self.send(text_data=json.dumps({
            "event": "nuevo_cliente_colectivo",
            "viaje_id": event["viaje_id"],
            "cliente_nombre": event["cliente_nombre"],
            "lat": event["lat"],
            "lng": event["lng"],
            "asientos": event["asientos"],
            "requiere_cajuela": event["requiere_cajuela"],
        }))

    async def notificar_nueva_solicitud_especial(self, event):
        """SOLO al chofer candidato para un viaje especial (estilo Uber)."""
        await self.send(text_data=json.dumps({
            "event": "nueva_solicitud_especial",
            "viaje_id": event["viaje_id"],
            "cliente_nombre": event["cliente_nombre"],
            "origen_lat": event["origen_lat"],
            "origen_lng": event["origen_lng"],
            "origen_direccion": event["origen_direccion"],
            "destino_lat": event["destino_lat"],
            "destino_lng": event["destino_lng"],
            "destino_direccion": event["destino_direccion"],
            "asientos": event["asientos"],
            "requiere_cajuela": event["requiere_cajuela"],
        }))

    async def notificar_viaje_aceptado(self, event):
        """SOLO al cliente que espera respuesta de un viaje especial."""
        await self.send(text_data=json.dumps({
            "event": "viaje_aceptado",
            "viaje_id": event["viaje_id"],
            "chofer_nombre": event["chofer_nombre"],
            "vehiculo": event["vehiculo"],
            "chofer_lat": event.get("chofer_lat"),
            "chofer_lng": event.get("chofer_lng"),
        }))

    async def notificar_sin_chofer_disponible(self, event):
        """SOLO al cliente, cuando ya no quedan choferes candidatos."""
        await self.send(text_data=json.dumps({
            "event": "sin_chofer_disponible",
            "viaje_id": event["viaje_id"],
        }))

    # --- IDENTIFICACION POR TOKEN ---

    @database_sync_to_async
    def _resolver_usuario_desde_token(self):
        try:
            query_string = self.scope.get("query_string", b"").decode()
            token_str = parse_qs(query_string).get("token", [None])[0]
            if not token_str:
                return None

            access = AccessToken(token_str)
            user_id = access["user_id"]

            usuario = PerfilUsuario.objects.get(id_usuario=user_id)
            chofer_id = usuario.chofer_datos.id if hasattr(usuario, "chofer_datos") else None

            return {"id_usuario": usuario.id_usuario, "chofer_id": chofer_id}
        except (TokenError, PerfilUsuario.DoesNotExist, KeyError):
            return None

    # --- CONSULTAS A BASE DE DATOS ---

    @database_sync_to_async
    def marcar_chofer_inactivo(self, chofer_id):
        try:
            chofer = Chofer.objects.get(id=chofer_id)
            chofer.estado = 'inactivo'
            chofer.save()
        except Chofer.DoesNotExist:
            pass