import React from 'react';
import { Link } from 'react-router-dom';

export default function HomePublico() {
  return (
    <div className="bg-slate-50 text-slate-900 flex flex-col min-h-screen justify-between font-sans">
      <header className="p-6 max-w-6xl mx-auto w-full flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <span className="text-3xl">🚕</span>
          <span className="text-2xl font-extrabold tracking-tight text-slate-900">
            Central<span className="text-amber-500">Taxi</span>
          </span>
        </div>
        <Link
          to="/login"
          className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold px-5 py-2.5 rounded-xl shadow-md hover:shadow-lg transition duration-200"
        >
          Ingresar al Panel
        </Link>
      </header>

      <main className="max-w-4xl mx-auto text-center px-6 my-auto py-16">
        <span className="bg-amber-100 text-amber-800 text-xs font-bold px-3 py-1.5 rounded-full uppercase tracking-wider">
          Plataforma de Movilidad Operativa
        </span>
        <h1 className="text-5xl md:text-6xl font-black tracking-tight text-slate-900 mt-6 mb-6 leading-tight">
          El viaje que mereces, <span className="text-amber-500">seguro y confiable.</span>
        </h1>
        <p className="text-slate-600 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
          Rastreo en tiempo real, choferes certificados y la mayor comodidad directo a tu ubicación.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <span className="bg-white border border-slate-200 shadow-sm px-5 py-3 rounded-2xl text-sm font-semibold text-slate-700 flex items-center space-x-2">
            <span>📍</span> <span>Una Sola Ruta Fija</span>
          </span>
          <span className="bg-white border border-slate-200 shadow-sm px-5 py-3 rounded-2xl text-sm font-semibold text-slate-700 flex items-center space-x-2">
            <span>📦</span> <span>Espacio para Cajuela</span>
          </span>
          <span className="bg-white border border-slate-200 shadow-sm px-5 py-3 rounded-2xl text-sm font-semibold text-slate-700 flex items-center space-x-2">
            <span>🎮</span> <span>Autos en 3D</span>
          </span>
        </div>
      </main>

      <footer className="p-6 text-center text-slate-400 text-sm border-t border-slate-200 bg-white">
        &copy; 2026 CentralTaxi. Todos los derechos reservados.
      </footer>
    </div>
  );
}