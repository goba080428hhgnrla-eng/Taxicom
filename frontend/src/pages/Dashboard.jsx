import React, { useEffect, useState, useRef } from 'react';
import { conectarWebSocket, suscribirWebSocket, obtenerUsuario, apiFetch } from '../api.js';

export default function Dashboard() {
  const [usuario] = useState(obtenerUsuario());
  const [choferes, setChoferes] = useState({});
  const [solicitudes, setSolicitudes] = useState([]);
  const mapRef = useRef(null);
  const leafletMap = useRef(null);
  const markersRef = useRef({});

  // Cargar librerías CDN de Leaflet en caliente
  useEffect(() => {
    if (!document.getElementById('leaflet-css')) {
      const link = document.createElement('link');
      link.id = 'leaflet-css';
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(link);
    }

    if (!window.L) {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.onload = () => initMap();
      document.head.appendChild(script);
    } else {
      initMap();
    }

    function initMap() {
      if (mapRef.current && !leafletMap.current && window.L) {
        leafletMap.current = window.L.map(mapRef.current).setView([19.432608, -99.133209], 13);
        window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors'
        }).addTo(leafletMap.current);
      }
    }
  }, []);

  // Escuchar conexiones WebSocket y actualizar el mapa Leaflet en vivo
  useEffect(() => {
    async function cargarIniciales() {
      try {
        const res = await apiFetch('/api/v1/choferes/activos/');
        if (res.ok) {
          const data = await res.json();
          const mapaData = {};
          data.forEach(c => { if(c.lat && c.lng) mapaData[c.id || c.chofer_id] = c; });
          setChoferes(mapaData);
        }
      } catch (e) {
        console.error(e);
      }
    }

    cargarIniciales();
    conectarWebSocket();

    const desuscribir = suscribirWebSocket((mensaje) => {
      if (mensaje.event === 'ubicacion_actualizada') {
        setChoferes((prev) => ({
          ...prev,
          [mensaje.chofer_id]: {
            chofer_id: mensaje.chofer_id,
            nombre: mensaje.nombre || `Chofer #${mensaje.chofer_id}`,
            lat: parseFloat(mensaje.lat),
            lng: parseFloat(mensaje.lng),
            vehiculo: mensaje.vehiculo || 'Taxi',
            modalidad: mensaje.modalidad || 'COLECTIVO'
          }
        }));
      } else if (mensaje.event === 'nuevo_cliente_colectivo') {
        setSolicitudes((prev) => [mensaje, ...prev]);
      }
    });

    return () => desuscribir();
  }, []);

  // Actualizar los marcadores en el mapa cuando cambie el estado de choferes
  useEffect(() => {
    if (!leafletMap.current || !window.L) return;

    Object.values(choferes).forEach((c) => {
      const { chofer_id, lat, lng, nombre, vehiculo } = c;
      if (!lat || !lng) return;

      if (markersRef.current[chofer_id]) {
        // Mover marcador existente
        markersRef.current[chofer_id].setLatLng([lat, lng]);
      } else {
        // Crear nuevo marcador
        const marker = window.L.marker([lat, lng]).addTo(leafletMap.current);
        marker.bindPopup(`<b>${nombre}</b><br/>${vehiculo}`);
        markersRef.current[chofer_id] = marker;
      }
    });
  }, [choferes]);

  const listaChoferes = Object.values(choferes);

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h2>🚖 Dashboard Taxicom</h2>
      <p>Usuario: <b>{usuario?.username || 'Admin'}</b></p>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '20px', height: '80vh' }}>
        <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '8px', overflowY: 'auto' }}>
          <h3>Choferes Activos ({listaChoferes.length})</h3>
          {listaChoferes.map((c) => (
            <div key={c.chofer_id} style={{ background: '#fff', padding: '10px', marginBottom: '10px', borderRadius: '5px' }}>
              <strong>{c.nombre}</strong><br />
              <small>📍 {c.lat?.toFixed(4)}, {c.lng?.toFixed(4)}</small>
            </div>
          ))}
        </div>

        {/* Contenedor del Mapa */}
        <div ref={mapRef} style={{ width: '100%', height: '100%', borderRadius: '8px' }} />
      </div>
    </div>
  );
}