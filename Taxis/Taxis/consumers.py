import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chofer, PerfilUsuario, Viaje

class TaxiColectivoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Canal unificado para dashboard web, pasajeros y unidades de taxi
        self.room_group_name = "central_taxis_colectivos"
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Procesa las acciones enviadas desde los dispositivos móviles Android y el Web.
        """
        data = json.loads(text_data)
        action = data.get("action")

        # 1. ACTUALIZACIÓN DE UBICACIÓN (Chofer envía coordenadas)
        if action == "actualizar_ubicacion_chofer":
            chofer_id = data.get("chofer_id")
            lat = data.get("latitud")
            lng = data.get("longitud")
            
            # Guardar en BD y traer datos descriptivos del chofer y vehículo
            chofer_info = await self.guardar_posicion_chofer(chofer_id, lat, lng)
            
            if chofer_info:
                # Transmitir el movimiento a todos los conectados (incluyendo Dashboard Web)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "broadcast_ubicacion",
                        "chofer_id": chofer_info["id"],
                        "latitud": lat,
                        "longitud": lng,
                        "nombre": chofer_info["nombre"],
                        "vehiculo": chofer_info["vehiculo"],
                        "sketchfab_id": chofer_info["sketchfab_id"],
                        "asientos_disponibles": chofer_info["asientos_disponibles"]
                    }
                )

        # 2. ACCIÓN DE "PARAR" TAXI COLECTIVO (Cliente solicita unidad)
        elif action == "solicitar_parada_colectivo":
            cliente_id = data.get("cliente_id")
            origen_lat = data.get("origen_lat")
            origen_lng = data.get("origen_lng")
            destino_lat = data.get("destino_lat")
            destino_lng = data.get("destino_lng")
            asientos_pedidos = int(data.get("asientos", 1))

            # Algoritmo de selección de unidad óptima
            chofer_asignado = await self.buscar_y_asignar_colectivo_inteligente(
                origen_lat, origen_lng, destino_lat, destino_lng, asientos_pedidos
            )

            if chofer_asignado:
                # Notificar la parada al chofer seleccionado
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
                        "asientos": asientos_pedidos
                    }
                )
                # Confirmación individual al cliente
                await self.send(text_data=json.dumps({
                    "status": "asignado",
                    "message": f"El taxi de {chofer_asignado['nombre']} ha recibido tu parada.",
                    "chofer_id": chofer_asignado['id']
                }))
            else:
                # Notificar falta de unidades disponibles
                await self.send(text_data=json.dumps({
                    "status": "sin_cupo",
                    "message": "No hay colectivos con asientos suficientes en este tramo."
                }))

        # 3. CONFIRMACIÓN DE ASCENSO/DESCENSO DE PASAJEROS
        elif action == "cambio_flujo_pasajeros":
            chofer_id = data.get("chofer_id")
            tipo_movimiento = data.get("tipo")  # "sube" o "baja"
            asientos = int(data.get("asientos", 1))
            
            nuevos_asientos = await self.actualizar_inventario_asientos(chofer_id, tipo_movimiento, asientos)
            
            # Notificar el cambio de disponibilidad en tiempo real
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_asientos_actualizados",
                    "chofer_id": chofer_id,
                    "asientos_disponibles": nuevos_asientos
                }
            )

    # --- HANDLERS ASÍNCRONOS DE BROADCAST ---

    async def broadcast_ubicacion(self, event):
        """
        Envía los datos de ubicación adaptados para actualizar los mapas Leaflet del Web y Android.
        """
        await self.send(text_data=json.dumps({
            "event": "ubicacion_actualizada",
            "chofer_id": event["chofer_id"],
            "lat": event["latitud"],
            "lng": event["longitud"],
            "nombre": event.get("nombre", "Chofer en Ruta"),
            "vehiculo": event.get("vehiculo", "Vehículo Activo"),
            "sketchfab_id": event.get("sketchfab_id", ""),
            "asientos_disponibles": event["asientos_disponibles"]
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

    async def broadcast_asientos_actualizados(self, event):
        await self.send(text_data=json.dumps({
            "event": "cupo_modificado",
            "chofer_id": event["chofer_id"],
            "asientos_disponibles": event["asientos_disponibles"]
        }))

    # --- INTERACCIONES CON LA BASE DE DATOS (MÉTODOS SYNC TO ASYNC) ---

    @database_sync_to_async
    def guardar_posicion_chofer(self, chofer_id, lat, lng):
        try:
            chofer = Chofer.objects.select_related('perfil', 'vehiculo').get(id=chofer_id)
            
            # Bloquear la actualización si el chofer no está aprobado aún
            if chofer.estado in ['pendiente', 'inactivo']:
                return None

            chofer.latitud = float(lat)
            chofer.longitud = float(lng)
            chofer.save()

            nombre_completo = f"{chofer.perfil.nombre} {chofer.perfil.apellido}".strip() if chofer.perfil else f"Chofer #{chofer.id}"
            info_vehiculo = f"{chofer.vehiculo.marca} {chofer.vehiculo.modelo}" if chofer.vehiculo else "Taxi Colectivo"
            sketchfab_model = chofer.vehiculo.sketchfab_model_id if chofer.vehiculo else ""

            return {
                'id': chofer.id,
                'nombre': nombre_completo,
                'vehiculo': info_vehiculo,
                'sketchfab_id': sketchfab_model,
                'asientos_disponibles': chofer.asientos_disponibles
            }
        except Chofer.DoesNotExist:
            return None

    @database_sync_to_async
    def actualizar_inventario_asientos(self, chofer_id, tipo, cantidad):
        try:
            chofer = Chofer.objects.select_related('vehiculo').get(id=chofer_id)
            if tipo == "sube":
                chofer.asientos_disponibles = max(0, chofer.asientos_disponibles - cantidad)
            elif tipo == "baja":
                limite_max = chofer.vehiculo.total_asientos if chofer.vehiculo and hasattr(chofer.vehiculo, 'total_asientos') else 4
                chofer.asientos_disponibles = min(limite_max, chofer.asientos_disponibles + cantidad)
            
            chofer.save()
            return chofer.asientos_disponibles
        except Chofer.DoesNotExist:
            return 4

    @database_sync_to_async
    def buscar_y_asignar_colectivo_inteligente(self, o_lat, o_lng, d_lat, d_lng, asientos_requeridos):
        """
        Filtra las unidades activas o en ruta con capacidad suficiente
        y asigna la más cercana.
        """
        choferes_disponibles = Chofer.objects.filter(
            estado__in=['activo', 'en_ruta'], 
            asientos_disponibles__gte=asientos_requeridos,
            latitud__isnull=False,
            longitud__isnull=False
        ).select_related('perfil')

        if not choferes_disponibles.exists():
            return None

        mejor_opcion = None
        menor_distancia = float('inf')

        for chofer in choferes_disponibles:
            # Distancia euclidiana aproximada
            distancia = ((chofer.latitud - float(o_lat))**2 + (chofer.longitud - float(o_lng))**2)**0.5
            if distancia < menor_distancia:
                menor_distancia = distancia
                mejor_opcion = chofer

        if mejor_opcion:
            return {
                'id': mejor_opcion.id,
                'nombre': mejor_opcion.perfil.nombre if mejor_opcion.perfil else f"Chofer #{mejor_opcion.id}"
            }
        return None