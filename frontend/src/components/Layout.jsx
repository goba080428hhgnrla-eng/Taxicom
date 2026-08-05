import React from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';

export default function Layout() {
  const navigate = useNavigate();

  const handleLogout = () => {
    navigate('/login');
  };

  return (
    <div className="bg-slate-50 text-slate-800 min-h-screen flex flex-col font-sans">
      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-8">
            <Link to="/admin" className="flex items-center space-x-2">
              <span className="text-2xl">🚕</span>
              <span className="text-xl font-bold tracking-tight text-slate-900">
                Central<span className="text-amber-500">Taxi</span>
              </span>
            </Link>
            <nav className="hidden md:flex space-x-1">
              <Link to="/admin" className="px-3 py-2 text-sm font-medium text-slate-600 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition">
                Mapa General
              </Link>
              <Link to="/admin/choferes" className="px-3 py-2 text-sm font-medium text-slate-600 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition">
                Gestión Choferes
              </Link>
              <Link to="/admin/roles" className="px-3 py-2 text-sm font-medium text-slate-600 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition">
                Roles y Turnos
              </Link>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-xs font-semibold uppercase tracking-wider bg-slate-100 text-slate-600 px-3 py-1 rounded-full border border-slate-200">
              Administrador
            </span>
            <button
              onClick={handleLogout}
              className="text-sm font-medium text-slate-500 hover:text-red-600 transition"
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}