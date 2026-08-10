// Sugerido: src/pages/GestionRutas.jsx
// El admin dibuja el trazo de la ruta clickeando puntos en el mapa (sin
// paradas con nombre), guarda, y asigna un chofer de la lista.
import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { apiFetch } from '../api';

export default function GestionRutas() {
  const [rutas, setRutas] = useState([]);
  const [choferes, setChoferes] = useState([]);
  const [rutaSeleccionada, setRutaSeleccionada] = useState(null);
  const [nombreNuevaRuta, setNombreNuevaRuta] = useState('');
  const [trazoEnEdicion, setTrazoEnEdicion] = useState([]);
  const [dibujando, setDibujando] = useState(false);

  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const polylineRef = useRef(null);
  const puntosMarkersRef = useRef([]);

  const cargarRutas = () => {
    apiFetch('/api/v1/admin/rutas/')
      .then((res) => res.json())
      .then((data) => setRutas(data.rutas || []));
  };

  const cargarChoferes = () => {
    // Reutiliza el endpoint de roles, que ya trae la lista de choferes.
    apiFetch('/api/v1/admin/roles/')
      .then((res) => res.json())
      .then((data) => setChoferes(data.choferes || []));
  };

  useEffect(() => {
    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current).setView([16.753, -93.115], 13);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap © CARTO',
      }).addTo(mapInstance.current);

      mapInstance.current.on('click', (e) => {
        setDibujando((actual) => {
          if (!actual) return actual; // ignora clicks si no esta en modo dibujo
          setTrazoEnEdicion((prev) => [...prev, [e.latlng.lat, e.latlng.lng]]);
          return actual;
        });
      });
    }

    cargarRutas();
    cargarChoferes();
  }, []);

  // Repinta la linea + puntos cada vez que cambia el trazo en edicion
  useEffect(() => {
    if (!mapInstance.current) return;

    if (polylineRef.current) {
      mapInstance.current.removeLayer(polylineRef.current);
      polylineRef.current = null;
    }
    puntosMarkersRef.current.forEach((m) => mapInstance.current.removeLayer(m));
    puntosMarkersRef.current = [];

    if (trazoEnEdicion.length > 0) {
      polylineRef.current = L.polyline(trazoEnEdicion, { color: '#f59e0b', weight: 4 }).addTo(mapInstance.current);
      trazoEnEdicion.forEach((punto, i) => {
        const marker = L.circleMarker(punto, { radius: 5, color: '#0f172a', fillColor: '#f59e0b', fillOpacity: 1 })
          .addTo(mapInstance.current)
          .bindTooltip(`${i + 1}`);
        puntosMarkersRef.current.push(marker);
      });
    }
  }, [trazoEnEdicion]);

  const seleccionarRuta = (ruta) => {
    setRutaSeleccionada(ruta);
    setTrazoEnEdicion(ruta.trazado || []);
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
    seleccionarRuta(nueva);
    setDibujando(true);
    setTrazoEnEdicion([]);
  };

  const guardarTrazo = async () => {
    if (!rutaSeleccionada) return;
    await apiFetch(`/api/v1/admin/rutas/${rutaSeleccionada.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ trazado: trazoEnEdicion }),
    });
    setDibujando(false);
    cargarRutas();
  };

  const borrarUltimoPunto = () => {
    setTrazoEnEdicion((prev) => prev.slice(0, -1));
  };

  const eliminarRuta = async (rutaId) => {
    if (!confirm('¿Eliminar esta ruta?')) return;
    await apiFetch(`/api/v1/admin/rutas/${rutaId}/`, { method: 'DELETE' });
    if (rutaSeleccionada?.id === rutaId) {
      setRutaSeleccionada(null);
      setTrazoEnEdicion([]);
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
      <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 h-[650px] flex flex-col">
        <h2 className="text-base font-bold text-slate-900 mb-4">Rutas de Colectivos</h2>

        <form onSubmit={crearRuta} className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="Nombre de la ruta"
            value={nombreNuevaRuta}
            onChange={(e) => setNombreNuevaRuta(e.target.value)}
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm"
          />
          <button type="submit" className="bg-amber-500 text-slate-950 font-bold text-sm px-4 rounded-xl">
            +
          </button>
        </form>

        <div className="space-y-2 overflow-y-auto flex-1">
          {rutas.map((r) => (
            <div
              key={r.id}
              onClick={() => seleccionarRuta(r)}
              className={`p-3 rounded-2xl border cursor-pointer transition ${
                rutaSeleccionada?.id === r.id
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-slate-50 border-slate-200 hover:border-amber-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="font-bold text-sm">{r.nombre}</p>
                <button
                  onClick={(e) => { e.stopPropagation(); eliminarRuta(r.id); }}
                  className="text-xs text-red-400 hover:text-red-600"
                >
                  ✕
                </button>
              </div>
              <p className="text-xs opacity-70 mt-1">
                {r.choferes_asignados?.length > 0
                  ? `${r.choferes_asignados.length} chofer(es) trabajando`
                  : 'Sin choferes asignados'}
              </p>
              <p className="text-xs opacity-50">{(r.trazado || []).length} puntos en el trazo</p>
            </div>
          ))}
          {rutas.length === 0 && (
            <p className="text-sm text-slate-400 text-center py-8">Crea tu primera ruta arriba.</p>
          )}
        </div>

        {rutaSeleccionada && (
          <div className="pt-4 mt-4 border-t border-slate-100 space-y-3">
            <div>
              <label className="text-xs font-bold text-slate-500 uppercase">
                Choferes trabajando esta ruta ({rutaSeleccionada.choferes_asignados?.length || 0})
              </label>
              <div className="space-y-1.5 mt-2 max-h-32 overflow-y-auto">
                {(rutaSeleccionada.choferes_asignados || []).map((c) => (
                  <div key={c.id} className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-xl px-3 py-2">
                    <div>
                      <p className="text-xs font-semibold text-slate-800">{c.nombre}</p>
                      <p className="text-[11px] text-slate-500">
                        {c.estado_display} · {c.asientos_disponibles} asientos libres{c.tiene_cajuela ? ' · cajuela' : ''}
                      </p>
                    </div>
                    <button
                      onClick={() => quitarChofer(c.id)}
                      className="text-xs text-red-400 hover:text-red-600 shrink-0 ml-2"
                    >
                      Quitar
                    </button>
                  </div>
                ))}
                {(rutaSeleccionada.choferes_asignados || []).length === 0 && (
                  <p className="text-xs text-slate-400 py-2">Ningún chofer trabajando esta ruta todavía.</p>
                )}
              </div>

              <select
                value=""
                onChange={(e) => e.target.value && agregarChofer(Number(e.target.value))}
                className="w-full mt-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm"
              >
                <option value="">+ Agregar chofer a esta ruta</option>
                {choferes
                  .filter((c) => !(rutaSeleccionada.choferes_asignados || []).some((a) => a.id === c.id))
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.perfil.nombre} {c.perfil.apellido} ({c.estado_display})
                    </option>
                  ))}
              </select>
            </div>

            {!dibujando ? (
              <button
                onClick={() => setDibujando(true)}
                className="w-full bg-slate-900 text-white text-sm font-semibold py-2.5 rounded-xl"
              >
                Editar trazo en el mapa
              </button>
            ) : (
              <div className="space-y-2">
                <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl p-2">
                  Haz click en el mapa para agregar puntos al trazo, en orden.
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={borrarUltimoPunto}
                    className="flex-1 bg-slate-100 text-slate-700 text-xs font-semibold py-2 rounded-xl"
                  >
                    Quitar último punto
                  </button>
                  <button
                    onClick={guardarTrazo}
                    className="flex-1 bg-emerald-600 text-white text-xs font-semibold py-2 rounded-xl"
                  >
                    Guardar trazo
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="lg:col-span-3 bg-white rounded-3xl shadow-sm border border-slate-200 relative h-[650px] overflow-hidden">
        <div ref={mapRef} className="w-full h-full z-0" />
      </div>
    </div>
  );
}