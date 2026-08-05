import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function Login() {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await fetch('/api/web/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      if (res.ok && data.status === 'ok') {
        navigate('/admin');
      } else {
        setError(data.message || 'Error al iniciar sesión');
      }
    } catch (err) {
      setError('Error de conexión con el servidor.');
    }
  };

  return (
    <div className="bg-slate-100 min-h-screen flex items-center justify-center px-4 font-sans">
      <div className="max-w-md w-full bg-white border border-slate-200 p-8 rounded-3xl shadow-xl">
        <div className="text-center mb-8">
          <div className="inline-block text-4xl mb-2">🚕</div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">CentralTaxi</h1>
          <p className="text-slate-500 text-sm mt-1">Panel de Control de Administración</p>
        </div>

        {error && (
          <div className="mb-6 p-4 text-sm bg-red-50 border border-red-200 text-red-600 rounded-2xl">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
              Usuario o Correo
            </label>
            <input
              type="text"
              required
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-amber-500 focus:bg-white text-slate-900 transition placeholder-slate-400"
              placeholder="Ingresa tu usuario"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
              Contraseña
            </label>
            <input
              type="password"
              required
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-amber-500 focus:bg-white text-slate-900 transition placeholder-slate-400"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          <button
            type="submit"
            className="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-3.5 px-4 rounded-xl shadow-md hover:shadow-lg transition duration-200 text-sm cursor-pointer"
          >
            Entrar al Sistema
          </button>
        </form>

        <div className="mt-8 text-center">
          <Link to="/" className="text-xs font-medium text-slate-400 hover:text-amber-600 transition">
            ← Volver al sitio principal
          </Link>
        </div>
      </div>
    </div>
  );
}