import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../api';

export default function AsignarRoles() {
  const [datos, setDatos] = useState({ grupos_configurados: [], choferes: [], pagos_pendientes: [] });
  const [cargando, setCargando] = useState(true);

  const cargarDatos = async () => {
    try {
      const res = await apiFetch('/api/v1/admin/roles/config/');
      if (res.ok) {
        const json = await res.json();
        setDatos(json);
      }
    } catch (err) {
      console.error("Error al cargar los datos:", err);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  const confirmarPagoEfectivo = async (pagoId, aprobado) => {
    try {
      const res = await apiFetch('/api/v1/admin/roles/confirmar-pago/', {
        method: 'POST',
        body: JSON.stringify({ pago_id: pagoId, aprobado }),
      });
      if (res.ok) {
        cargarDatos(); // Recargar para actualizar la lista de pendientes y estados
      }
    } catch (error) {
      console.error("Error al confirmar el pago:", error);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8 font-sans">
      
      {/* HEADER */}
      <div className="flex justify-between items-center pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Control de Pagos en Efectivo y Roles</h1>
          <p className="text-slate-500 text-sm mt-1">El sistema asigna los grupos de manera 100% automática.</p>
        </div>
        <Link to="/admin" className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-sm font-semibold text-slate-700">
          &larr; Volver al Admin
        </Link>
      </div>

      {/* SECCIÓN 1: ÚNICA TAREA MANUAL DEL ADMIN (CONFIRMAR EFECTIVO) */}
      <div className="bg-white p-6 rounded-2xl border border-amber-200 bg-amber-50/20 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">💵 Confirmación de Cobros en Efectivo</h2>
            <p className="text-xs text-slate-500">Confirma aquí únicamente cuando recibas el dinero del chofer físicamente.</p>
          </div>
          <span className="bg-amber-500 text-slate-950 font-bold text-xs px-3 py-1 rounded-full">
            {datos.pagos_pendientes?.length || 0} Pendientes
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
          {datos.pagos_pendientes?.length > 0 ? (
            datos.pagos_pendientes.map((p) => (
              <div key={p.id} className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between space-y-3">
                <div>
                  <p className="text-sm font-bold text-slate-900">{p.chofer_nombre}</p>
                  <p className="text-lg font-extrabold text-amber-600">${p.monto} <span className="text-xs font-normal text-slate-400">MXN</span></p>
                  <p className="text-[11px] text-slate-400">{p.fecha}</p>
                </div>
                <div className="flex gap-2 pt-2 border-t border-slate-100">
                  <button
                    onClick={() => confirmarPagoEfectivo(p.id, true)}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold py-2 rounded-lg transition"
                  >
                    Confirmar Cobro
                  </button>
                  <button
                    onClick={() => confirmarPagoEfectivo(p.id, false)}
                    className="bg-red-50 hover:bg-red-100 text-red-600 text-xs font-bold px-3 py-2 rounded-lg transition"
                  >
                    Rechazar
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full py-6 text-center text-slate-400 text-xs font-medium">
              ✨ No hay cobros en efectivo pendientes por confirmar en este momento.
            </div>
          )}
        </div>
      </div>

      {/* SECCIÓN 2: INFORMACIÓN EN SOLO LECTURA DEL SISTEMA AUTOMÁTICO */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* GRUPOS AUTOMÁTICOS */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50">
            <h3 className="text-sm font-bold text-slate-800">Grupos y Cobertura (Automático)</h3>
          </div>
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-slate-400 uppercase font-semibold border-b border-slate-100">
              <tr>
                <th className="p-3">Grupo</th>
                <th className="p-3">Días Esta Semana</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {datos.grupos_configurados?.map((g) => (
                <tr key={g.nombre}>
                  <td className="p-3 font-bold text-amber-600">{g.nombre} ({g.total_choferes})</td>
                  <td className="p-3">
                    <div className="flex flex-wrap gap-1">
                      {g.dias_semana_actual?.map((d) => (
                        <span key={d} className="bg-amber-100 text-amber-900 text-[11px] px-2 py-0.5 rounded font-bold">
                          {d}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* CHOFERES ASIGNADOS */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50">
            <h3 className="text-sm font-bold text-slate-800">Asignación de Choferes</h3>
          </div>
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-slate-400 uppercase font-semibold border-b border-slate-100">
              <tr>
                <th className="p-3">Chofer</th>
                <th className="p-3">Grupo</th>
                <th className="p-3">Estatus Rol</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {datos.choferes?.map((c) => (
                <tr key={c.id}>
                  <td className="p-3 font-semibold text-slate-800">{c.nombre}</td>
                  <td className="p-3 font-bold text-slate-600">⚡ {c.grupo_rol}</td>
                  <td className="p-3">
                    {c.al_dia ? (
                      <span className="text-emerald-600 font-bold text-xs">✓ Al día</span>
                    ) : (
                      <span className="text-amber-600 font-bold text-xs">⚠️ Pendiente</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>

    </div>
  );
}