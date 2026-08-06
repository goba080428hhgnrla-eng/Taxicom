import React, { useEffect, useState } from 'react';
import { apiFetch } from '../api';

export default function GestionChoferes() {
  const [pendientes, setPendientes] = useState([]);
  const [activos, setActivos] = useState([]);

  const cargarDatos = () => {
    apiFetch('/api/v1/admin/choferes/')
      .then((res) => res.json())
      .then((data) => {
        setPendientes(data.pendientes || []);
        setActivos(data.activos || []);
      });
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  const handleAccion = async (chofer_id, accion) => {
    const res = await apiFetch('/api/v1/admin/choferes/gestionar/', {
      method: 'POST',
      body: JSON.stringify({ chofer_id, accion }),
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.message || 'No se pudo procesar la acción.');
      return;
    }
    cargarDatos();
  };

  return (
    <div className="space-y-8 font-sans antialiased max-w-7xl mx-auto p-6">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Solicitudes y Operadores</h1>
        <p className="text-slate-500 text-sm mt-1">Valida nuevos conductores o revisa el estado de la flota activa.</p>
      </div>

      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-amber-50/30 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-amber-950">Nuevas Solicitudes por Aprobar</h2>
            <p className="text-xs text-amber-800/80">Conductores en espera de verificación de documentos</p>
          </div>
          <span className="bg-amber-100 text-amber-900 text-xs font-bold px-3 py-1 rounded-full">
            {pendientes.length} pendientes
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                <th className="p-4 pl-6">Nombre</th>
                <th className="p-4">Teléfono</th>
                <th className="p-4">Vehículo</th>
                <th className="p-4">Placas</th>
                <th className="p-4 text-center pr-6">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {pendientes.length > 0 ? (
                pendientes.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/50 transition">
                    <td className="p-4 pl-6 font-bold text-slate-900">
                      {p.perfil.nombre} {p.perfil.apellido}
                    </td>
                    <td className="p-4 text-slate-600">{p.perfil.telefono || 'Sin teléfono'}</td>
                    <td className="p-4 text-slate-600">
                      {p.vehiculo.marca} {p.vehiculo.modelo} {p.vehiculo.anio && `(${p.vehiculo.anio})`}
                    </td>
                    <td className="p-4 font-mono font-bold text-slate-700">{p.vehiculo.placas}</td>
                    <td className="p-4 text-center pr-6">
                      <div className="flex justify-center space-x-2">
                        <button
                          onClick={() => handleAccion(p.id, 'aceptar')}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-3.5 py-1.5 rounded-xl transition shadow-sm"
                        >
                          Aceptar
                        </button>
                        <button
                          onClick={() => handleAccion(p.id, 'rechazar')}
                          className="bg-red-50 hover:bg-red-100 text-red-600 border border-red-200/60 font-semibold text-xs px-3.5 py-1.5 rounded-xl transition"
                        >
                          Rechazar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-slate-400">
                    No hay registros pendientes de validación.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h2 className="text-base font-bold text-slate-900">Choferes Activos / En Ruta</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                <th className="p-4 pl-6">Nombre</th>
                <th className="p-4">Vehículo</th>
                <th className="p-4">Placas</th>
                <th className="p-4 pr-6">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {activos.length > 0 ? (
                activos.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/50 transition">
                    <td className="p-4 pl-6 font-semibold text-slate-900">
                      {c.perfil.nombre} {c.perfil.apellido}
                    </td>
                    <td className="p-4 text-slate-600">
                      {c.vehiculo.marca} {c.vehiculo.modelo}
                    </td>
                    <td className="p-4 font-mono font-bold text-slate-700">{c.vehiculo.placas}</td>
                    <td className="p-4 pr-6">
                      <span
                        className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                          c.estado === 'en_ruta'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                            : 'bg-blue-50 text-blue-700 border border-blue-200/60'
                        }`}
                      >
                        {c.estado_display}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="p-8 text-center text-slate-400">
                    No hay choferes activos registrados en el sistema.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}