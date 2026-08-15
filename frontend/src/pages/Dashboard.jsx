import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { conectarWebSocket, suscribirWebSocket, obtenerUsuario, apiFetch } from '../api.js';

// Corrección de íconos por defecto de Leaflet en React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Ícono personalizado para los Choferes
const taxiIcon = new L.Icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png',
  iconSize: [35, 35],
  iconAnchor: [17, 35],
  popupAnchor: [0, -35],
});

export default function Dashboard() {
  const [usuario] = useState(obtenerUsuario());
  const [choferes, setChoferes] = useState({});
  const [solicitudes, setSolicitudes] = useState([]);
  const [centroMapa] = useState([19.432608, -99.133209]); // Coordenadas por defecto (ej. CDMX)

  useEffect(() => {
    // 1. Cargar estado inicial de choferes vía HTTP (opcional)
    async function cargarChoferesIniciales() {
      try {
        const res = await apiFetch('/api/v1/choferes/activos/');
        if (res.ok) {
          const data = await res.json();
          const mapaChoferes = {};
          data.forEach((c) => {
            if (c.lat && c.lng) {
              mapaChoferes[c.id || c.chofer_id] = c;
            }
          });
          setChoferes(mapaChoferes);
        }
      } catch (err) {
        console.error("Error al cargar choferes iniciales:", err);
      }
    }

    cargarChoferesIniciales();

    // 2. Conectar al WebSocket
    conectarWebSocket();

    // 3. Suscribirse a los eventos entrantes en tiempo real
    const desuscribir = suscribirWebSocket((mensaje) => {
      switch (mensaje.event) {
        case 'ubicacion_actualizada':
          setChoferes((prev) => ({
            ...prev,
            [mensaje.chofer_id]: {
              chofer_id: mensaje.chofer_id,
              nombre: mensaje.nombre || `Chofer #${mensaje.chofer_id}`,
              lat: parseFloat(mensaje.lat),
              lng: parseFloat(mensaje.lng),
              vehiculo: mensaje.vehiculo || 'Taxi',
              modalidad: mensaje.modalidad || 'COLECTIVO',
              asientos: mensaje.asientos_disponibles ?? 'N/A',
            },
          }));
          break;

        case 'nuevo_cliente_colectivo':
        case 'nueva_solicitud_especial':
          setSolicitudes((prev) => [mensaje, ...prev]);
          break;

        default:
          break;
      }
    });

    return () => desuscribir();
  }, []);

  const listaChoferes = Object.values(choferes);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h2>🚖 Dashboard Taxicom</h2>
        <div>
          <span>Usuario: <strong>{usuario?.username || usuario?.nombre || 'Administrador'}</strong></span>
        </div>
      </header>

      {/* Grid de Estado y Mapa */}
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '20px', height: 'calc(100vh - 150px)' }}>
        
        {/* Panel Lateral */}
        <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '8px', overflowY: 'auto', backgroundColor: '#f9f9f9' }}>
          <h3>Unidades Activas ({listaChoferes.length})</h3>
          {listaChoferes.length === 0 ? (
            <p style={{ color: '#666' }}>No hay choferes transmitiendo en vivo.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {listaChoferes.map((c) => (
                <li key={c.chofer_id} style={{ padding: '10px', background: '#fff', marginBottom: '10px', borderRadius: '5px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                  <strong>{c.nombre}</strong><br />
                  <small>🚗 Vehículo: {c.vehiculo}</small><br />
                  <small>📌 Modalidad: {c.modalidad}</small><br />
                  <small>📍 Lat: {c.lat?.toFixed(4)}, Lng: {c.lng?.toFixed(4)}</small>
                </li>
              ))}
            </ul>
          )}

          <hr style={{ margin: '20px 0' }} />

          <h3>Últimas Solicitudes</h3>
          {solicitudes.length === 0 ? (
            <p style={{ color: '#666' }}>Sin solicitudes recientes.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {solicitudes.map((s, idx) => (
                <li key={idx} style={{ padding: '8px', background: '#eef6ff', marginBottom: '8px', borderRadius: '5px' }}>
                  <small><strong>{s.event}</strong></small><br />
                  <small>Cliente: {s.cliente_nombre || s.cliente_id}</small>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Mapa Interactivo */}
        <div style={{ width: '100%', height: '100%', borderRadius: '8px', overflow: 'hidden', border: '1px solid #ccc' }}>
          <MapContainer center={centroMapa} zoom={13} style={{ width: '100%', height: '100%' }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Renderizado de Marcadores de Choferes */}
            {listaChoferes.map((c) => (
              <Marker key={c.chofer_id} position={[c.lat, c.lng]} icon={taxiIcon}>
                <Popup>
                  <div style={{ textAlign: 'center' }}>
                    <strong>{c.nombre}</strong><br />
                    <span>{c.vehiculo}</span><br />
                    <span>Modalidad: <b>{c.modalidad}</b></span><br />
                    <small>Asientos libres: {c.asientos}</small>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>

      </div>
    </div>
  );
}