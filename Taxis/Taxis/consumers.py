import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Chofer, PerfilUsuario

GRUPO_COLECTIVOS = "central_taxis_colectivos"


class TaxiColectivoConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_group_name = GRUPO_COLECTIVOS
        self.chofer_id = None
        self.usuario_id = None
        self.grupo_personal = None

        # =====================================================
        # RESOLVER JWT
        # =====================================================
        info = await self._resolver_usuario_desde_token()

        if info is None:
            # Rechazar de forma explícita si el token no existe o es inválido
            await self.close(code=4001)
            return

        self.usuario_id = info["id_usuario"]
        self.chofer_id = info["chofer_id"]

        # =====================================================
        # GRUPO GENERAL
        # =====================================================
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # =====================================================
        # GRUPO PERSONAL
        # =====================================================
        if self.chofer_id:
            self.grupo_personal = f"chofer_{self.chofer_id}"
        else:
            self.grupo_personal = f"cliente_{self.usuario_id}"

        await self.channel_layer.group_add(
            self.grupo_personal,
            self.channel_name
        )

        await self.accept()

        print(
            f"WebSocket conectado "
            f"usuario={self.usuario_id} "
            f"chofer={self.chofer_id}"
        )

    # =========================================================
    # DISCONNECT
    # =========================================================
    async def disconnect(self, close_code):
        print(
            f"WebSocket desconectado "
            f"usuario={self.usuario_id} "
            f"chofer={self.chofer_id} "
            f"code={close_code}"
        )

        # Retirar sockets de los grupos registrados
        if self.grupo_personal:
            await self.channel_layer.group_discard(
                self.grupo_personal,
                self.channel_name
            )

        if hasattr(self, 'room_group_name') and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # =========================================================
    # RECEIVE
    # =========================================================
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get("action")
        msg_type = data.get("type")

        # =====================================================
        # HEARTBEAT (PING / PONG) - Evita timeouts 1006 en Render
        # =====================================================
        if action == "ping" or msg_type == "ping":
            await self.send(text_data=json.dumps({"event": "pong"}))
            return

        # =====================================================
        # FINALIZAR TURNO
        # =====================================================
        if action == "finalizar_turno":
            chofer_id = data.get("chofer_id")

            if not chofer_id:
                return

            if self.chofer_id != int(chofer_id):
                return

            await self.marcar_chofer_inactivo(self.chofer_id)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_chofer_desconectado",
                    "chofer_id": self.chofer_id
                }
            )

    # =========================================================
    # UBICACIÓN
    # =========================================================
    async def broadcast_ubicacion(self, event):
        await self.send(
            text_data=json.dumps({
                "event": "ubicacion_actualizada",
                "chofer_id": event["chofer_id"],
                "lat": event["latitud"],
                "lng": event["longitud"],
                "nombre": event.get("nombre", "Chofer en Ruta"),
                "vehiculo": event.get("vehiculo", "Vehículo Activo"),
                "modalidad": event.get("modalidad", "COLECTIVO"),
                "asientos_disponibles": event.get("asientos_disponibles", 0)
            })
        )

    # =========================================================
    # CHOFER DESCONECTADO
    # =========================================================
    async def broadcast_chofer_desconectado(self, event):
        await self.send(
            text_data=json.dumps({
                "event": "chofer_desconectado",
                "chofer_id": event["chofer_id"]
            })
        )

    # =========================================================
    # NUEVO CLIENTE COLECTIVO
    # =========================================================
    async def notificar_cliente_colectivo(self, event):
        await self.send(
            text_data=json.dumps({
                "event": "nuevo_cliente_colectivo",
                "viaje_id": event["viaje_id"],
                "cliente_nombre": event["cliente_nombre"],
                "lat": event["lat"],
                "lng": event["lng"],
                "asientos": event["asientos"],
                "requiere_cajuela": event["requiere_cajuela"]
            })
        )

    # =========================================================
    # SOLICITUD ESPECIAL
    # =========================================================
    async def notificar_nueva_solicitud_especial(self, event):
        await self.send(
            text_data=json.dumps({
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
                "requiere_cajuela": event["requiere_cajuela"]
            })
        )

    # =========================================================
    # VIAJE ACEPTADO
    # =========================================================
    async def notificar_viaje_aceptado(self, event):
        await self.send(
            text_data=json.dumps({
                "event": "viaje_aceptado",
                "viaje_id": event["viaje_id"],
                "chofer_nombre": event["chofer_nombre"],
                "vehiculo": event["vehiculo"],
                "chofer_lat": event.get("chofer_lat"),
                "chofer_lng": event.get("chofer_lng")
            })
        )

    # =========================================================
    # SIN CHOFER
    # =========================================================
    async def notificar_sin_chofer_disponible(self, event):
        await self.send(
            text_data=json.dumps({
                "event": "sin_chofer_disponible",
                "viaje_id": event["viaje_id"]
            })
        )

    # =========================================================
    # AUTENTICAR JWT
    # =========================================================
    @database_sync_to_async
    def _resolver_usuario_desde_token(self):
        try:
            query_string = self.scope.get("query_string", b"").decode()
            token_str = parse_qs(query_string).get("token", [None])[0]

            if not token_str or not token_str.strip():
                return None

            access = AccessToken(token_str)
            user_id = access["user_id"]

            usuario = PerfilUsuario.objects.get(id_usuario=user_id)

            try:
                chofer = usuario.chofer_datos
                chofer_id = chofer.id
            except (Chofer.DoesNotExist, AttributeError):
                chofer_id = None

            return {
                "id_usuario": usuario.id_usuario,
                "chofer_id": chofer_id
            }

        except (TokenError, PerfilUsuario.DoesNotExist, KeyError, ValueError):
            return None

    # =========================================================
    # MARCAR INACTIVO
    # =========================================================
    @database_sync_to_async
    def marcar_chofer_inactivo(self, chofer_id):
        try:
            chofer = Chofer.objects.get(id=chofer_id)
            chofer.estado = "inactivo"
            chofer.save(update_fields=["estado"])
        except Chofer.DoesNotExist:
            pass