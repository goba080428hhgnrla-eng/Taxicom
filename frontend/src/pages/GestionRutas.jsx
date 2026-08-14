// src/pages/GestionRutas.jsx
import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { apiFetch } from '../api';

// Coordenadas de Villa del Carbón
const VILLA_DEL_CARBON = [19.727, -99.508];

export default function GestionRutas() {
  const [rutas, setRutas] = useState([]);
  const [choferes, setChoferes] = useState([]);
  const [rutaSeleccionada, setRutaSeleccionada] = useState(null);
  const [nombreNuevaRuta, setNombreNuevaRuta] = useState('');
  
  // Puntos clave seleccionados por el Administrador (Waypoints)
  const [puntosClave, setPuntosClave] = useState([]);
  // Trazado detallado generado por el motor de carreteras (OSRM)
  const [trazadoCarretera, setTrazadoCarretera] = useState([]);
  
  const [dibujando, setDibujando] = useState(false);
  const [cargandoRuta, setCargandoRuta] = useState(false);
  const [miUbicacion, setMiUbicacion] = useState(null);

  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const polylineRef = useRef(null);
  const markersRef = useRef([]);
  const miUbicacionMarkerRef = useRef(null);

  const cargarRutas = () => {
    apiFetch('/api/v1/admin/rutas/')
      .then((res) => res.json())
      .then((data) => setRutas(data.rutas || []));
  };

  const cargarChoferes = () => {
    apiFetch('/api/v1/admin/roles/')
      .then((res) => res.json())
      .then((data) => setChoferes(data.choferes || []));
  };

  // 1. Inicializar Mapa en Villa del Carbón y rastreo GPS
  useEffect(() => {
    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current).setView(VILLA_DEL_CARBON, 14);

      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap © CARTO',
        maxZoom: 19,
      }).addTo(mapInstance.current);

      // Evento de clic en el mapa para ir agregando puntos
      mapInstance.current.on('click', (e) => {
        setDibujando((isDibujando) => {
          if (!isDibujando) return isDibujando;
          const nuevaCoord = [e.latlng.lat, e.latlng.lng];
          setPuntosClave((prev) => [...prev, nuevaCoord]);
          return isDibujando;
        });
      });
    }

    // Geolocalización del dispositivo
    if ('geolocation' in navigator) {
      const watchId = navigator.geolocation.watchPosition(
        (pos) => setMiUbicacion([pos.coords.latitude, pos.coords.longitude]),
        (err) => console.warn('Error GPS:', err.message),
        { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
      );
      return () => navigator.geolocation.clearWatch(watchId);
    }

    cargarRutas();
    cargarChoferes();
  }, []);

  // 2. Calcular ruta sobre carreteras con OSRM cuando cambian los puntos clave
  useEffect(() => {
    if (puntosClave.length < 2) {
      setTrazadoCarretera(puntosClave);
      return;
    }

    setCargandoRuta(true);
    // Convertir de [lat, lng] a "lng,lat" para OSRM
    const coordsString = puntosClave.map((pt) => `${pt[1]},${pt[0]}`).join(';');
    const url = `https://router.project-osrm.org/route/v1/driving/${coordsString}?overview=full&geometries=geojson`;

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        if (data.routes && data.routes.length > 0) {
          // Extraer las coordenadas y pasarlas a [lat, lng]
          const routeCoords = data.routes[0].geometry.coordinates.map((c) => [c[1], c[0]]);
          setTrazadoCarretera(routeCoords);
        } else {
          setTrazadoCarretera(puntosClave);
        }
      })
      .catch((err) => {
        console.error('Error calculando ruta por carreteras:', err);
        setTrazadoCarretera(puntosClave);
      })
      .finally(() => setCargandoRuta(false));
  }, [puntosClave]);

  // 3. Renderizar el trazado y marcadores de puntos clave en el mapa
  useEffect(() => {
    if (!mapInstance.current) return;

    // Limpiar capa previa
    if (polylineRef.current) {
      mapInstance.current.removeLayer(polylineRef.current);
      polylineRef.current = null;
    }
    markersRef.current.forEach((m) => mapInstance.current.removeLayer(m));
    markersRef.current = [];

    // Pintar la línea ajustada a calles/carreteras
    if (trazadoCarretera.length > 0) {
      polylineRef.current = L.polyline(trazadoCarretera, {
        color: '#d97706',
        weight: 6,
        opacity: 0.85,
        lineJoin: 'round',
      }).addTo(mapInstance.current);
    }

    // Pintar los marcadores de los clics (puntos clave)
    puntosClave.forEach((punto, index) => {
      const marker = L.circleMarker(punto, {
        radius: 7,
        color: '#0f172a',
        fillColor: '#fbbf24',
        fillOpacity: 1,
        weight: 2,
      })
        .addTo(mapInstance.current)
        .bindTooltip(`Punto ${index + 1}`, { permanent: false });
      markersRef.current.push(marker);
    });
  }, [trazadoCarretera, puntosClave]);

  // 4. Marcador para la ubicación actual del dispositivo
  useEffect(() => {
    if (!mapInstance.current || !miUbicacion) return;

    if (miUbicacionMarkerRef.current) {
      miUbicacionMarkerRef.current.setLatLng(miUbicacion);
    } else {
      const miIcono = L.divIcon({
        className: 'mi-ubicacion-icon',
        html: `<div style="background-color: #2563eb; width: 14px; height: 14px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 8px rgba(0,0,0,0.4);"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      miUbicacionMarkerRef.current = L.marker(miUbicacion, { icon: miIcono })
        .addTo(mapInstance.current)
        .bindTooltip('Tu Ubicación');
    }
  }, [miUbicacion]);

  // Funciones de Control
  const centrarEnVillaDelCarbon = () => {
    if (mapInstance.current) {
      mapInstance.current.flyTo(VILLA_DEL_CARBON, 14);
    }
  };

  const seleccionarRuta = (ruta) => {
    setRutaSeleccionada(ruta);
    setTrazadoCarretera(ruta.trazado || []);
    setPuntosClave([]); // Se reinician puntos temporales de edición
    setDibujando(false);

    if (ruta.trazado?.length > 0 && mapInstance.current) {
      mapInstance.current.fitBounds(ruta.trazado, { padding: [40, 40] });
    }
  };

  const crearRuta = async (e) => {
    e.preventDefault();
    if (!nombreNuevaRuta.trim()) return;

    const res = await apiFetch('/api/v1/admin/rutas/', {
      method: 'POST',
      body: JSON.stringify({ nombre: nombreNuevaRuta, trazado: [] }),
    });
    const nueva = await res.json();
    setNombreNuevaRuta('');
    cargarRutas();
    
    // Activar modo dibujo para la nueva ruta creada
    setRutaSeleccionada(nueva);
    setPuntosClave([]);
    setTrazadoCarretera([]);
    setDibujando(true);
  };

  const guardarTrazo = async () => {
    if (!rutaSeleccionada) return;
    await apiFetch(`/api/v1/admin/rutas/${rutaSeleccionada.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ trazado: trazadoCarretera }),
    });
    setDibujando(false);
    setPuntosClave([]);
    cargarRutas();
  };

  const deshacerPunto = () => {
    setPuntosClave((prev) => prev.slice(0, -1));
  };

  const limpiarTrazo = () => {
    setPuntosClave([]);
    setTrazadoCarretera([]);
  };

  const eliminarRuta = async (rutaId) => {
    if (!confirm('¿Deseas eliminar esta ruta?')) return;
    await apiFetch(`/api/v1/admin/rutas/${rutaId}/`, { method: 'DELETE' });
    if (rutaSeleccionada?.id === rutaId) {
      setRutaSeleccionada(null);
      setPuntosClave([]);
      setTrazadoCarretera([]);
    }
    cargarRutas();
  };

  const agregarChofer = async (choferId) => {
    if (!rutaSeleccionada || !choferId) return;
    const res = await apiFetch(`/api/v1/admin/rutas/${rutaSeleccionada.id}/agregar-chofer/`, {
      method: 'POST',
      body: JSON.stringify({ chofer_id: choferId }),
    });
    const actualizada = await res.json();
    setRutaSeleccionada(actualizada);
    cargarRutas();
  };

  const quitarChofer = async (choferId) => {
    if (!rutaSeleccionada) return;
    const res = await apiFetch(`/api/v1/admin/rutas/${rutaSeleccionada.id}/quitar-chofer/`, {
      method: 'POST',
      body: JSON.stringify({ chofer_id: choferId }),
    });
    const actualizada = await res.json();
    setRutaSeleccionada(actualizada);
    cargarRutas();
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 p-6 max-w-7xl mx-auto font-sans antialiased">
      {/* Panel Izquierdo de Gestión */}
      <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 h-[680px] flex flex-col">
        <h2 className="text-lg font-bold text-slate-900 mb-4">Rutas en Villa del Carbón</h2>

        {/* Crear Nueva Ruta */}
        <form onSubmit={crearRuta} className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="Ej. Ruta Centro - San Martín"
            value={nombreNuevaRuta}
            onChange={(e) => setNombreNuevaRuta(e.target.value)}
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
          <button type="submit" className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-sm px-4 rounded-xl transition">
            +
          </button>
        </form>

        {/* Lista de Rutas */}
        <div className="space-y-2 overflow-y-auto flex-1 pr-1">
          {rutas.map((r) => (
            <div
              key={r.id}
              onClick={() => seleccionarRuta(r)}
              className={`p-3.5 rounded-2xl border cursor-pointer transition ${
                rutaSeleccionada?.id === r.id
                  ? 'bg-slate-900 text-white border-slate-900 shadow-md'
                  : 'bg-slate-50 border-slate-200 hover:border-amber-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="font-bold text-sm">{r.nombre}</p>
                <button
                  onClick={(e) => { e.stopPropagation(); eliminarRuta(r.id); }}
                  className="text-xs text-red-400 hover:text-red-500 p-1"
                >
                  ✕
                </button>
              </div>
              <p className="text-xs opacity-75 mt-1">
                {r.choferes_asignados?.length || 0} chofer(es) asignados
              </p>
              <p className="text-[11px] opacity-50">{(r.trazado || []).length} puntos en carretera</p>
            </div>
          ))}
        </div>

        {/* Detalles y Controles de Edición de la Ruta Seleccionada */}
        {rutaSeleccionada && (
          <div className="pt-4 mt-4 border-t border-slate-100 space-y-3">
            <div>
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Choferes Asignados ({rutaSeleccionada.choferes_asignados?.length || 0})
              </label>
              <div className="space-y-1.5 mt-1.5 max-h-24 overflow-y-auto">
                {(rutaSeleccionada.choferes_asignados || []).map((c) => (
                  <div key={c.id} className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5">
                    <span className="text-xs font-semibold text-slate-800">{c.nombre}</span>
                    <button
                      onClick={() => quitarChofer(c.id)}
                      className="text-xs text-red-500 hover:text-red-700"
                    >
                      Quitar
                    </button>
                  </div>
                ))}
              </div>

              <select
                value=""
                onChange={(e) => e.target.value && agregarChofer(Number(e.target.value))}
                className="w-full mt-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs"
              >
                <option value="">+ Asignar Chofer</option>
                {choferes
                  .filter((c) => !(rutaSeleccionada.choferes_asignados || []).some((a) => a.id === c.id))
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.perfil.nombre} {c.perfil.apellido}
                    </option>
                  ))}
              </select>
            </div>

            {/* Panel dinámico para Dibujar / Modificar Trazado */}
            {!dibujando ? (
              <button
                onClick={() => {
                  setDibujando(true);
                  setPuntosClave([]);
                }}
                className="w-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold py-2.5 rounded-xl transition"
              >
                ✏️ Dibujar / Modificar Trazado
              </button>
            ) : (
              <div className="bg-amber-50 border border-amber-200 p-3 rounded-2xl space-y-2">
                <p className="text-xs text-amber-900 font-medium">
                  {cargandoRuta
                    ? 'Calculando ruta por carreteras...'
                    : 'Haz clic en las carreteras del mapa por donde pasará el colectivo.'}
                </p>
                <div className="flex gap-1.5">
                  <button
                    onClick={deshacerPunto}
                    className="flex-1 bg-white border border-slate-200 text-slate-700 text-xs font-semibold py-1.5 rounded-lg hover:bg-slate-50"
                  >
                    Deshacer
                  </button>
                  <button
                    onClick={limpiarTrazo}
                    className="flex-1 bg-white border border-slate-200 text-slate-700 text-xs font-semibold py-1.5 rounded-lg hover:bg-slate-50"
                  >
                    Limpiar
                  </button>
                  <button
                    onClick={guardarTrazo}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold py-1.5 rounded-lg"
                  >
                    Guardar
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Contenedor del Mapa */}
      <div className="lg:col-span-3 bg-white rounded-3xl shadow-sm border border-slate-200 relative h-[680px] overflow-hidden">
        <div className="absolute top-4 right-4 z-[1000] flex gap-2">
          <button
            onClick={centrarEnVillaDelCarbon}
            className="bg-white text-slate-800 font-bold text-xs px-3 py-2 rounded-xl shadow-md border border-slate-200 hover:bg-slate-50 flex items-center gap-1.5"
          >
            ⛰️ Villa del Carbón
          </button>
        </div>
        <div ref={mapRef} className="w-full h-full z-0" />
      </div>
    </div>
  );
}