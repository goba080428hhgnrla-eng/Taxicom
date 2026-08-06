import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chofer, Viaje

class TaxiColectivoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Canal unificado para dashboard web, pasajeros y unidades
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
        data = json.loads(text_data)
        action = data.get("action")

        # 1. ACTUALIZACIÓN DE UBICACIÓN (Especial o Colectivo)
        if action == "actualizar_ubicacion_chofer":
            chofer_id = data.get("chofer_id")
            lat = data.get("latitud")
            lng = data.get("longitud")
            
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
                        "modalidad": chofer_info["modalidad"],  # "ESPECIAL" o "COLECTIVO"
                        "asientos_disponibles": chofer_info["asientos_disponibles"]
                    }
                )

        # 2. SOLICITUD DE TAXI COLECTIVO (Por asientos)
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

        # 3. SOLICITUD DE TAXI ESPECIAL (Viaje Privado)
        elif action == "solicitar_viaje_especial":
            cliente_id = data.get("cliente_id")
            origen_lat = data.get("origen_lat")
            origen_lng = data.get("origen_lng")

            chofer_especial = await self.buscar_chofer_especial_cercano(origen_lat, origen_lng)

            if chofer_especial:
                await self.send(text_data=json.dumps({
                    "status": "asignado",
                    "message": f"Taxi Especial asignado: {chofer_especial['nombre']}",
                    "chofer_id": chofer_especial['id']
                }))
            else:
                await self.send(text_data=json.dumps({
                    "status": "sin_unidades",
                    "message": "No hay taxis especiales disponibles cerca."
                }))

        # 4. CAMBIO DE PASAJEROS (Solo aplica a Colectivos)
        elif action == "cambio_flujo_pasajeros":
            chofer_id = data.get("chofer_id")
            tipo_movimiento = data.get("tipo")  # "sube" o "baja"
            asientos = int(data.get("asientos", 1))
            
            nuevos_asientos = await self.actualizar_inventario_asientos(chofer_id, tipo_movimiento, asientos)
            
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
        await self.send(text_data=json.dumps({
            "event": "ubicacion_actualizada",
            "chofer_id": event["chofer_id"],
            "lat": event["latitud"],
            "lng": event["longitud"],
            "nombre": event.get("nombre", "Chofer en Ruta"),
            "vehiculo": event.get("vehiculo", "Vehículo Activo"),
            "modalidad": event.get("modalidad", "COLECTIVO"), # "ESPECIAL" o "COLECTIVO"
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

    # --- CONSULTAS A BASE DE DATOS ---

    @database_sync_to_async
    def guardar_posicion_chofer(self, chofer_id, lat, lng):
        try:
            # Usar select_related según la relación con el usuario en tu modelo
            chofer = Chofer.objects.select_related('usuario', 'vehiculo').get(id=chofer_id)
            
            if chofer.estado in ['pendiente', 'inactivo']:
                return None

            chofer.latitud = float(lat)
            chofer.longitud = float(lng)
            chofer.save()

            nombre_completo = f"{chofer.usuario.first_name} {chofer.usuario.last_name}".strip() if hasattr(chofer, 'usuario') else f"Chofer #{chofer.id}"
            info_vehiculo = f"{chofer.vehiculo.marca} {chofer.vehiculo.modelo}" if getattr(chofer, 'vehiculo', None) else "Taxi"
            
            # Obtener modalidad (si no existe el campo en el modelo, por defecto se asume 'COLECTIVO')
            modalidad = getattr(chofer, 'modalidad', 'COLECTIVO')

            return {
                'id': chofer.id,
                'nombre': nombre_completo,
                'vehiculo': info_vehiculo,
                'modalidad': modalidad,
                'asientos_disponibles': getattr(chofer, 'asientos_disponibles', 4)
            }
        except Chofer.DoesNotExist:
            return None

    @database_sync_to_async
    def buscar_y_asignar_colectivo_inteligente(self, o_lat, o_lng, d_lat, d_lng, asientos_requeridos):
        # Filtra únicamente los taxis en modalidad COLECTIVO
        choferes = Chofer.objects.filter(
            estado__in=['activo', 'en_ruta'],
            modalidad='COLECTIVO',
            asientos_disponibles__gte=asientos_requeridos,
            latitud__isnull=False,
            longitud__isnull=False
        ).select_related('usuario')

        if not choferes.exists():
            return None

        mejor_opcion = None
        menor_distancia = float('inf')

        for chofer in choferes:
            distancia = ((chofer.latitud - float(o_lat))**2 + (chofer.longitud - float(o_lng))**2)**0.5
            if distancia < menor_distancia:
                menor_distancia = distancia
                mejor_opcion = chofer

        if mejor_opcion:
            return {
                'id': mejor_opcion.id,
                'nombre': mejor_opcion.usuario.first_name if hasattr(mejor_opcion, 'usuario') else f"Chofer #{mejor_opcion.id}"
            }
        return None

    @database_sync_to_async
    def buscar_chofer_especial_cercano(self, o_lat, o_lng):
        # Filtra únicamente taxis en modalidad ESPECIAL y que estén libres
        choferes = Chofer.objects.filter(
            estado='activo',
            modalidad='ESPECIAL',
            latitud__isnull=False,
            longitud__isnull=False
        ).select_related('usuario')

        if not choferes.exists():
            return None

        mejor_opcion = None
        menor_distancia = float('inf')

        for chofer in choferes:
            distancia = ((chofer.latitud - float(o_lat))**2 + (chofer.longitud - float(o_lng))**2)**0.5
            if distancia < menor_distancia:
                menor_distancia = distancia
                mejor_opcion = chofer

        if mejor_opcion:
            return {
                'id': mejor_opcion.id,
                'nombre': mejor_opcion.usuario.first_name if hasattr(mejor_opcion, 'usuario') else f"Chofer #{mejor_opcion.id}"
            }
        return None

    @database_sync_to_async
    def actualizar_inventario_asientos(self, chofer_id, tipo, cantidad):
        try:
            chofer = Chofer.objects.get(id=chofer_id)
            if tipo == "sube":
                chofer.asientos_disponibles = max(0, chofer.asientos_disponibles - cantidad)
            elif tipo == "baja":
                chofer.asientos_disponibles = min(4, chofer.asientos_disponibles + cantidad)
            
            chofer.save()
            return chofer.asientos_disponibles
        except Chofer.DoesNotExist:
            return 4