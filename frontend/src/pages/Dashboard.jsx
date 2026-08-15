import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import { apiFetch } from '../api';

const taxiIcon = L.icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png',
  iconSize: [36, 36],
  iconAnchor: [18, 18],
  popupAnchor: [0, -18],
});

export default function Dashboard() {
  const [choferes, setChoferes] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [wsStatus, setWsStatus] = useState('Conectando...');

  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markers = useRef({});
  const socketRef = useRef(null);
  const reconnectTimeout = useRef(null);

  // Helper para validar y extraer coordenadas
  const obtenerCoordenadas = (data) => {
    const lat = data.latitud ?? data.lat;
    const lng = data.longitud ?? data.lng;

    if (lat === undefined || lng === undefined || lat === null || lng === null) {
      return null;
    }

    const latFloat = parseFloat(lat);
    const lngFloat = parseFloat(lng);

    if (isNaN(latFloat) || isNaN(lngFloat) || (latFloat === 0.0 && lngFloat === 0.0)) {
      return null;
    }

    return { lat: latFloat, lng: lngFloat };
  };

  const removerMarcador = (id) => {
    if (markers.current[id]) {
      mapInstance.current?.removeLayer(markers.current[id]);
      delete markers.current[id];
    }
  };

  const moverMarcadorFluidamente = (marker, targetLat, targetLng, duracion = 2000) => {
    const startLatLng = marker.getLatLng();
    const startLat = startLatLng.lat;
    const startLng = startLatLng.lng;

    if (startLat === targetLat && startLng === targetLng) return;

    const startTime = performance.now();

    function animar(currentTime) {
      const elapsedTime = currentTime - startTime;
      const progress = Math.min(elapsedTime / duracion, 1);

      const currentLat = startLat + (targetLat - startLat) * progress;
      const currentLng = startLng + (targetLng - startLng) * progress;

      marker.setLatLng([currentLat, currentLng]);

      if (progress < 1) {
        requestAnimationFrame(animar);
      }
    }

    requestAnimationFrame(animar);
  };

  const crearOActualizarMarcador = (id, lat, lng, nombre, auto, asientos) => {
    if (!lat || !lng) return;

    const popupContent = `
      <div style="width:240px; padding:4px; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:10px; color:#94a3b8;">CONDUCTOR</div>
            <div style="font-size:14px; font-weight:bold;">${nombre}</div>
          </div>
          <span>🚕</span>
        </div>
        <div style="margin-top:8px; padding:8px; background:#f8fafc; border-radius:8px;">
          <div style="font-size:10px; color:#94a3b8;">VEHÍCULO</div>
          <div style="font-size:12px; font-weight:600;">${auto}</div>
        </div>
        <div style="margin-top:6px; font-size:12px;">
          Asientos libres: <b>${asientos}</b>
        </div>
      </div>
    `;

    if (markers.current[id]) {
      moverMarcadorFluidamente(markers.current[id], lat, lng);
      markers.current[id].getPopup().setContent(popupContent);
    } else {
      markers.current[id] = L.marker([lat, lng], { icon: taxiIcon })
        .addTo(mapInstance.current)
        .bindPopup(popupContent);
    }
  };

  const conectarWebSocket = () => {
    const accessToken = localStorage.getItem('access_token') || localStorage.getItem('token');

    if (!accessToken) {
      setWsStatus('Sin token');
      return;
    }

    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(
      `${wsScheme}://${window.location.host}/ws/colectivos/?token=${accessToken}`
    );
    socketRef.current = socket;

    socket.onopen = () => {
      setWsStatus('WebSocket Conectado');
    };

    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);

      // CASO 1: DESCONEXIÓN / CHOFER INACTIVO
      if (data.type === 'broadcast_chofer_desconectado' || data.event === 'chofer_desconectado') {
        removerMarcador(data.chofer_id);
        
        // NO lo borramos de la lista, solo cambiamos su estado a Inactivo
        setChoferes((prev) =>
          prev.map((c) =>
            c.chofer_id === data.chofer_id
              ? { ...c, estado: 'Inactivo' }
              : c
          )
        );
        return;
      }

      // CASO 2: ACTUALIZACIÓN DE UBICACIÓN Y ESTADO
      const esBroadcastUbicacion = data.type === 'broadcast_ubicacion' || data.event === 'ubicacion_actualizada';
      const coords = obtenerCoordenadas(data);

      if ((esBroadcastUbicacion || coords) && data.chofer_id) {
        if (coords) {
          crearOActualizarMarcador(
            data.chofer_id,
            coords.lat,
            coords.lng,
            data.nombre || 'Chofer en Ruta',
            data.vehiculo || 'Vehículo Activo',
            data.asientos_disponibles ?? 0
          );
        }

        setChoferes((prev) => {
          const existe = prev.some((c) => c.chofer_id === data.chofer_id);

          if (!existe) {
            return [
              ...prev,
              {
                chofer_id: data.chofer_id,
                nombre: data.nombre || 'Chofer en Ruta',
                vehiculo: data.vehiculo || 'Vehículo Activo',
                asientos_disponibles: data.asientos_disponibles ?? 0,
                lat: coords?.lat,
                lng: coords?.lng,
                estado: data.modalidad || 'Activo',
              },
            ];
          }

          return prev.map((c) =>
            c.chofer_id === data.chofer_id
              ? {
                  ...c,
                  nombre: data.nombre || c.nombre,
                  vehiculo: data.vehiculo || c.vehiculo,
                  lat: coords ? coords.lat : c.lat,
                  lng: coords ? coords.lng : c.lng,
                  asientos_disponibles: data.asientos_disponibles ?? c.asientos_disponibles,
                  estado: data.modalidad || 'Activo',
                }
              : c
          );
        });
      }
    };

    socket.onclose = (e) => {
      setWsStatus(`Desconectado (code ${e.code})`);
      if (e.code !== 4001) {
        reconnectTimeout.current = setTimeout(conectarWebSocket, 3000);
      }
    };

    socket.onerror = () => {
      socket.close();
    };
  };

  useEffect(() => {
    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current, { zoomControl: false }).setView([19.727, -99.508], 13);
      L.control.zoom({ position: 'bottomright' }).addTo(mapInstance.current);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap © CARTO',
      }).addTo(mapInstance.current);
    }

    // CARGA INICIAL POR API REST
    // Si quieres traer TODOS los choferes (incluyendo inactivos), usa la vista general de choferes
    apiFetch('/api/v1/admin/choferes/')
      .then((res) => res.json())
      .then((data) => {
        const listaChoferes = data.results || data.choferes || (Array.isArray(data) ? data : []);
        setChoferes(listaChoferes);

        listaChoferes.forEach((c) => {
          const coords = obtenerCoordenadas(c);
          if (coords) {
            crearOActualizarMarcador(
              c.chofer_id || c.id,
              coords.lat,
              coords.lng,
              c.nombre,
              c.vehiculo,
              c.asientos_disponibles
            );
          }
        });
      })
      .catch((err) => console.error('Error cargando lista de choferes:', err));

    conectarWebSocket();

    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      socketRef.current?.close();
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, []);

  const seleccionarConductor = (chofer) => {
    const id = chofer.chofer_id || chofer.id;
    setSelectedDriver(id);
    const marker = markers.current[id];
    if (marker && mapInstance.current) {
      mapInstance.current.flyTo(marker.getLatLng(), 16, { duration: 0.8 });
      marker.openPopup();
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-50 text-slate-900 flex flex-col">
      <header className="w-full h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8">
        <p className="font-bold text-lg">CentralTaxi Admin</p>
        <span className="text-xs bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full font-semibold">
          {wsStatus}
        </span>
      </header>

      <main className="flex-1 w-full p-4 overflow-hidden">
        <div className="w-full h-full grid grid-cols-12 gap-4">
          <aside className="col-span-3 bg-white rounded-2xl border border-slate-200 p-4 overflow-y-auto">
            <h2 className="font-bold text-lg mb-4">Lista de Choferes ({choferes.length})</h2>
            {choferes.map((c) => {
              const id = c.chofer_id || c.id;
              const estaActivo = c.estado !== 'Inactivo' && c.estado !== 'inactivo';

              return (
                <button
                  key={id}
                  onClick={() => seleccionarConductor(c)}
                  className={`w-full text-left p-3 mb-2 rounded-xl border transition-all ${
                    selectedDriver === id ? 'bg-slate-900 text-white' : 'bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <div className="font-semibold text-sm">{c.nombre}</div>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                        estaActivo ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {c.estado || 'Inactivo'}
                    </span>
                  </div>
                  <div className="text-xs opacity-70 mt-1">{c.vehiculo}</div>
                  <div className="text-xs mt-1 opacity-80">Asientos libres: {c.asientos_disponibles ?? 0}</div>
                </button>
              );
            })}
            {choferes.length === 0 && (
              <p className="text-xs text-slate-400 text-center mt-8">
                No hay choferes registrados.
              </p>
            )}
          </aside>

          <section className="col-span-9 relative bg-white rounded-2xl border border-slate-200 overflow-hidden min-h-[500px]">
            <div ref={mapRef} className="absolute inset-0 z-0" />
          </section>
        </div>
      </main>
    </div>
  );
}