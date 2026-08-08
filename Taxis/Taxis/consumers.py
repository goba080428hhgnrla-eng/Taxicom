import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chofer, Viaje

class TaxiColectivoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "central_taxis_colectivos"
        self.chofer_id = None
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Si la conexión era de un chofer conocido, marcarlo inactivo en DB y avisar al mapa
        if self.chofer_id:
            await self.marcar_chofer_inactivo(self.chofer_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_chofer_desconectado",
                    "chofer_id": self.chofer_id
                }
            )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        # 1. ACTUALIZACIÓN DE UBICACIÓN
        if action == "actualizar_ubicacion_chofer":
            chofer_id = data.get("chofer_id")
            self.chofer_id = chofer_id
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

        # 2. FINALIZAR TURNO EXPLÍCITO
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

        # 3. SOLICITUD DE TAXI COLECTIVO
        elif action == "solicitar_parada_colectivo":
            cliente_id = data.get("cliente_id")
            origen_lat = data.get("origen_lat")
            origen_lng = data.get("origen_lng")
            destino_lat = data.get("destino_lat")
            destino_lng = data.get("destino_lng")
            asientos_pedidos = int(data.get("asientos", 1))

            chofer_asignado = await self.buscar_y_asignar_colectivo_inteligente(
                origen_lat, origen_lng, destino_lat, destino_lng, asientos_pedidos
            )

            if chofer_asignado:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "notificar_chofer_parada",
                        "chofer_id": chofer_asignado['id'],
                        "cliente_id": cliente_id,
                        "recoger_lat": origen_lat,
                        "recoger_lng": origen_lng,
                        "bajar_lat": destino_lat,
                        "bajar_lng": destino_lng,
                        "asientos": asientos_pedidos,
                        "tipo_servicio": "COLECTIVO"
                    }
                )
                await self.send(text_data=json.dumps({
                    "status": "asignado",
                    "message": f"El colectivo de {chofer_asignado['nombre']} ha recibido tu parada.",
                    "chofer_id": chofer_asignado['id']
                }))
            else:
                await self.send(text_data=json.dumps({
                    "status": "sin_cupo",
                    "message": "No hay colectivos disponibles en este tramo."
                }))

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

    async def notificar_chofer_parada(self, event):
        await self.send(text_data=json.dumps({
            "event": "nueva_parada_solicitada",
            "chofer_id": event["chofer_id"],
            "cliente_id": event["cliente_id"],
            "recoger_lat": event["recoger_lat"],
            "recoger_lng": event["recoger_lng"],
            "bajar_lat": event["bajar_lat"],
            "bajar_lng": event["bajar_lng"],
            "asientos": event["asientos"]
        }))

    # --- CONSULTAS A BASE DE DATOS ---

    @database_sync_to_async
    def guardar_posicion_chofer(self, chofer_id, lat, lng):
        try:
            chofer = Chofer.objects.select_related('usuario', 'vehiculo').get(id=chofer_id)
            if chofer.estado in ['pendiente', 'inactivo']:
                return None

            chofer.latitud = float(lat)
            chofer.longitud = float(lng)
            chofer.save()

            # Obtención segura de nombres para evitar AttributeError con PerfilUsuario
            usuario = getattr(chofer, 'usuario', None)
            if usuario:
                first_name = getattr(usuario, 'first_name', None) or getattr(usuario, 'nombre', '')
                last_name = getattr(usuario, 'last_name', None) or getattr(usuario, 'apellido', '')
                nombre_completo = f"{first_name} {last_name}".strip() or f"Chofer #{chofer.id}"
            else:
                nombre_completo = f"Chofer #{chofer.id}"

            info_vehiculo = f"{chofer.vehiculo.marca} {chofer.vehiculo.modelo}" if getattr(chofer, 'vehiculo', None) else "Taxi"

            return {
                'id': chofer.id,
                'nombre': nombre_completo,
                'vehiculo': info_vehiculo,
                'modalidad': getattr(chofer, 'modalidad', 'COLECTIVO'),
                'asientos_disponibles': getattr(chofer, 'asientos_disponibles', 4)
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