import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { guardarSesion, cerrarSesion } from '../api';

export default function Login() {
  const [formData, setFormData] = useState({ correo_o_usuario: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();

      if (!res.ok) {
        const mensaje =
          data.non_field_errors?.[0] || data.detail || 'Credenciales inválidas. Verifica tus datos.';
        setError(mensaje);
        return;
      }

      if (!data.usuario?.es_admin) {
        cerrarSesion();
        setError('Acceso denegado. No eres administrador.');
        return;
      }

      guardarSesion(data);
      navigate('/admin');
    } catch (err) {
      setError('Error de conexión con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-100/70 min-h-screen flex items-center justify-center p-4 font-sans antialiased">
      <div className="max-w-md w-full bg-white border border-slate-200/80 p-8 rounded-3xl shadow-xl shadow-slate-200/50">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-amber-500 text-slate-950 rounded-2xl mb-4 shadow-md shadow-amber-500/20">
            <svg className="w-7 h-7 fill-current" viewBox="0 0 24 24">
              <path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/>
            </svg>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">CentralTaxi</h1>
          <p className="text-slate-500 text-sm mt-1">Panel de Control de Administración</p>
        </div>

        {error && (
          <div className="mb-6 p-4 text-sm bg-red-50 border border-red-200/80 text-red-700 rounded-2xl flex items-center space-x-3">
            <svg className="w-5 h-5 text-red-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Usuario o Correo
            </label>
            <input
              type="text"
              required
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 focus:bg-white text-slate-900 transition placeholder-slate-400"
              placeholder="nombre@ejemplo.com"
              value={formData.correo_o_usuario}
              onChange={(e) => setFormData({ ...formData, correo_o_usuario: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Contraseña
            </label>
            <input
              type="password"
              required
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 focus:bg-white text-slate-900 transition placeholder-slate-400"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-amber-500 hover:bg-amber-400 active:scale-[0.99] disabled:opacity-50 text-slate-950 font-bold py-3.5 px-4 rounded-xl shadow-md shadow-amber-500/10 hover:shadow-lg transition duration-150 text-sm cursor-pointer"
          >
            {loading ? 'Validando...' : 'Entrar al Sistema'}
          </button>
        </form>

        <div className="mt-8 text-center border-t border-slate-100 pt-6">
          <Link to="/" className="inline-flex items-center text-xs font-medium text-slate-500 hover:text-slate-900 transition space-x-1">
            <span>&larr;</span>
            <span>Volver al sitio principal</span>
          </Link>
        </div>
      </div>
    </div>
  );
}