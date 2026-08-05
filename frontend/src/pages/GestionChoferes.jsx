import React, { useEffect, useState } from 'react';

export default function GestionChoferes() {
  const [pendientes, setPendientes] = useState([]);
  const [activos, setActivos] = useState([]);

  const cargarDatos = () => {
    fetch('/api/web/gestion-choferes/')
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
    await fetch('/api/web/gestion-choferes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chofer_id, accion }),
    });
    cargarDatos();
  };

  return (
    <div className="space-y-8 font-sans">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Solicitudes y Operadores</h1>
        <p className="text-slate-500 text-sm mt-1">Valida nuevos conductores o revisa el estado de la flota activa.</p>
      </div>

      {/* Solicitudes Pendientes */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 bg-amber-50/50">
          <h2 className="text-base font-bold text-amber-900">Nuevas Solicitudes por Aprobar</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase border-b border-slate-200">
                <th className="p-4">Nombre</th>
                <th className="p-4">Teléfono</th>
                <th className="p-4">Vehículo</th>
                <th className="p-4">Placas</th>
                <th className="p-4 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {pendientes.length > 0 ? (
                pendientes.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/80 transition">
                    <td className="p-4 font-semibold text-slate-800">
                      {p.perfil.nombre} {p.perfil.apellido}
                    </td>
                    <td className="p-4 text-slate-600">{p.perfil.telefono || 'Sin teléfono'}</td>
                    <td className="p-4 text-slate-600">
                      {p.vehiculo.marca} {p.vehiculo.modelo} {p.vehiculo.anio && `(${p.vehiculo.anio})`}
                    </td>
                    <td className="p-4 font-mono font-bold text-amber-600">{p.vehiculo.placas}</td>
                    <td className="p-4 text-center">
                      <div className="flex justify-center space-x-2">
                        <button
                          onClick={() => handleAccion(p.id, 'aceptar')}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs px-3 py-1.5 rounded-lg transition shadow-sm"
                        >
                          Aceptar
                        </button>
                        <button
                          onClick={() => handleAccion(p.id, 'rechazar')}
                          className="bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 font-medium text-xs px-3 py-1.5 rounded-lg transition"
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

      {/* Choferes Activos */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100">
          <h2 className="text-base font-bold text-slate-900">Choferes Activos / En Ruta</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase border-b border-slate-200">
                <th className="p-4">Nombre</th>
                <th className="p-4">Vehículo</th>
                <th className="p-4">Placas</th>
                <th className="p-4">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {activos.length > 0 ? (
                activos.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/80 transition">
                    <td className="p-4 font-semibold text-slate-800">
                      {c.perfil.nombre} {c.perfil.apellido}
                    </td>
                    <td className="p-4 text-slate-600">
                      {c.vehiculo.marca} {c.vehiculo.modelo}
                    </td>
                    <td className="p-4 font-mono font-bold text-slate-700">{c.vehiculo.placas}</td>
                    <td className="p-4">
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase ${
                          c.estado === 'en_ruta'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-blue-100 text-blue-800'
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