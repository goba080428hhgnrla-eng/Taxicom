import React, { useEffect, useRef } from 'react';
import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Función para calcular el rumbo/ángulo entre dos coordenadas
const calcularRumbo = (startLat, startLng, endLat, endLng) => {
  const dLng = (endLng - startLng) * (Math.PI / 180);
  const lat1 = startLat * (Math.PI / 180);
  const lat2 = endLat * (Math.PI / 180);

  const y = Math.sin(dLng) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
  let brng = Math.atan2(y, x) * (180 / Math.PI);
  return (brng + 360) % 360;
};

// Generar el ícono SVG dinámico según la modalidad y los asientos libres
const crearIconoVehiculo = (rotacion, modalidad, asientos) => {
  let colorVehiculo = '#EAB308'; // Amarillo por defecto para Taxi Especial
  let etiquetaModalidad = 'ESPECIAL';

  if (modalidad === 'COLECTIVO') {
    etiquetaModalidad = `COLECTIVO (${asientos} libre${asientos !== 1 ? 's' : ''})`;
    // Verde si tiene lugares disponibles, Rojo si va lleno
    colorVehiculo = asientos > 0 ? '#10B981' : '#EF4444';
  }

  return L.divIcon({
    className: 'custom-driver-icon',
    html: `
      <div style="
        transform: rotate(${rotacion}deg);
        transition: transform 0.15s ease-out;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Sombra -->
          <ellipse cx="12" cy="14" rx="7" ry="9" fill="rgba(0,0,0,0.3)"/>
          <!-- Chasis del Auto -->
          <path d="M12 2L6 8V20C6 21.1 6.9 22 8 22H16C17.1 22 18 21.1 18 20V8L12 2Z" fill="${colorVehiculo}" stroke="#FFFFFF" stroke-width="1.5"/>
          <!-- Parabrisas y Ventanas -->
          <path d="M9 9H15L14 13H10L9 9Z" fill="#0F172A"/>
          <!-- Indicador en Techo -->
          <rect x="10" y="11" width="4" height="2" fill="#FFFFFF"/>
        </svg>
      </div>
    `,
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -20],
  });
};

export const SmoothDriverMarker = ({ chofer, duracionAnimacion = 3000 }) => {
  const markerRef = useRef(null);
  const posActualRef = useRef({ lat: chofer.latitud, lng: chofer.longitud, rot: 0 });
  const animFrameRef = useRef(null);

  useEffect(() => {
    const latPrev = posActualRef.current.lat;
    const lngPrev = posActualRef.current.lng;
    const latNueva = chofer.latitud;
    const lngNueva = chofer.longitud;

    if (latPrev === latNueva && lngPrev === lngNueva) return;

    const nuevoRumbo = calcularRumbo(latPrev, lngPrev, latNueva, lngNueva);
    const startTime = performance.now();

    const animar = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duracionAnimacion, 1);
      const easeProgress = 1 - Math.pow(1 - progress, 2); // Quad Ease Out

      const latInterpolada = latPrev + (latNueva - latPrev) * easeProgress;
      const lngInterpolada = lngPrev + (lngNueva - lngPrev) * easeProgress;

      if (markerRef.current) {
        markerRef.current.setLatLng([latInterpolada, lngInterpolada]);
        markerRef.current.setIcon(
          crearIconoVehiculo(nuevoRumbo, chofer.modalidad, chofer.asientos_disponibles)
        );
      }

      posActualRef.current = { lat: latInterpolada, lng: lngInterpolada, rot: nuevoRumbo };

      if (progress < 1) {
        animFrameRef.current = requestAnimationFrame(animar);
      }
    };

    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    animFrameRef.current = requestAnimationFrame(animar);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [chofer.latitud, chofer.longitud, chofer.asientos_disponibles, chofer.modalidad, duracionAnimacion]);

  return (
    <Marker
      ref={markerRef}
      position={[chofer.latitud, chofer.longitud]}
      icon={crearIconoVehiculo(posActualRef.current.rot, chofer.modalidad, chofer.asientos_disponibles)}
    >
      <Popup>
        <div style={{ textAlign: 'center', fontFamily: 'sans-serif' }}>
          <strong style={{ fontSize: '14px' }}>{chofer.nombre}</strong>
          <br />
          <span style={{ fontSize: '12px', color: '#475569' }}>
            {chofer.vehiculo}
          </span>
          <br />
          <div style={{ 
            marginTop: '6px', 
            padding: '2px 8px', 
            borderRadius: '12px', 
            fontSize: '11px', 
            fontWeight: 'bold',
            color: '#FFF',
            backgroundColor: chofer.modalidad === 'ESPECIAL' ? '#D97706' : (chofer.asientos_disponibles > 0 ? '#059669' : '#DC2626')
          }}>
            {chofer.modalidad === 'ESPECIAL' 
              ? 'TAXI ESPECIAL (PRIVADO)' 
              : `COLECTIVO (${chofer.asientos_disponibles} asientos)`}
          </div>
        </div>
      </Popup>
    </Marker>
  );
};