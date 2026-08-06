import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import { SmoothDriverMarker } from '../components/SmoothDriverMarker';
import 'leaflet/dist/leaflet.css';

export const MapaChoferes = () => {
  const [choferes, setChoferes] = useState({});
  const socketRef = useRef(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/colectivos/`;
    
    socketRef.current = new WebSocket(wsUrl);

    socketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.event === "ubicacion_actualizada") {
        setChoferes((prev) => ({
          ...prev,
          [data.chofer_id]: {
            id: data.chofer_id,
            latitud: data.lat,
            longitud: data.lng,
            nombre: data.nombre,
            vehiculo: data.vehiculo,
            modalidad: data.modalidad,
            asientos_disponibles: data.asientos_disponibles
          }
        }));
      } else if (data.event === "cupo_modificado") {
        setChoferes((prev) => {
          if (!prev[data.chofer_id]) return prev;
          return {
            ...prev,
            [data.chofer_id]: {
              ...prev[data.chofer_id],
              asientos_disponibles: data.asientos_disponibles
            }
          };
        });
      }
    };

    return () => socketRef.current?.close();
  }, []);

  // Función para solicitar un Colectivo
  const pedirColectivo = () => {
    socketRef.current?.send(JSON.stringify({
      action: "solicitar_parada_colectivo",
      cliente_id: 1, // ID del usuario dinámico
      origen_lat: 16.753,
      origen_lng: -93.115,
      destino_lat: 16.758,
      destino_lng: -93.120,
      asientos: 1
    }));
  };

  // Función para solicitar un Taxi Especial
  const pedirEspecial = () => {
    socketRef.current?.send(JSON.stringify({
      action: "solicitar_viaje_especial",
      cliente_id: 1,
      origen_lat: 16.753,
      origen_lng: -93.115
    }));
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
      {/* Overlay de botones para probar las solicitudes */}
      <div style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        zIndex: 1000,
        backgroundColor: '#FFFFFF',
        padding: '12px 16px',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        display: 'flex',
        gap: '10px'
      }}>
        <button 
          onClick={pedirColectivo}
          style={{
            backgroundColor: '#059669',
            color: '#FFF',
            border: 'none',
            padding: '8px 12px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          Pedir Colectivo
        </button>
        <button 
          onClick={pedirEspecial}
          style={{
            backgroundColor: '#D97706',
            color: '#FFF',
            border: 'none',
            padding: '8px 12px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          Pedir Taxi Especial
        </button>
      </div>

      <MapContainer center={[16.75, -93.11]} zoom={14} style={{ height: '100%', width: '100%' }}>
        <TileLayer 
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />
        {Object.values(choferes).map((chofer) => (
          <SmoothDriverMarker key={chofer.id} chofer={chofer} duracionAnimacion={3000} />
        ))}
      </MapContainer>
    </div>
  );
};