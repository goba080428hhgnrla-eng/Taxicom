import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
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
  const pingInterval = useRef(null);

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
    const accessToken = localStorage.getItem('taxicom_access');

    if (!accessToken) {
      console.error('No hay access token disponible, no se puede abrir el WebSocket');
      setWsStatus('Sin token');
      return;
    }

    const wsUrl = `wss://taxicom.onrender.com/ws/colectivos/?token=${encodeURIComponent(accessToken)}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setWsStatus('WebSocket Conectado');

      if (pingInterval.current) clearInterval(pingInterval.current);
      pingInterval.current = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ action: 'ping' }));
        }
      }, 25000);
    };

    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);

      if (data.event === 'pong') return;

      if (data.event === 'chofer_desconectado') {
        removerMarcador(data.chofer_id);
        setChoferes((prev) => prev.filter((c) => c.chofer_id !== data.chofer_id));
        return;
      }

      if (data.event === 'ubicacion_actualizada' || data.lat) {
        const choferId = data.chofer_id || data.id;
        crearOActualizarMarcador(
          choferId,
          data.lat,
          data.lng,
          data.nombre || 'Chofer en Ruta',
          data.vehiculo || 'Vehículo Activo',
          data.sketchfab_id || '',
          data.asientos_disponibles ?? 0
        );

        setChoferes((prev) => {
          const existe = prev.some((c) => c.chofer_id === choferId);
          if (!existe) {
            return [
              ...prev,
              {
                chofer_id: choferId,
                nombre: data.nombre || 'Chofer en Ruta',
                vehiculo: data.vehiculo || 'Vehículo Activo',
                asientos_disponibles: data.asientos_disponibles ?? 0,
                estado: 'En Ruta',
                lat: data.lat,
                lng: data.lng,
              },
            ];
          }
          return prev.map((c) =>
            c.chofer_id === choferId
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
      if (pingInterval.current) clearInterval(pingInterval.current);

      if (e.code !== 4001 && e.code !== 1000) {
        reconnectTimeout.current = setTimeout(conectarWebSocket, 3000);
      } else if (e.code === 4001) {
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

    // Usar la ruta correcta del backend adaptada a MapaChoferesActivosView
    apiFetch('/api/v1/admin/mapa-activos/')
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        const lista = Array.isArray(data) ? data : data.choferes || [];
        setChoferes(lista);
        lista.forEach((c) => {
          const choferId = c.chofer_id || c.id;
          crearOActualizarMarcador(
            choferId,
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

    conectarWebSocket();

    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (pingInterval.current) clearInterval(pingInterval.current);
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
        <span className={`text-xs px-3 py-1 rounded-full font-semibold ${
          wsStatus.includes('Conectado') ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
        }`}>
          {wsStatus}
        </span>
      </header>

      <main className="flex-1 w-full p-4 overflow-hidden">
        <div className="w-full h-full grid grid-cols-12 gap-4">
          <aside className="col-span-3 bg-white rounded-2xl border border-slate-200 p-4 overflow-y-auto">
            <h2 className="font-bold text-lg mb-4">Vehículos Activos ({choferes.length})</h2>
            {choferes.map((c) => {
              const id = c.chofer_id || c.id;
              return (
                <button
                  key={id}
                  onClick={() => seleccionarConductor(c)}
                  className={`w-full text-left p-3 mb-2 rounded-xl border transition-all ${
                    selectedDriver === id ? 'bg-slate-900 text-white' : 'bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="font-semibold text-sm">{c.nombre}</div>
                  <div className="text-xs opacity-70">{c.vehiculo}</div>
                  <div className="text-xs mt-2 font-medium">Asientos libres: {c.asientos_disponibles ?? 0}</div>
                </button>
              );
            })}
          </aside>

          <section className="col-span-9 relative bg-white rounded-2xl border border-slate-200 overflow-hidden min-h-[500px]">
            <div ref={mapRef} className="absolute inset-0 z-0" />
          </section>
        </div>
      </main>
    </div>
  );
}