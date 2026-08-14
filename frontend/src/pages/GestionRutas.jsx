// src/pages/GestionRutas.jsx
import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { apiFetch } from '../api';

const VILLA_DEL_CARBON = [19.727, -99.508];

export default function GestionRutas() {
  const [rutas, setRutas] = useState([]);
  const [choferes, setChoferes] = useState([]);
  const [rutaSeleccionada, setRutaSeleccionada] = useState(null);
  const [nombreNuevaRuta, setNombreNuevaRuta] = useState('');
  
  // Puntos clave / paradas del trazado
  const [puntosClave, setPuntosClave] = useState([]);
  // Trazado de alta precisión
  const [trazadoCarretera, setTrazadoCarretera] = useState([]);
  
  const [dibujando, setDibujando] = useState(false);
  const [cargandoRuta, setCargandoRuta] = useState(false);
  const [miUbicacion, setMiUbicacion] = useState(null);
  const [capaSatelite, setCapaSatelite] = useState(false);

  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const tileLayerRef = useRef(null);
  const polylineRef = useRef(null);
  const markersRef = useRef([]);
  const miUbicacionMarkerRef = useRef(null);

  const cargarRutas = () => {
    apiFetch('/api/v1/admin/rutas/')
      .then((res) => res.json())
      .then((data) => setRutas(data.rutas || []))
      .catch((err) => console.error("Error al cargar rutas:", err));
  };

  const cargarChoferes = () => {
    apiFetch('/api/v1/admin/roles/')
      .then((res) => res.json())
      .then((data) => setChoferes(data.choferes || []))
      .catch((err) => console.error("Error al cargar choferes:", err));
  };

  // 1. Inicialización del Mapa con Capas Conmutables
  useEffect(() => {
    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current, {
        zoomControl: false,
        maxZoom: 20
      }).setView(VILLA_DEL_CARBON, 15);

      L.control.zoom({ position: 'bottomright' }).addTo(mapInstance.current);

      // Capa base por defecto (Voyager de CARTO para máxima claridad urbana)
      tileLayerRef.current = L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        { maxZoom: 20, attribution: '© CARTO / OpenStreetMap' }
      ).addTo(mapInstance.current);

      // Click para agregar coordenadas exactas
      mapInstance.current.on('click', (e) => {
        setDibujando((isDibujando) => {
          if (!isDibujando) return isDibujando;
          const nuevaCoord = [e.latlng.lat, e.latlng.lng];
          setPuntosClave((prev) => [...prev, nuevaCoord]);
          return isDibujando;
        });
      });
    }

    if ('geolocation' in navigator) {
      const watchId = navigator.geolocation.watchPosition(
        (pos) => setMiUbicacion([pos.coords.latitude, pos.coords.longitude]),
        (err) => console.warn('Error GPS:', err.message),
        { enableHighAccuracy: true, maximumAge: 5000, timeout: 5000 }
      );
      return () => navigator.geolocation.clearWatch(watchId);
    }

    cargarRutas();
    cargarChoferes();
  }, []);

  // Cambiar entre vista vectorial y vista de Satélite HD
  const alternarCapas = () => {
    if (!mapInstance.current || !tileLayerRef.current) return;

    mapInstance.current.removeLayer(tileLayerRef.current);

    if (!capaSatelite) {
      // Satélite Esri World Imagery (Imágenes de alta resolución para zonas rurales)
      tileLayerRef.current = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 19, attribution: '© Esri Satellite' }
      );
    } else {
      // Mapa Vectorial CARTO
      tileLayerRef.current = L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        { maxZoom: 20, attribution: '© CARTO / OpenStreetMap' }
      );
    }

    tileLayerRef.current.addTo(mapInstance.current);
    setCapaSatelite(!capaSatelite);
  };

  // 2. Motor de Trazado de Alta Precisión (OSRM con Geometría Completa)
  useEffect(() => {
    if (puntosClave.length < 2) {
      setTrazadoCarretera(puntosClave);
      return;
    }

    setCargandoRuta(true);
    const coordsString = puntosClave.map((pt) => `${pt[1]},${pt[0]}`).join(';');
    // geometries=geojson&overview=full fuerza máxima definición vectorial en cada curva
    const url = `https://router.project-osrm.org/route/v1/driving/${coordsString}?overview=full&geometries=geojson&continue_straight=true`;

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        if (data.routes && data.routes.length > 0) {
          const routeCoords = data.routes[0].geometry.coordinates.map((c) => [c[1], c[0]]);
          setTrazadoCarretera(routeCoords);
        } else {
          setTrazadoCarretera(puntosClave);
        }
      })
      .catch(() => setTrazadoCarretera(puntosClave))
      .finally(() => setCargandoRuta(false));
  }, [puntosClave]);

  // 3. Renderizado HD de Trazado e Indicadores
  useEffect(() => {
    if (!mapInstance.current) return;

    if (polylineRef.current) {
      mapInstance.current.removeLayer(polylineRef.current);
      polylineRef.current = null;
    }
    markersRef.current.forEach((m) => mapInstance.current.removeLayer(m));
    markersRef.current = [];

    if (trazadoCarretera.length > 0) {
      polylineRef.current = L.polyline(trazadoCarretera, {
        color: '#f59e0b',
        weight: 6,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round',
      }).addTo(mapInstance.current);
    }

    // Dibujar cada nodo/hito tocado por el admin
    puntosClave.forEach((punto, index) => {
      const marker = L.circleMarker(punto, {
        radius: 7,
        color: '#0f172a',
        fillColor: '#fbbf24',
        fillOpacity: 1,
        weight: 3,
      }).addTo(mapInstance.current);
      markersRef.current.push(marker);
    });
  }, [trazadoCarretera, puntosClave]);

  // 4. Marcador GPS Móvil
  useEffect(() => {
    if (!mapInstance.current || !miUbicacion) return;

    if (miUbicacionMarkerRef.current) {
      miUbicacionMarkerRef.current.setLatLng(miUbicacion);
    } else {
      const miIcono = L.divIcon({
        className: 'mi-ubicacion-icon',
        html: `<div style="background-color: #2563eb; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 12px rgba(37,99,235,0.8);"></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      });

      miUbicacionMarkerRef.current = L.marker(miUbicacion, { icon: miIcono })
        .addTo(mapInstance.current)
        .bindTooltip('Tu Ubicación');
    }
  }, [miUbicacion]);

  // Acciones rápidas
  const centrarMiUbicacion = () => {
    if (miUbicacion && mapInstance.current) {
      mapInstance.current.flyTo(miUbicacion, 17);
    } else {
      alert('Localizando señal GPS...');
    }
  };

  const centrarVilla = () => {
    if (mapInstance.current) {
      mapInstance.current.flyTo(VILLA_DEL_CARBON, 15);
    }
  };

  const seleccionarRuta = (ruta) => {
    setRutaSeleccionada(ruta);
    setTrazadoCarretera(ruta.trazado || []);
    setPuntosClave([]);
    setDibujando(false);

    if (ruta.trazado?.length > 0 && mapInstance.current) {
      mapInstance.current.fitBounds(ruta.trazado, { padding: [30, 30] });
    }
  };

  const crearRuta = async (e) => {
    e.preventDefault();
    if (!nombreNuevaRuta.trim()) return;

    const res = await apiFetch('/api/v1/admin/rutas/', {
      method: 'POST',
      body: JSON.stringify({ nombre: nombreNuevaRuta, trazado: [] }),
    });

    if (res.ok) {
      const nueva = await res.json();
      setNombreNuevaRuta('');
      cargarRutas();
      setRutaSeleccionada(nueva);
      setPuntosClave([]);
      setTrazadoCarretera([]);
      setDibujando(true);
    }
  };

  const guardarTrazo = async () => {
    if (!rutaSeleccionada) return;
    const res = await apiFetch(`/api/v1/admin/rutas/${rutaSeleccionada.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ trazado: trazadoCarretera }),
    });
    if (res.ok) {
      setDibujando(false);
      setPuntosClave([]);
      cargarRutas();
    }
  };

  return (
    <div className="flex flex-col lg:grid lg:grid-cols-4 gap-4 p-3 md:p-6 max-w-7xl mx-auto font-sans antialiased min-h-screen">
      
      {/* PANEL LATERAL / INFERIOR */}
      <div className="order-2 lg:order-1 bg-white p-4 md:p-6 rounded-3xl shadow-sm border border-slate-200 flex flex-col max-h-[500px] lg:max-h-[720px] overflow-y-auto">
        <h2 className="text-base font-bold text-slate-900 mb-3">Rutas - Villa del Carbón</h2>

        <form onSubmit={crearRuta} className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="Nombre de la ruta"
            value={nombreNuevaRuta}
            onChange={(e) => setNombreNuevaRuta(e.target.value)}
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
          <button type="submit" className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-sm px-4 rounded-xl shrink-0">
            +
          </button>
        </form>

        <div className="space-y-2 overflow-y-auto flex-1 mb-4">
          {rutas.map((r) => (
            <div
              key={r.id}
              onClick={() => seleccionarRuta(r)}
              className={`p-3 rounded-2xl border cursor-pointer transition ${
                rutaSeleccionada?.id === r.id
                  ? 'bg-slate-900 text-white border-slate-900 shadow-md'
                  : 'bg-slate-50 border-slate-200 hover:border-amber-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="font-bold text-sm">{r.nombre}</p>
                <span className="text-[10px] bg-amber-500 text-slate-950 font-extrabold px-2 py-0.5 rounded-full">
                  {(r.trazado || []).length > 0 ? `${r.trazado.length} pts` : 'Sin trazo'}
                </span>
              </div>
            </div>
          ))}
        </div>

        {rutaSeleccionada && (
          <div className="pt-3 border-t border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase">Ruta: {rutaSeleccionada.nombre}</span>
              <button
                onClick={() => {
                  if (confirm('¿Eliminar esta ruta?')) {
                    apiFetch(`/api/v1/admin/rutas/${rutaSeleccionada.id}/`, { method: 'DELETE' }).then(() => {
                      setRutaSeleccionada(null);
                      cargarRutas();
                    });
                  }
                }}
                className="text-xs text-red-500 font-semibold"
              >
                Eliminar
              </button>
            </div>

            {!dibujando ? (
              <button
                onClick={() => {
                  setDibujando(true);
                  setPuntosClave([]);
                }}
                className="w-full bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-extrabold py-3 rounded-2xl shadow-sm transition"
              >
                ✏️ Trazar / Editar en Mapa
              </button>
            ) : (
              <div className="bg-amber-50 border border-amber-300 p-3 rounded-2xl space-y-2">
                <p className="text-xs text-amber-950 font-semibold">
                  {cargandoRuta ? '🔄 Calculando trayecto HD...' : '👉 Toca las curvas o vialidades por donde pasa la ruta.'}
                </p>
                <div className="grid grid-cols-3 gap-1.5">
                  <button
                    onClick={() => setPuntosClave((prev) => prev.slice(0, -1))}
                    className="bg-white border border-slate-200 text-slate-800 text-xs font-bold py-2 rounded-xl"
                  >
                    Deshacer
                  </button>
                  <button
                    onClick={() => setPuntosClave([])}
                    className="bg-white border border-slate-200 text-slate-800 text-xs font-bold py-2 rounded-xl"
                  >
                    Limpiar
                  </button>
                  <button
                    onClick={guardarTrazo}
                    className="bg-emerald-600 text-white text-xs font-bold py-2 rounded-xl shadow-sm"
                  >
                    Guardar
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* CONTENEDOR DEL MAPA */}
      <div className="order-1 lg:order-2 lg:col-span-3 bg-white rounded-3xl shadow-sm border border-slate-200 relative h-[480px] md:h-[620px] lg:h-[720px] overflow-hidden">
        
        {dibujando && (
          <div className="absolute top-3 left-3 right-3 z-[1000] bg-slate-900/90 text-amber-400 backdrop-blur-md px-4 py-2.5 rounded-2xl text-xs font-bold text-center shadow-lg flex items-center justify-between">
            <span>📍 Trazando Ruta en Vivo</span>
            <button
              onClick={() => setDibujando(false)}
              className="bg-slate-800 text-white px-2.5 py-1 rounded-xl text-[10px]"
            >
              Cancelar
            </button>
          </div>
        )}

        {/* BOTONES FLOTANTES DE MAPA Y NAVEGACIÓN */}
        <div className="absolute bottom-4 left-4 z-[1000] flex flex-wrap gap-2">
          <button
            onClick={centrarMiUbicacion}
            className="bg-white text-slate-900 font-bold text-xs px-3.5 py-2.5 rounded-2xl shadow-lg border border-slate-200 hover:bg-slate-50 flex items-center gap-1.5 active:scale-95 transition"
          >
            🎯 Mi Ubicación
          </button>

          <button
            onClick={centrarVilla}
            className="bg-slate-900 text-white font-bold text-xs px-3.5 py-2.5 rounded-2xl shadow-lg border border-slate-800 flex items-center gap-1.5 active:scale-95 transition"
          >
            ⛰️ Villa del Carbón
          </button>

          <button
            onClick={alternarCapas}
            className="bg-amber-500 text-slate-950 font-extrabold text-xs px-3.5 py-2.5 rounded-2xl shadow-lg hover:bg-amber-400 flex items-center gap-1.5 active:scale-95 transition"
          >
            {capaSatelite ? '🗺️ Ver Mapa' : '🛰️ Ver Satélite HD'}
          </button>
        </div>

        <div ref={mapRef} className="w-full h-full z-0" />
      </div>

    </div>
  );
}