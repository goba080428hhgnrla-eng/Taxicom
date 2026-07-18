import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chofer, PerfilUsuario, Viaje

class TaxiColectivoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "central_taxis_colectivos"
        
        # Unir al cliente o chofer al canal unificado de transmisión
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
        Procesa las acciones enviadas desde los dispositivos móviles Android.
        """
        data = json.loads(text_data)
        action = data.get("action")

        # 1. ACTUALIZACIÓN DE UBICACIÓN (Enviada por el Chofer constantemente)
        if action == "actualizar_ubicacion_chofer":
            chofer_id = data.get("chofer_id")
            lat = data.get("latitud")
            lng = data.get("longitud")
            
            # Guardar coordenadas del chofer en la base de datos
            asientos_libres = await self.guardar_posicion_chofer(chofer_id, lat, lng)
            
            # Retransmitir a todos los clientes conectados el movimiento del coche en el mapa
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_ubicacion",
                    "chofer_id": chofer_id,
                    "latitud": lat,
                    "longitud": lng,
                    "asientos_disponibles": asientos_libres
                }
            )

        # 2. ACCIÓN DE "PARAR" TAXI COLECTIVO (Enviada por el Cliente)
        elif action == "solicitar_parada_colectivo":
            cliente_id = data.get("cliente_id")
            origen_lat = data.get("origen_lat")
            origen_lng = data.get("origen_lng")
            destino_lat = data.get("destino_lat")
            destino_lng = data.get("destino_lng")
            asientos_pedidos = int(data.get("asientos", 1))

            # Lógica inteligente: Buscar el taxi colectivo más óptimo con espacio suficiente
            chofer_asignado = await self.buscar_y_asignar_colectivo_inteligente(
                origen_lat, origen_lng, destino_lat, destino_lng, asientos_pedidos
            )

            if chofer_asignado:
                # Notificar directamente al chofer seleccionado en la app que tiene pasaje esperando
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
                # Confirmar al cliente que un vehículo va en camino a su parada
                await self.send(text_data=json.dumps({
                    "status": "asignado",
                    "message": f"El taxi de {chofer_asignado['nombre']} ha recibido tu parada.",
                    "chofer_id": chofer_asignado['id']
                }))
            else:
                # Informar al cliente si todas las unidades colectivas van llenas en ese tramo
                await self.send(text_data=json.dumps({
                    "status": "sin_cupo",
                    "message": "No hay colectivos con asientos disponibles en este momento."
                }))

        # 3. CONFIRMACIÓN DE ASCENSO/DESCENSO (Enviada por el Chofer al subir o bajar pasaje)
        elif action == "cambio_flujo_pasajeros":
            chofer_id = data.get("chofer_id")
            tipo_movimiento = data.get("tipo") # "sube" o "baja"
            asientos = int(data.get("asientos", 1))
            
            nuevos_asientos = await self.actualizar_inventario_asientos(chofer_id, tipo_movimiento, asientos)
            
            # Avisar al mapa global que el inventario del taxi cambió
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
            "latitud": event["latitud"],
            "longitud": event["longitud"],
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
            chofer = Chofer.objects.get(id=chofer_id)
            chofer.latitud = float(lat)
            chofer.longitud = float(lng)
            chofer.save()
            return chofer.asientos_disponibles
        except Chofer.DoesNotExist:
            return 4

    @database_sync_to_async
    def actualizar_inventario_asientos(self, chofer_id, tipo, cantidad):
        try:
            chofer = Chofer.objects.get(id=chofer_id)
            if tipo == "sube":
                chofer.asientos_disponibles = max(0, chofer.asientos_disponibles - cantidad)
            elif tipo == "baja":
                # No exceder la capacidad máxima configurada en su vehículo
                limite_max = chofer.vehiculo.total_asientos if chofer.vehiculo else 4
                chofer.asientos_disponibles = min(limite_max, chofer.asientos_disponibles + cantidad)
            chofer.save()
            return chofer.asientos_disponibles
        except Chofer.DoesNotExist:
            return 4

    @database_sync_to_async
    def buscar_y_asignar_colectivo_inteligente(self, o_lat, o_lng, d_lat, d_lng, asientos_requeridos):
        """
        Algoritmo predictivo básico: Filtra los choferes que están en modalidad 'activo'
        (Colectivo) y que cuentan con asientos suficientes en tiempo real.
        """
        choferes_disponibles = Chofer.objects.filter(
            estado='activo', 
            asientos_disponibles__gte=asientos_requeridos
        ).select_related('perfil')

        if not choferes_disponibles.exists():
            return None

        # Asigna la unidad más cercana basándose en cálculo euclidiano simple
        mejor_opcion = None
        menor_distancia = float('inf')

        for chofer in choferes_disponibles:
            distancia = ((chofer.latitud - float(o_lat))**2 + (chofer.longitud - float(o_lng))**2)**0.5
            if distancia < menor_distancia:
                menor_distancia = distancia
                mejor_opcion = chofer

        if mejor_opcion:
            return {
                'id': mejor_opcion.id,
                'nombre': mejor_opcion.perfil.nombre
            }
        return None