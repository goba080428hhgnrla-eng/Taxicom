import React, { useEffect, useState } from 'react';
import { apiFetch } from '../api';

export default function GestionChoferes() {
  const [pendientes, setPendientes] = useState([]);
  const [activos, setActivos] = useState([]);

  // Estados para el expediente lateral y baja por incidencia
  const [choferDetalle, setChoferDetalle] = useState(null);
  const [cargandoDetalle, setCargandoDetalle] = useState(false);
  const [modalEliminar, setModalEliminar] = useState(false);
  const [motivoIncidencia, setMotivoIncidencia] = useState('');

  const cargarDatos = () => {
    apiFetch('/api/v1/admin/choferes/')
      .then((res) => res.json())
      .then((data) => {
        setPendientes(data.pendientes || []);
        setActivos(data.activos || []);
      })
      .catch((err) => console.error("Error al cargar choferes:", err));
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
    if (choferDetalle?.id === chofer_id) setChoferDetalle(null);
    cargarDatos();
  };

  const abrirExpediente = async (chofer_id) => {
    setCargandoDetalle(true);
    try {
      const res = await apiFetch(`/api/v1/admin/choferes/${chofer_id}/`);
      const contentType = res.headers.get("content-type");
      
      if (!contentType || !contentType.includes("application/json")) {
        console.error(`Respuesta no válida del servidor (${res.status}).`);
        alert(`Error (${res.status}): Verifica la ruta '/api/v1/admin/choferes/${chofer_id}/' enurls.py.`);
        return;
      }

      const data = await res.json();
      if (res.ok) {
        setChoferDetalle(data);
      } else {
        alert(data.message || "Error al obtener datos del chofer");
      }
    } catch (error) {
      console.error("Error al obtener expediente:", error);
    } finally {
      setCargandoDetalle(false);
    }
  };

  const handleEliminarIncidencia = async () => {
    if (!choferDetalle) return;

    const res = await apiFetch(`/api/v1/admin/choferes/${choferDetalle.id}/`, {
      method: 'DELETE',
      body: JSON.stringify({ motivo: motivoIncidencia }),
    });

    if (res.ok) {
      setModalEliminar(false);
      setChoferDetalle(null);
      setMotivoIncidencia('');
      cargarDatos();
    } else {
      alert("No se pudo dar de baja al conductor.");
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 font-sans antialiased max-w-7xl mx-auto p-4 sm:p-6 pt-4 md:pt-6">
      
      {/* HEADER PRINCIPAL */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Solicitudes y Operadores
        </h1>
        <p className="text-slate-500 text-xs sm:text-sm mt-1">
          Valida nuevos conductores o selecciona cualquier operador para ver su expediente completo.
        </p>
      </div>

      {/* FLOATING SPINNER */}
      {cargandoDetalle && (
        <div className="fixed top-20 right-4 bg-amber-500 text-slate-950 px-3 py-1.5 rounded-xl text-xs font-bold shadow-xl z-50 animate-pulse">
          Cargando expediente...
        </div>
      )}

      {/* TABLA 1: PENDIENTES */}
      <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 sm:p-6 border-b border-slate-100 bg-amber-50/30 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-sm sm:text-base font-bold text-amber-950">Nuevas Solicitudes por Aprobar</h2>
            <p className="text-xs text-amber-800/80">Haz clic en una fila para revisar la información</p>
          </div>
          <span className="self-start sm:self-auto bg-amber-100 text-amber-900 text-xs font-bold px-3 py-1 rounded-full">
            {pendientes.length} pendientes
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[600px]">
            <thead>
              <tr className="bg-slate-50/50 text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                <th className="p-3 sm:p-4 pl-4 sm:pl-6">Nombre</th>
                <th className="p-3 sm:p-4">Teléfono</th>
                <th className="p-3 sm:p-4">Vehículo</th>
                <th className="p-3 sm:p-4">Placas</th>
                <th className="p-3 sm:p-4 text-center pr-4 sm:pr-6">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs sm:text-sm">
              {pendientes.length > 0 ? (
                pendientes.map((p) => (
                  <tr 
                    key={p.id} 
                    onClick={() => abrirExpediente(p.id)}
                    className="hover:bg-amber-50/30 cursor-pointer transition active:bg-amber-100/50"
                  >
                    <td className="p-3 sm:p-4 pl-4 sm:pl-6 font-bold text-slate-900">
                      {p.perfil.nombre} {p.perfil.apellido}
                    </td>
                    <td className="p-3 sm:p-4 text-slate-600">{p.perfil.telefono || 'Sin teléfono'}</td>
                    <td className="p-3 sm:p-4 text-slate-600">
                      {p.vehiculo.marca} {p.vehiculo.modelo}
                    </td>
                    <td className="p-3 sm:p-4 font-mono font-bold text-slate-700">{p.vehiculo.placas}</td>
                    <td className="p-3 sm:p-4 text-center pr-4 sm:pr-6" onClick={(e) => e.stopPropagation()}>
                      <div className="flex justify-center space-x-1.5">
                        <button
                          onClick={() => handleAccion(p.id, 'aceptar')}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-3 py-1 rounded-lg transition"
                        >
                          Aceptar
                        </button>
                        <button
                          onClick={() => handleAccion(p.id, 'rechazar')}
                          className="bg-red-50 hover:bg-red-100 text-red-600 border border-red-200/60 font-semibold text-xs px-3 py-1 rounded-lg transition"
                        >
                          Rechazar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="p-6 text-center text-slate-400 text-xs sm:text-sm">
                    No hay registros pendientes de validación.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* TABLA 2: ACTIVOS */}
      <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 sm:p-6 border-b border-slate-100">
          <h2 className="text-sm sm:text-base font-bold text-slate-900">Choferes Activos / En Ruta</h2>
          <p className="text-xs text-slate-400 mt-0.5">Selecciona cualquier chofer registrado para inspeccionar su expediente</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[500px]">
            <thead>
              <tr className="bg-slate-50/50 text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                <th className="p-3 sm:p-4 pl-4 sm:pl-6">Nombre</th>
                <th className="p-3 sm:p-4">Vehículo</th>
                <th className="p-3 sm:p-4">Placas</th>
                <th className="p-3 sm:p-4 pr-4 sm:pr-6">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs sm:text-sm">
              {activos.length > 0 ? (
                activos.map((c) => (
                  <tr 
                    key={c.id} 
                    onClick={() => abrirExpediente(c.id)}
                    className="hover:bg-slate-100/70 cursor-pointer transition active:bg-slate-200"
                  >
                    <td className="p-3 sm:p-4 pl-4 sm:pl-6 font-semibold text-slate-900">
                      {c.perfil.nombre} {c.perfil.apellido}
                    </td>
                    <td className="p-3 sm:p-4 text-slate-600">
                      {c.vehiculo.marca} {c.vehiculo.modelo}
                    </td>
                    <td className="p-3 sm:p-4 font-mono font-bold text-slate-700">{c.vehiculo.placas}</td>
                    <td className="p-3 sm:p-4 pr-4 sm:pr-6">
                      <span
                        className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] sm:text-xs font-bold uppercase tracking-wider ${
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
                  <td colSpan="4" className="p-6 text-center text-slate-400 text-xs sm:text-sm">
                    No hay choferes activos registrados en el sistema.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* EXPEDIENTE SLIDE-OVER (AJUSTADO PARA RESPONSIVE Y SIN EMPALMAR NAVBAR) */}
      {choferDetalle && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex justify-end">
          <div className="bg-white w-full sm:w-[450px] h-full shadow-2xl p-5 sm:p-6 overflow-y-auto flex flex-col justify-between">
            <div className="space-y-5">
              
              {/* Encabezado panel */}
              <div className="flex items-start justify-between border-b border-slate-100 pb-4">
                <div>
                  <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
                    Expediente Digital
                  </span>
                  <h3 className="text-lg sm:text-xl font-bold text-slate-900 mt-2">
                    {choferDetalle.perfil.nombre} {choferDetalle.perfil.apellido}
                  </h3>
                  <p className="text-xs text-slate-400">ID Operador: #{choferDetalle.id}</p>
                </div>
                <button
                  onClick={() => setChoferDetalle(null)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 rounded-full hover:bg-slate-100 text-lg font-bold"
                >
                  ✕
                </button>
              </div>

              {/* Datos Personales */}
              <div className="space-y-2.5">
                <h4 className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">Información de Contacto</h4>
                <div className="bg-slate-50 rounded-2xl p-3.5 sm:p-4 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Teléfono:</span>
                    <span className="font-bold text-slate-800">{choferDetalle.perfil.telefono || 'Sin registro'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Correo:</span>
                    <span className="font-bold text-slate-800 truncate max-w-[180px] sm:max-w-none">{choferDetalle.perfil.email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Grupo / Turno:</span>
                    <span className="font-bold text-amber-600">⚡ {choferDetalle.grupo_rol}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Fecha de Registro:</span>
                    <span className="font-medium text-slate-600">{choferDetalle.perfil.fecha_registro}</span>
                  </div>
                </div>
              </div>

              {/* Datos Vehículo */}
              <div className="space-y-2.5">
                <h4 className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">Vehículo Registrado</h4>
                {choferDetalle.vehiculo ? (
                  <div className="bg-slate-900 text-white rounded-2xl p-4 sm:p-5 space-y-3 shadow-md">
                    <div className="flex justify-between items-center">
                      <p className="font-extrabold text-sm sm:text-base">{choferDetalle.vehiculo.marca} {choferDetalle.vehiculo.modelo}</p>
                      <span className="bg-amber-500 text-slate-950 font-black text-xs px-2.5 py-1 rounded-lg">
                        {choferDetalle.vehiculo.placas}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs text-slate-300 border-t border-slate-800 pt-3">
                      <div>Año: <b className="text-white">{choferDetalle.vehiculo.anio || 'N/A'}</b></div>
                      <div>Color: <b className="text-white">{choferDetalle.vehiculo.color}</b></div>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No cuenta con vehículo asignado.</p>
                )}
              </div>

            </div>

            {/* BOTÓN DAR DE BAJA */}
            <div className="pt-4 mt-6 border-t border-slate-100">
              <button
                onClick={() => setModalEliminar(true)}
                className="w-full bg-red-50 hover:bg-red-100 text-red-600 border border-red-200/70 font-bold text-xs py-3 rounded-2xl transition flex items-center justify-center space-x-2"
              >
                <span>🚨 Dar de baja por Incidencia</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL DE INCIDENCIA */}
      {modalEliminar && (
        <div className="fixed inset-0 z-[60] bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-extrabold text-red-600">Baja por Incidencia</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Ingresa la justificación de la baja para <b className="text-slate-900">{choferDetalle?.perfil.nombre}</b>:
            </p>
            <textarea
              value={motivoIncidencia}
              onChange={(e) => setMotivoIncidencia(e.target.value)}
              placeholder="Ej. Accidente, cobro no autorizado, falta administrativa..."
              className="w-full border border-slate-200 rounded-2xl p-3 text-xs focus:ring-2 focus:ring-red-500 focus:outline-none min-h-[80px]"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setModalEliminar(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl"
              >
                Cancelar
              </button>
              <button
                onClick={handleEliminarIncidencia}
                className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-xl"
              >
                Confirmar Baja
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}