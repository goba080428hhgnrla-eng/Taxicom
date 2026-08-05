import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';

const taxiIcon = L.icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png',
  iconSize: [36, 36],
  iconAnchor: [18, 18],
  popupAnchor: [0, -18]
});

export default function Dashboard() {
  const [choferes, setChoferes] = useState([]);
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markers = useRef({});

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
      if (progress < 1) requestAnimationFrame(animar);
    }
    requestAnimationFrame(animar);
  };

  const crearOActualizarMarcador = (id, lat, lng, nombre, auto, sketchfabId, asientos) => {
    if (!lat || !lng || parseFloat(lat) === 0.0) return;

    const iframe3D = sketchfabId
      ? `<iframe src="https://sketchfab.com/models/${sketchfabId}/embed?autostart=1&internal=1" class="w-full h-40 mt-2 rounded-xl border border-slate-200" frameborder="0"></iframe>`
      : '';

    const popupContent = `
      <div class="text-slate-800 p-1 w-64 font-sans">
        <h3 class="font-bold text-sm text-amber-600">${nombre}</h3>
        <p class="text-xs font-semibold text-slate-600 mt-0.5">Vehículo: ${auto}</p>
        <p class="text-xs text-slate-500">Asientos libres: <b class="text-slate-800">${asientos}</b></p>
        ${iframe3D}
      </div>
    `;

    if (markers.current[id]) {
      moverMarcadorFluidamente(markers.current[id], parseFloat(lat), parseFloat(lng));
      markers.current[id].getPopup().setContent(popupContent);
    } else {
      markers.current[id] = L.marker([lat, lng], { icon: taxiIcon })
        .addTo(mapInstance.current)
        .bindPopup(popupContent);
    }
  };

  useEffect(() => {
    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current).setView([19.4326, -99.1332], 13);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO'
      }).addTo(mapInstance.current);
    }

    fetch('/api/web/choferes-activos/')
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
      });

    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/tracking/`);

    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      crearOActualizarMarcador(
        data.chofer_id,
        data.lat,
        data.lng,
        data.nombre || 'Chofer en Ruta',
        data.vehiculo || 'Vehículo Activo',
        data.sketchfab_id || '',
        data.asientos_disponibles ?? 0
      );
    };

    return () => socket.close();
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 h-[600px] flex flex-col">
        <h2 className="text-base font-bold pb-3 border-b border-slate-100 text-slate-900 flex items-center space-x-2">
          <span>🚕</span> <span>Vehículos en Circulación</span>
        </h2>
        <div className="space-y-3 mt-4 overflow-y-auto flex-1 pr-1">
          {choferes.length > 0 ? (
            choferes.map((c) => (
              <div key={c.chofer_id} className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 hover:border-amber-300 transition">
                <p className="font-semibold text-slate-800 text-sm">{c.nombre}</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  Vehículo: <span className="font-medium text-slate-700">{c.vehiculo}</span>
                </p>
                <div className="mt-3 flex items-center justify-between">
                  <span
                    className={`px-2.5 py-0.5 text-[11px] font-bold rounded-full ${
                      c.estado === 'En Ruta'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {c.estado}
                  </span>
                  <span className="text-xs text-slate-500">
                    Libres: <b className="text-slate-800">{c.asientos_disponibles}</b>
                  </span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-slate-400 text-sm text-center py-8">
              No hay vehículos en circulación actualmente.
            </p>
          )}
        </div>
      </div>

      <div className="lg:col-span-3 bg-white rounded-2xl shadow-sm border border-slate-200 relative h-[600px] overflow-hidden">
        <div ref={mapRef} className="w-full h-full z-0"></div>
      </div>
    </div>
  );
}