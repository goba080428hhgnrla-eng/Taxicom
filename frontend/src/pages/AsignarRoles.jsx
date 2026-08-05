import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export default function AsignarRoles() {
  const [grupo, setGrupo] = useState('');
  const [diasSeleccionados, setDiasSeleccionados] = useState([]);
  const [gruposConfigurados, setGruposConfigurados] = useState({});
  const [choferes, setChoferes] = useState([]);
  const [diasOpciones, setDiasOpciones] = useState([]);
  const [asignaciones, setAsignaciones] = useState({});

  const cargarDatos = () => {
    fetch('/api/web/roles/')
      .then((res) => res.json())
      .then((data) => {
        setGruposConfigurados(data.grupos_configurados || {});
        setChoferes(data.choferes || []);
        setDiasOpciones(data.dias_opciones || []);
      });
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  const toggleDia = (dia) => {
    setDiasSeleccionados((prev) =>
      prev.includes(dia) ? prev.filter((d) => d !== dia) : [...prev, dia]
    );
  };

  const guardarGrupo = async (e) => {
    e.preventDefault();
    await fetch('/api/web/roles/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accion: 'guardar_regla', grupo, dias: diasSeleccionados }),
    });
    setGrupo('');
    setDiasSeleccionados([]);
    cargarDatos();
  };

  const eliminarGrupo = async (nombreGrupo) => {
    if (!confirm('¿Eliminar grupo? Los choferes de este grupo quedarán sin rol asignado.')) return;
    await fetch('/api/web/roles/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accion: 'eliminar_grupo', grupo: nombreGrupo }),
    });
    cargarDatos();
  };

  const vincularChofer = async (chofer_id) => {
    const grupo_rol = asignaciones[chofer_id] ?? '';
    await fetch('/api/web/roles/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ accion: 'asignar_chofer', chofer_id, grupo_rol }),
    });
    cargarDatos();
  };

  return (
    <div className="space-y-8 font-sans">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Gestión Operativa de Roles</h1>
          <p className="text-slate-500 text-sm mt-1">Crea grupos de servicio y asigna conductores por turno.</p>
        </div>
        <Link
          to="/admin"
          className="bg-white border border-slate-200 hover:bg-slate-50 px-4 py-2 rounded-xl text-sm font-semibold text-slate-700 transition shadow-sm"
        >
          ← Volver al Mapa
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Formulario */}
        <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm h-fit">
          <h2 className="text-base font-bold text-slate-900 mb-2">Definir Nuevo Grupo</h2>
          <p className="text-xs text-slate-500 mb-6">
            Configura un grupo y selecciona qué días tiene permitido operar.
          </p>

          <form onSubmit={guardarGrupo} className="space-y-5">
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Nombre del Grupo</label>
              <input
                type="text"
                required
                placeholder="Ej: Grupo 1, Fin de Semana"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-amber-500 focus:bg-white text-slate-800 transition"
                value={grupo}
                onChange={(e) => setGrupo(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-3">Días Autorizados</label>
              <div className="grid grid-cols-2 gap-2.5">
                {diasOpciones.map((dia) => (
                  <label
                    key={dia}
                    className="flex items-center space-x-2.5 bg-slate-50 border border-slate-200 p-2.5 rounded-xl cursor-pointer hover:border-amber-400 transition"
                  >
                    <input
                      type="checkbox"
                      checked={diasSeleccionados.includes(dia)}
                      onChange={() => toggleDia(dia)}
                      className="accent-amber-500 rounded text-slate-900 focus:ring-0"
                    />
                    <span className="text-xs font-medium text-slate-700">{dia}</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-3 rounded-xl transition shadow-md text-sm cursor-pointer"
            >
              Crear / Actualizar Grupo
            </button>
          </form>
        </div>

        {/* Tablas */}
        <div className="lg:col-span-2 space-y-8">
          {/* Calendario de Grupos */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900">Grupos Registrados</h2>
            </div>
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase border-b border-slate-200">
                  <th className="p-4">Grupo</th>
                  <th className="p-4">Días Operativos</th>
                  <th className="p-4 text-center">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {Object.keys(gruposConfigurados).length > 0 ? (
                  Object.entries(gruposConfigurados).map(([gNombre, dias]) => (
                    <tr key={gNombre} className="hover:bg-slate-50/80 transition">
                      <td className="p-4 font-bold text-amber-600">{gNombre}</td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1.5">
                          {dias.map((d) => (
                            <span
                              key={d}
                              className="bg-slate-100 border border-slate-200 text-slate-700 text-xs px-2.5 py-1 rounded-lg font-medium"
                            >
                              📅 {d}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="p-4 text-center">
                        <button
                          onClick={() => eliminarGrupo(gNombre)}
                          className="text-xs bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 px-3 py-1.5 rounded-lg font-medium transition"
                        >
                          Eliminar
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="3" className="p-8 text-center text-slate-400">
                      No hay grupos configurados aún.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Asignación a Personal */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900">Asignación Manual de Personal</h2>
            </div>
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase border-b border-slate-200">
                  <th className="p-4">Conductor</th>
                  <th className="p-4">Estado</th>
                  <th className="p-4">Grupo / Rol</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {choferes.length > 0 ? (
                  choferes.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/80 transition">
                      <td className="p-4">
                        <div className="font-semibold text-slate-800">
                          {c.perfil.nombre} {c.perfil.apellido}
                        </div>
                        <div className="text-xs text-slate-400">{c.perfil.telefono || 'Sin teléfono'}</div>
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
                          {c.estado_display}
                        </span>
                      </td>
                      <td className="p-4 flex items-center space-x-2">
                        <select
                          value={asignaciones[c.id] ?? c.grupo_rol ?? ''}
                          onChange={(e) => setAsignaciones({ ...asignaciones, [c.id]: e.target.value })}
                          className="bg-slate-50 border border-slate-200 text-xs text-slate-800 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-amber-500 transition"
                        >
                          <option value="">-- Fuera de Rol --</option>
                          {Object.keys(gruposConfigurados).map((g) => (
                            <option key={g} value={g}>
                              {g}
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={() => vincularChofer(c.id)}
                          className="bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold px-3 py-1.5 rounded-lg transition"
                        >
                          Vincular
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="3" className="p-8 text-center text-slate-400">
                      No hay conductores disponibles para asignar.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}