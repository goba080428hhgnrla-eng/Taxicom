import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css'; // Asegúrate de tener importados los estilos de Leaflet

export default function Dashboard() {
  const [choferes, setChoferes] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markers = useRef({});
  const socketRef = useRef(null);

  // =========================================================
  // ICONO PERSONALIZADO PARA LEAFLET
  // =========================================================
  const taxiIcon = L.icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png', // Cambia por tu propio icono si lo deseas
    iconSize: [35, 35],
    iconAnchor: [17, 35],
    popupAnchor: [0, -35],
  });

  // =========================================================
  // HELPER: OBTENER COORDENADAS (ACEPTA 0.0)
  // =========================================================
  const obtenerCoordenadas = (data) => {
    // Lee las variables exactas que manda tu backend en Django (choferes.py)
    const lat = data.latitud ?? data.lat;
    const lng = data.longitud ?? data.lng;

    if (lat === undefined || lng === undefined || lat === null || lng === null) {
      return null;
    }

    const latFloat = parseFloat(lat);
    const lngFloat = parseFloat(lng);

    if (isNaN(latFloat) || isNaN(lngFloat)) return null;

    return { lat: latFloat, lng: lngFloat };
  };

  // =========================================================
  // HELPER: DIBUJAR O ACTUALIZAR MARCADOR
  // =========================================================
  const dibujarOActualizarMarcador = (chofer) => {
    const coords = obtenerCoordenadas(chofer);
    if (!coords) return; // Si no hay coordenadas válidas (NaN/null), no dibujamos

    const id = chofer.chofer_id || chofer.id;
    const nombre = chofer.nombre || 'Chofer Activo';
    const vehiculo = chofer.vehiculo || 'Vehículo';
    const asientos = chofer.asientos_disponibles ?? 0;

    const popupContent = `
      <div style="font-family:sans-serif; min-width:150px;">
        <div style="font-size:14px; font-weight:bold;">${nombre}</div>
        <div style="font-size:12px; color:#64748b; margin-top:2px;">${vehiculo}</div>
        <div style="font-size:12px; margin-top:6px; background:#f1f5f9; padding:4px; border-radius:4px;">
          Asientos libres: <b>${asientos}</b>
        </div>
      </div>
    `;

    if (markers.current[id]) {
      // Si el marcador ya existe, lo movemos y actualizamos la info
      markers.current[id].setLatLng([coords.lat, coords.lng]);
      markers.current[id].getPopup().setContent(popupContent);
    } else if (mapInstance.current) {
      // Si no existe, lo creamos y lo añadimos al mapa
      markers.current[id] = L.marker([coords.lat, coords.lng], { icon: taxiIcon })
        .addTo(mapInstance.current)
        .bindPopup(popupContent);
    }
  };

  // =========================================================
  // HELPER: QUITAR MARCADOR DEL MAPA
  // =========================================================
  const removerMarcador = (id) => {
    if (markers.current[id] && mapInstance.current) {
      mapInstance.current.removeLayer(markers.current[id]);
      delete markers.current[id];
    }
  };

  // =========================================================
  // CARGA INICIAL (HTTP REST)
  // =========================================================
  const cargarChoferesIniciales = async () => {
    try {
      const token = localStorage.getItem('token') || '';
      const res = await fetch('/api/v1/admin/choferes/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (res.ok) {
        const data = await res.json();
        // Ajusta esto dependiendo de si tu API devuelve paginación o un array directo
        const lista = Array.isArray(data) ? data : (data.results || []);
        
        setChoferes(lista);

        // Dibujar en el mapa todos los choferes que estén activos al recargar la página
        lista.forEach((c) => {
          if (c.estado !== 'Inactivo' && c.estado !== 'inactivo') {
            dibujarOActualizarMarcador(c);
          }
        });
      }
    } catch (err) {
      console.error('❌ Error cargando lista inicial de choferes:', err);
    }
  };

  // =========================================================
  // EFECTO PRINCIPAL (INICIALIZAR MAPA Y WEBSOCKET)
  // =========================================================
  useEffect(() => {
    // 1. Inicializar Mapa Leaflet (evita inicializarlo 2 veces)
    if (!mapInstance.current && mapRef.current) {
      mapInstance.current = L.map(mapRef.current).setView([19.727, -99.508], 13); // Cambia las coordenadas por tu ciudad
      
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap © CARTO',
      }).addTo(mapInstance.current);
      
      // Forzar recálculo del tamaño después del render
      setTimeout(() => mapInstance.current?.invalidateSize(), 300);
    }

    // 2. Traer registros por API
    cargarChoferesIniciales();

    // 3. Configurar WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const token = localStorage.getItem('token') || '';
    const wsUrl = `${protocol}//${host}/ws/colectivos/?token=${token}`;

    console.log('⚡ Intentando conectar WebSocket a:', wsUrl);
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => console.log('✅ WebSocket Conectado Correctamente');
    ws.onerror = (err) => console.error('❌ Error en WebSocket:', err);
    ws.onclose = () => console.warn('⚠️ WebSocket Cerrado');

    // 4. Escuchar mensajes del WebSocket
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      console.log('📡 Evento WS:', data);

      // CASO A: Chofer Desconectado o Inactivo
      if (data.type === 'broadcast_chofer_desconectado') {
        removerMarcador(data.chofer_id);
        setChoferes((prev) =>
          prev.map((c) => {
            const idActual = c.chofer_id || c.id;
            if (idActual === data.chofer_id) {
              return { ...c, estado: 'Inactivo' };
            }
            return c;
          })
        );
        return;
      }

      // CASO B: Recepción de Ubicación (Activo)
      if (data.type === 'broadcast_ubicacion' && data.chofer_id) {
        // Dibuja la chincheta (incluso si viene en 0.0)
        dibujarOActualizarMarcador(data);

        // Actualiza el listado lateral
        setChoferes((prev) => {
          const existe = prev.some((c) => (c.chofer_id || c.id) === data.chofer_id);

          if (!existe) {
            // Es un chofer nuevo que acaba de reportar ubicación
            return [
              ...prev,
              {
                chofer_id: data.chofer_id,
                nombre: data.nombre,
                vehiculo: data.vehiculo,
                asientos_disponibles: data.asientos_disponibles,
                latitud: data.latitud,
                longitud: data.longitud,
                estado: data.modalidad || 'Activo',
              },
            ];
          }

          // Es un chofer existente, actualizamos su info
          return prev.map((c) => {
            const idActual = c.chofer_id || c.id;
            if (idActual === data.chofer_id) {
              return {
                ...c,
                ...data, // Mezclamos la nueva data del backend (incluye latitud/longitud)
                estado: data.modalidad || 'Activo', // Nos aseguramos de marcarlo activo
              };
            }
            return c;
          });
        });
      }
    };

    // 5. Limpieza al desmontar el componente
    return () => {
      if (socketRef.current) socketRef.current.close();
      // Opcional: si desmontas la vista completamente, podrías destruir el mapa aquí
      // if (mapInstance.current) { mapInstance.current.remove(); mapInstance.current = null; }
    };
  }, []);

  // =========================================================
  // RENDER DE LA INTERFAZ
  // =========================================================
  return (
    <div className="grid grid-cols-12 h-screen w-full bg-slate-50">
      
      {/* SIDEBAR LISTA DE CHOFERES */}
      <aside className="col-span-12 md:col-span-3 bg-white p-4 overflow-y-auto border-r border-slate-200 z-10 shadow-lg">
        <h2 className="font-bold text-lg text-slate-800 mb-4">
          Choferes en Sistema ({choferes.length})
        </h2>
        
        {choferes.length === 0 && (
          <p className="text-sm text-slate-500 text-center mt-10">No hay datos disponibles.</p>
        )}

        {choferes.map((c) => {
          const id = c.chofer_id || c.id;
          const estaActivo = c.estado !== 'Inactivo' && c.estado !== 'inactivo';
          
          return (
            <div
              key={id}
              onClick={() => {
                setSelectedDriver(id);
                // Si existe el marcador, volamos hacia él y abrimos su popup
                if (markers.current[id] && mapInstance.current) {
                  mapInstance.current.flyTo(markers.current[id].getLatLng(), 16, { duration: 0.8 });
                  markers.current[id].openPopup();
                }
              }}
              className={`p-3 mb-3 rounded-xl border transition-all cursor-pointer shadow-sm
                ${selectedDriver === id 
                  ? 'bg-slate-800 text-white border-slate-800' 
                  : 'bg-white hover:bg-slate-50 border-slate-200'
                }`}
            >
              <div className="flex justify-between items-start">
                <span className="font-semibold text-sm truncate pr-2">{c.nombre || 'Sin nombre'}</span>
                
                {/* Badge de Estado Visual */}
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold whitespace-nowrap
                  ${estaActivo 
                    ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' 
                    : 'bg-slate-100 text-slate-500 border border-slate-200'
                  }`}
                >
                  {estaActivo ? (c.estado || 'Activo').toUpperCase() : 'INACTIVO'}
                </span>
              </div>
              
              <div className={`text-xs mt-1 truncate ${selectedDriver === id ? 'text-slate-300' : 'text-slate-500'}`}>
                {c.vehiculo || 'Vehículo desconocido'}
              </div>
              
              {estaActivo && (
                <div className={`text-xs mt-2 font-medium ${selectedDriver === id ? 'text-emerald-300' : 'text-emerald-600'}`}>
                  Asientos libres: {c.asientos_disponibles ?? 0}
                </div>
              )}
            </div>
          );
        })}
      </aside>

      {/* ÁREA DEL MAPA */}
      <main className="col-span-12 md:col-span-9 h-full w-full relative z-0">
        <div ref={mapRef} className="h-full w-full" style={{ minHeight: '100vh' }} />
      </main>

    </div>
  );
}