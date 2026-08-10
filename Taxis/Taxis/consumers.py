import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Chofer, PerfilUsuario, Viaje


class TaxiColectivoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "central_taxis_colectivos"
        self.chofer_id = None
        self.grupo_personal = None

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Identifica al chofer por el JWT en la URL (?token=...), en vez de
        # confiar en un chofer_id que el cliente mande despues en un
        # mensaje -- eso permitia (por bug de origen) mandar cualquier id y
        # ademas no alcanzaba para armar un grupo personal antes de que el
        # chofer mandara su primera ubicacion.
        chofer_info = await self._resolver_chofer_desde_token()
        if chofer_info:
            self.chofer_id = chofer_info["id"]
            self.grupo_personal = f"chofer_{self.chofer_id}"
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

        # NOTA: la actualizacion de ubicacion por este canal (action=
        # "actualizar_ubicacion_chofer") ya no es necesaria -- TrackingService
        # ahora manda la ubicacion por REST (ActualizarUbicacionView), que
        # ya identifica al chofer por su token de forma segura. Si tu app
        # ya no manda mas esta action, puedes borrar este bloque completo
        # mas adelante; lo dejo por si todavia hay una version vieja de la
        # app en uso.
        if action == "actualizar_ubicacion_chofer":
            chofer_id = data.get("chofer_id")
            lat = data.get("latitud") or data.get("lat")
            lng = data.get("longitud") or data.get("lng")

            chofer_info = await self.guardar_posicion_chofer(chofer_id, lat, lng)

            if chofer_info:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "broadcast_ubicacion",
                        "chofer_id": chofer_info["id"],
                        "latitud": lat,
                        "longitud": lng,
                        "nombre": chofer_info["nombre"],
                        "vehiculo": chofer_info["vehiculo"],
                        "modalidad": chofer_info["modalidad"],
                        "asientos_disponibles": chofer_info["asientos_disponibles"]
                    }
                )

        elif action == "finalizar_turno":
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
        """
        Este SOLO le llega al chofer correcto -- se manda con
        group_send(f"chofer_{chofer.id}", ...) desde SolicitarColectivoView,
        nunca al grupo compartido central_taxis_colectivos.
        """
        await self.send(text_data=json.dumps({
            "event": "nuevo_cliente_colectivo",
            "viaje_id": event["viaje_id"],
            "cliente_nombre": event["cliente_nombre"],
            "lat": event["lat"],
            "lng": event["lng"],
            "asientos": event["asientos"],
            "requiere_cajuela": event["requiere_cajuela"],
        }))

    # --- IDENTIFICACION POR TOKEN ---

    @database_sync_to_async
    def _resolver_chofer_desde_token(self):
        try:
            query_string = self.scope.get("query_string", b"").decode()
            token_str = parse_qs(query_string).get("token", [None])[0]
            if not token_str:
                return None

            access = AccessToken(token_str)
            user_id = access["user_id"]

            usuario = PerfilUsuario.objects.get(id_usuario=user_id)
            if not hasattr(usuario, "chofer_datos"):
                return None

            return {"id": usuario.chofer_datos.id}
        except (TokenError, PerfilUsuario.DoesNotExist, KeyError):
            return None

    # --- CONSULTAS A BASE DE DATOS ---

    @database_sync_to_async
    def guardar_posicion_chofer(self, chofer_id, lat, lng):
        try:
            chofer = Chofer.objects.select_related('perfil', 'vehiculo').get(id=chofer_id)
            if chofer.estado in ['pendiente', 'inactivo']:
                return None

            chofer.latitud = float(lat)
            chofer.longitud = float(lng)
            chofer.save()

            nombre_completo = f"{chofer.perfil.nombre or ''} {chofer.perfil.apellido or ''}".strip() \
                or f"Chofer #{chofer.id}"

            info_vehiculo = f"{chofer.vehiculo.marca} {chofer.vehiculo.modelo}" if chofer.vehiculo else "Taxi"

            return {
                'id': chofer.id,
                'nombre': nombre_completo,
                'vehiculo': info_vehiculo,
                'modalidad': chofer.get_estado_display(),
                'asientos_disponibles': chofer.asientos_disponibles
            }
        except Chofer.DoesNotExist:
            return None

    @database_sync_to_async
    def marcar_chofer_inactivo(self, chofer_id):
        try:
            chofer = Chofer.objects.get(id=chofer_id)
            chofer.estado = 'inactivo'
            chofer.save()
        except Chofer.DoesNotExist:
            pass