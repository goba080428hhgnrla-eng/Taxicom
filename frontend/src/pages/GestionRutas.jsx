// src/pages/GestionRutas.jsx
import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { apiFetch } from '../api';

const VILLA_DEL_CARBON = [19.727, -99.508];

const PALETA_COLORES = [
  '#2563eb', // Azul
  '#10b981', // Verde
  '#8b5cf6', // Morado
  '#f97316', // Naranja
  '#ec4899', // Rosa
  '#ef4444', // Rojo
  '#06b6d4', // Cyan
  '#84cc16', // Lima
];

export default function GestionRutas() {
  const [rutas, setRutas] = useState([]);
  const [choferes, setChoferes] = useState([]);
  const [rutaSeleccionada, setRutaSeleccionada] = useState(null);
  const [verTodas, setVerTodas] = useState(true);
  const [nombreNuevaRuta, setNombreNuevaRuta] = useState('');
  const [mapaListo, setMapaListo] = useState(false); // Flag para asegurar que el mapa está montado
  
  // Puntos clave y trazado en edición
  const [puntosClave, setPuntosClave] = useState([]);
  const [trazadoCarretera, setTrazadoCarretera] = useState([]);
  
  const [dibujando, setDibujando] = useState(false);
  const [cargandoRuta, setCargandoRuta] = useState(false);
  const [miUbicacion, setMiUbicacion] = useState(null);
  const [capaSatelite, setCapaSatelite] = useState(false);

  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const tileLayerRef = useRef(null);
  
  const polylinesGroupRef = useRef(L.featureGroup());
  const markersRef = useRef([]);
  const miUbicacionMarkerRef = useRef(null);

  const cargarRutas = () => {
    return apiFetch('/api/v1/admin/rutas/')
      .then((res) => res.json())
      .then((data) => {
        const lista = data.rutas || [];
        setRutas(lista);
        return lista;
      })
      .catch((err) => console.error("Error al cargar rutas:", err));
  };

  const cargarChoferes = () => {
    apiFetch('/api/v1/admin/roles/')
      .then((res) => res.json())
      .then((data) => setChoferes(data.choferes || []))
      .catch((err) => console.error("Error al cargar choferes:", err));
  };

  // 1. Inicializar Mapa Leaflet y Cargar Datos Iniciales
  useEffect(() => {
    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current, {
        zoomControl: false,
        maxZoom: 20
      }).setView(VILLA_DEL_CARBON, 14);

      L.control.zoom({ position: 'bottomright' }).addTo(mapInstance.current);

      tileLayerRef.current = L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        { maxZoom: 20, attribution: '© CARTO / OpenStreetMap' }
      ).addTo(mapInstance.current);

      polylinesGroupRef.current.addTo(mapInstance.current);

      mapInstance.current.on('click', (e) => {
        setDibujando((isDibujando) => {
          if (!isDibujando) return isDibujando;
          const nuevaCoord = [e.latlng.lat, e.latlng.lng];
          setPuntosClave((prev) => [...prev, nuevaCoord]);
          return isDibujando;
        });
      });

      setMapaListo(true);
    }

    if ('geolocation' in navigator) {
      const watchId = navigator.geolocation.watchPosition(
        (pos) => setMiUbicacion([pos.coords.latitude, pos.coords.longitude]),
        (err) => console.warn('Error GPS:', err.message),
        { enableHighAccuracy: true, maximumAge: 5000, timeout: 5000 }
      );
      return () => navigator.geolocation.clearWatch(watchId);
    }

    cargarChoferes();
    cargarRutas();
  }, []);

  // 2. Alternar entre Mapa Normal y Satélite HD
  const alternarCapas = () => {
    if (!mapInstance.current || !tileLayerRef.current) return;
    mapInstance.current.removeLayer(tileLayerRef.current);

    if (!capaSatelite) {
      tileLayerRef.current = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 19, attribution: '© Esri Satellite' }
      );
    } else {
      tileLayerRef.current = L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        { maxZoom: 20, attribution: '© CARTO / OpenStreetMap' }
      );
    }

    tileLayerRef.current.addTo(mapInstance.current);
    setCapaSatelite(!capaSatelite);
  };

  // 3. Motor OSRM para edición
  useEffect(() => {
    if (puntosClave.length < 2) {
      setTrazadoCarretera(puntosClave);
      return;
    }

    setCargandoRuta(true);
    const coordsString = puntosClave.map((pt) => `${pt[1]},${pt[0]}`).join(';');
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

  // 4. RENDERIZADO INMEDIATO Y DIBUJO DE RUTAS EN EL MAPA
  useEffect(() => {
    if (!mapInstance.current || !mapaListo) return;

    polylinesGroupRef.current.clearLayers();
    markersRef.current.forEach((m) => mapInstance.current.removeLayer(m));
    markersRef.current = [];

    // CASO A: MODO DIBUJO
    if (dibujando) {
      if (trazadoCarretera.length > 0) {
        const polyline = L.polyline(trazadoCarretera, {
          color: '#f59e0b',
          weight: 7,
          opacity: 0.9,
          lineCap: 'round',
          lineJoin: 'round',
        });
        polylinesGroupRef.current.addLayer(polyline);
      }

      puntosClave.forEach((punto) => {
        const marker = L.circleMarker(punto, {
          radius: 7,
          color: '#0f172a',
          fillColor: '#fbbf24',
          fillOpacity: 1,
          weight: 3,
        }).addTo(mapInstance.current);
        markersRef.current.push(marker);
      });
      return;
    }

    // CASO B: MOSTRAR TODAS LAS RUTAS DESDE EL INICIO
    if (verTodas) {
      rutas.forEach((ruta, index) => {
        if (ruta.trazado && ruta.trazado.length > 0) {
          const colorRuta = PALETA_COLORES[index % PALETA_COLORES.length];

          const polyline = L.polyline(ruta.trazado, {
            color: colorRuta,
            weight: 5,
            opacity: 0.8,
            lineCap: 'round',
            lineJoin: 'round',
          });

          polyline.bindTooltip(ruta.nombre, { permanent: false, direction: 'center' });

          polyline.on('click', () => {
            setRutaSeleccionada(ruta);
            setVerTodas(false);
          });

          polylinesGroupRef.current.addLayer(polyline);
        }
      });

      // Si hay rutas con trazo, enfocar automáticamente el mapa sobre todas ellas
      if (polylinesGroupRef.current.getBounds().isValid()) {
        mapInstance.current.fitBounds(polylinesGroupRef.current.getBounds(), { padding: [40, 40] });
      }
      return;
    }

    // CASO C: MOSTRAR SÓLO LA RUTA SELECCIONADA
    if (rutaSeleccionada && rutaSeleccionada.trazado?.length > 0) {
      const indexRuta = rutas.findIndex((r) => r.id === rutaSeleccionada.id);
      const colorRuta = PALETA_COLORES[indexRuta % PALETA_COLORES.length] || '#2563eb';

      const polyline = L.polyline(rutaSeleccionada.trazado, {
        color: colorRuta,
        weight: 8,
        opacity: 0.95,
        lineCap: 'round',
        lineJoin: 'round',
      });

      polyline.bindTooltip(rutaSeleccionada.nombre, { permanent: true, direction: 'top' });
      polylinesGroupRef.current.addLayer(polyline);
    }
  }, [rutas, rutaSeleccionada, verTodas, dibujando, trazadoCarretera, puntosClave, mapaListo]);

  // 5. GPS
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

  const seleccionarRutaIndividual = (ruta) => {
    setRutaSeleccionada(ruta);
    setVerTodas(false);
    setDibujando(false);

    if (ruta.trazado?.length > 0 && mapInstance.current) {
      mapInstance.current.fitBounds(ruta.trazado, { padding: [40, 40] });
    }
  };

  const mostrarTodasLasRutas = () => {
    setRutaSeleccionada(null);
    setVerTodas(true);
    setDibujando(false);

    if (polylinesGroupRef.current.getBounds().isValid() && mapInstance.current) {
      mapInstance.current.fitBounds(polylinesGroupRef.current.getBounds(), { padding: [40, 40] });
    } else {
      centrarVilla();
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
      await cargarRutas();
      setRutaSeleccionada(nueva);
      setVerTodas(false);
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
      await cargarRutas();
    }
  };

  return (
    <div className="flex flex-col lg:grid lg:grid-cols-4 gap-4 p-3 md:p-6 max-w-7xl mx-auto font-sans antialiased min-h-screen">
      
      {/* PANEL LATERAL */}
      <div className="order-2 lg:order-1 bg-white p-4 md:p-6 rounded-3xl shadow-sm border border-slate-200 flex flex-col max-h-[500px] lg:max-h-[720px] overflow-y-auto">
        <h2 className="text-base font-bold text-slate-900 mb-3">Rutas - Villa del Carbón</h2>

        {/* Crear Ruta */}
        <form onSubmit={crearRuta} className="flex gap-2 mb-3">
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

        {/* Botón para Ver Todas las Rutas */}
        <button
          onClick={mostrarTodasLasRutas}
          className={`w-full py-2.5 px-3 mb-3 rounded-xl font-bold text-xs border transition flex items-center justify-center gap-2 ${
            verTodas
              ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
              : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
          }`}
        >
          👁️ Ver Todas las Rutas en el Mapa
        </button>

        {/* Lista de Rutas */}
        <div className="space-y-2 overflow-y-auto flex-1 mb-3">
          {rutas.map((r, index) => {
            const colorRuta = PALETA_COLORES[index % PALETA_COLORES.length];
            const estaSeleccionada = !verTodas && rutaSeleccionada?.id === r.id;

            return (
              <div
                key={r.id}
                onClick={() => seleccionarRutaIndividual(r)}
                className={`p-3 rounded-2xl border cursor-pointer transition flex items-center justify-between ${
                  estaSeleccionada
                    ? 'bg-slate-900 text-white border-slate-900 shadow-md'
                    : 'bg-slate-50 border-slate-200 hover:border-amber-300'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className="w-3.5 h-3.5 rounded-full shrink-0 shadow-sm"
                    style={{ backgroundColor: colorRuta }}
                  />
                  <p className="font-bold text-sm">{r.nombre}</p>
                </div>
                <span className="text-[10px] opacity-75">
                  {(r.trazado || []).length > 0 ? `${r.trazado.length} pts` : 'Sin trazo'}
                </span>
              </div>
            );
          })}
        </div>

        {/* Edición de Ruta Seleccionada */}
        {!verTodas && rutaSeleccionada && (
          <div className="pt-3 border-t border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase">Ruta: {rutaSeleccionada.nombre}</span>
              <button
                onClick={() => {
                  if (confirm('¿Eliminar esta ruta?')) {
                    apiFetch(`/api/v1/admin/rutas/${rutaSeleccionada.id}/`, { method: 'DELETE' }).then(() => {
                      setRutaSeleccionada(null);
                      setVerTodas(true);
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
                ✏️ Editar / Redibujar Trazo
              </button>
            ) : (
              <div className="bg-amber-50 border border-amber-300 p-3 rounded-2xl space-y-2">
                <p className="text-xs text-amber-950 font-semibold">
                  {cargandoRuta ? '🔄 Calculando carretera...' : '👉 Toca las calles por donde pasará esta ruta.'}
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
            <span>📍 Dibujando Ruta Activa</span>
            <button
              onClick={() => setDibujando(false)}
              className="bg-slate-800 text-white px-2.5 py-1 rounded-xl text-[10px]"
            >
              Cancelar
            </button>
          </div>
        )}

        {/* BOTONES FLOTANTES */}
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
            {capaSatelite ? '🗺️ Ver Mapa' : '🛰️ Satélite HD'}
          </button>
        </div>

        <div ref={mapRef} className="w-full h-full z-0" />
      </div>

    </div>
  );
}