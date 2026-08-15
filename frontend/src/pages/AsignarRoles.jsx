import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../api';

export default function AsignarRoles() {
  const [datos, setDatos] = useState({ grupos_configurados: [], choferes: [], pagos_pendientes: [], dias_opciones: [] });
  const [nuevoGrupoNombre, setNuevoGrupoNombre] = useState('');
  const [diasSeleccionados, setDiasSeleccionados] = useState([]);
  const [cargando, setCargando] = useState(true);

  const cargarConfiguracion = async () => {
    setCargando(true);
    try {
      const res = await apiFetch('/api/v1/admin/roles/config/');
      if (res.ok) {
        const json = await res.json();
        setDatos(json);
      }
    } catch (err) {
      console.error("Error cargando configuración:", err);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarConfiguracion();
  }, []);

  const toggleDia = (dia) => {
    setDiasSeleccionados(prev => 
      prev.includes(dia) ? prev.filter(d => d !== dia) : [...prev, dia]
    );
  };

  const guardarGrupo = async (e) => {
    e.preventDefault();
    if (!nuevoGrupoNombre.trim() || diasSeleccionados.length === 0) {
      alert("Ingresa un nombre de grupo y al menos un día.");
      return;
    }

    const res = await apiFetch('/api/v1/admin/roles/guardar/', {
      method: 'POST',
      body: JSON.stringify({ grupo: nuevoGrupoNombre, dias: diasSeleccionados }),
    });

    if (res.ok) {
      setNuevoGrupoNombre('');
      setDiasSeleccionados([]);
      cargarConfiguracion();
    }
  };

  const eliminarGrupo = async (nombreGrupo) => {
    if (!confirm(`¿Eliminar ${nombreGrupo}? Los choferes serán redistribuidos automáticamente entre los demás grupos.`)) return;

    await apiFetch('/api/v1/admin/roles/eliminar-grupo/', {
      method: 'POST',
      body: JSON.stringify({ grupo: nombreGrupo }),
    });
    cargarConfiguracion();
  };

  const confirmarPagoEfectivo = async (pagoId, aprobado) => {
    await apiFetch('/api/v1/admin/roles/confirmar-pago/', {
      method: 'POST',
      body: JSON.stringify({ pago_id: pagoId, aprobado }),
    });
    cargarConfiguracion();
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8 font-sans">
      
      {/* HEADER */}
      <div className="flex justify-between items-center pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Asignación Automática de Roles y Cobro</h1>
          <p className="text-slate-500 text-sm mt-1">El sistema asigna los choferes a los grupos automáticamente por orden de ingreso.</p>
        </div>
        <Link to="/admin" className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-sm font-semibold text-slate-700">
          &larr; Volver
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* IZQUIERDA: CREAR GRUPO & APROBAR COBROS */}
        <div className="space-y-6">
          
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Crear Regla de Grupo</h2>
            <form onSubmit={guardarGrupo} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Nombre del Grupo</label>
                <input
                  type="text"
                  placeholder="Ej: Grupo A"
                  value={nuevoGrupoNombre}
                  onChange={(e) => setNuevoGrupoNombre(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase mb-2">Días del Rol</label>
                <div className="flex flex-wrap gap-1.5">
                  {datos.dias_opciones?.map((d) => {
                    const sel = diasSeleccionados.includes(d);
                    return (
                      <button
                        key={d}
                        type="button"
                        onClick={() => toggleDia(d)}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                          sel ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {d}
                      </button>
                    );
                  })}
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-3 rounded-xl text-sm transition shadow-sm"
              >
                Crear y Asignar Choferes
              </button>
            </form>
          </div>

          {/* CONFIRMACIÓN DE DINERO EN EFECTIVO */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900">💵 Cobros en Efectivo</h2>
              <span className="bg-amber-100 text-amber-800 text-xs px-2.5 py-0.5 rounded-full font-bold">
                {datos.pagos_pendientes?.length || 0}
              </span>
            </div>

            <div className="space-y-3">
              {datos.pagos_pendientes?.length > 0 ? (
                datos.pagos_pendientes.map((p) => (
                  <div key={p.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex justify-between items-center">
                    <div>
                      <p className="text-xs font-bold text-slate-900">{p.chofer_nombre}</p>
                      <p className="text-[11px] text-slate-500">${p.monto} - {p.fecha}</p>
                    </div>
                    <div className="flex gap-1.5">
                      <button
                        onClick={() => confirmarPagoEfectivo(p.id, true)}
                        className="bg-emerald-600 text-white text-xs font-bold px-2.5 py-1.5 rounded-lg hover:bg-emerald-500 transition"
                      >
                        Confirmar
                      </button>
                      <button
                        onClick={() => confirmarPagoEfectivo(p.id, false)}
                        className="bg-red-50 text-red-600 text-xs font-bold px-2 py-1.5 rounded-lg hover:bg-red-100 transition"
                      >
                        Rechazar
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400 text-center py-4">Sin cobros pendientes de verificación.</p>
              )}
            </div>
          </div>

        </div>

        {/* DERECHA: VER GRUPOS Y CHOFERES AUTO-ASIGNADOS */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900">Grupos y Rotación Semanal</h2>
            </div>
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-100 text-xs text-slate-400 uppercase font-semibold">
                <tr>
                  <th className="p-4">Grupo</th>
                  <th className="p-4">Total Choferes</th>
                  <th className="p-4">Días (Esta Semana)</th>
                  <th className="p-4 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {datos.grupos_configurados?.map((g) => (
                  <tr key={g.nombre} className="hover:bg-slate-50/50">
                    <td className="p-4 font-bold text-amber-600">{g.nombre}</td>
                    <td className="p-4 text-slate-600 font-medium">{g.total_choferes} asignados</td>
                    <td className="p-4">
                      <div className="flex flex-wrap gap-1">
                        {g.dias_semana_actual?.map((d) => (
                          <span key={d} className="bg-amber-100 text-amber-900 text-xs px-2 py-0.5 rounded-md font-semibold">
                            {d}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => eliminarGrupo(g.nombre)}
                        className="text-xs text-red-600 bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded-lg font-semibold transition"
                      >
                        Eliminar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900">Conductores y Asignación Automática</h2>
            </div>
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-100 text-xs text-slate-400 uppercase font-semibold">
                <tr>
                  <th className="p-4">Conductor</th>
                  <th className="p-4">Grupo Asignado</th>
                  <th className="p-4">Estado Pago</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {datos.choferes?.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/50">
                    <td className="p-4 font-semibold text-slate-800">
                      {c.nombre}
                      <span className="block text-[11px] text-slate-400 font-normal">{c.telefono}</span>
                    </td>
                    <td className="p-4">
                      <span className="bg-slate-100 text-slate-800 text-xs font-bold px-2.5 py-1 rounded-md border border-slate-200">
                        ⚡ {c.grupo_rol}
                      </span>
                    </td>
                    <td className="p-4">
                      {c.al_dia ? (
                        <span className="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-bold">
                          ✓ Al día
                        </span>
                      ) : (
                        <span className="bg-amber-100 text-amber-900 text-xs px-2.5 py-1 rounded-full font-bold">
                          ⚠️ Pendiente
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </div>

      </div>
    </div>
  );
}