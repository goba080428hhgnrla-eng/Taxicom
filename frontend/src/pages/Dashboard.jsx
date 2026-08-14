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

  // =========================================================
  // ANIMACIÓN Y ELIMINACIÓN DE MARCADORES
  // =========================================================

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

  const crearOActualizarMarcador = (id, lat, lng, nombre, auto, sketchfabId, asientos) => {
    if (!lat || !lng || parseFloat(lat) === 0.0) return;

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
      moverMarcadorFluidamente(markers.current[id], parseFloat(lat), parseFloat(lng));
      markers.current[id].getPopup().setContent(popupContent);
    } else {
      markers.current[id] = L.marker([parseFloat(lat), parseFloat(lng)], { icon: taxiIcon })
        .addTo(mapInstance.current)
        .bindPopup(popupContent);
    }
  };

  // =========================================================
  // WEBSOCKET (con token + reconexión)
  // =========================================================

  const conectarWebSocket = () => {
    // AJUSTA ESTA LÍNEA a donde realmente guardas el access token
    // (localStorage, un contexto de auth, etc. — debe ser el mismo
    // que usa apiFetch para el header Authorization).
    const accessToken = localStorage.getItem('access_token');

    if (!accessToken) {
      console.error('No hay access token disponible, no se puede abrir el WebSocket');
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

      // CASO 1: CHOFER FINALIZÓ TURNO O SE DESCONECTÓ
      if (data.event === 'chofer_desconectado') {
        removerMarcador(data.chofer_id);
        setChoferes((prev) => prev.filter((c) => c.chofer_id !== data.chofer_id));
        return;
      }

      // CASO 2: ACTUALIZACIÓN DE UBICACIÓN
      if (data.event === 'ubicacion_actualizada' || data.lat) {
        crearOActualizarMarcador(
          data.chofer_id,
          data.lat,
          data.lng,
          data.nombre || 'Chofer en Ruta',
          data.vehiculo || 'Vehículo Activo',
          data.sketchfab_id || '',
          data.asientos_disponibles ?? 0
        );

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
                estado: 'En Ruta',
              },
            ];
          }
          return prev.map((c) =>
            c.chofer_id === data.chofer_id
              ? {
                  ...c,
                  lat: data.lat,
                  lng: data.lng,
                  asientos_disponibles: data.asientos_disponibles ?? c.asientos_disponibles,
                  estado: 'En Ruta',
                }
              : c
          );
        });
      }
    };

    socket.onclose = (e) => {
      setWsStatus(`Desconectado (code ${e.code})`);

      // code 4001 = token ausente/ inválido -> no tiene caso reintentar
      // solo, hay que revisar el token. Cualquier otro código sí
      // reintenta la conexión.
      if (e.code !== 4001) {
        reconnectTimeout.current = setTimeout(conectarWebSocket, 3000);
      } else {
        console.error('WebSocket rechazado por autenticación (code 4001)');
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

    // CARGA INICIAL POR API
    apiFetch('/api/v1/admin/choferes/mapa/')
      .then((res) => res.json())
      .then((data) => {
        setChoferes(data.choferes || []);
        data.choferes?.forEach((c) => {
          crearOActualizarMarcador(
            c.chofer_id,
            c.lat,
            c.lng,
            c.nombre,
            c.vehiculo,
            c.sketchfab_id,
            c.asientos_disponibles
          );
        });
      })
      .catch((err) => console.error('Error cargando flota:', err));

    // WEBSOCKET
    conectarWebSocket();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      socketRef.current?.close();
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, []);

  const seleccionarConductor = (chofer) => {
    setSelectedDriver(chofer.chofer_id);
    const marker = markers.current[chofer.chofer_id];
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
            <h2 className="font-bold text-lg mb-4">Vehículos Activos ({choferes.length})</h2>
            {choferes.map((c) => (
              <button
                key={c.chofer_id}
                onClick={() => seleccionarConductor(c)}
                className={`w-full text-left p-3 mb-2 rounded-xl border ${
                  selectedDriver === c.chofer_id ? 'bg-slate-900 text-white' : 'bg-white hover:bg-slate-50'
                }`}
              >
                <div className="font-semibold text-sm">{c.nombre}</div>
                <div className="text-xs opacity-70">{c.vehiculo}</div>
                <div className="text-xs mt-2">Free seats: {c.asientos_disponibles}</div>
              </button>
            ))}
          </aside>

          <section className="col-span-9 relative bg-white rounded-2xl border border-slate-200 overflow-hidden min-h-[500px]">
            <div ref={mapRef} className="absolute inset-0 z-0" />
          </section>
        </div>
      </main>
    </div>
  );
}