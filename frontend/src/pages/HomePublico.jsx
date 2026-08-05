import React from 'react';
import { Link } from 'react-router-dom';

export default function HomePublico() {
  return (
    <div className="bg-slate-50 text-slate-900 flex flex-col min-h-screen justify-between font-sans antialiased selection:bg-amber-500 selection:text-white">
      {/* Navbar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/80 border-b border-slate-200/80">
        <div className="max-w-7xl mx-auto px-6 h-20 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-amber-500 text-slate-950 rounded-xl flex items-center justify-center font-black shadow-md shadow-amber-500/20">
              <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24">
                <path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/>
              </svg>
            </div>
            <span className="text-2xl font-black tracking-tight text-slate-900">
              Central<span className="text-amber-500">Taxi</span>
            </span>
          </div>
          <Link
            to="/login"
            className="inline-flex items-center justify-center bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm px-5 py-2.5 rounded-xl shadow-sm hover:shadow transition-all duration-150 active:scale-95 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            Ingresar al Panel
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-5xl mx-auto text-center px-6 my-auto py-16 md:py-24">
        <div className="inline-flex items-center space-x-2 bg-amber-50 border border-amber-200/60 px-4 py-1.5 rounded-full mb-8">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
          <span className="text-amber-900 text-xs font-bold uppercase tracking-wider">
            Plataforma de Movilidad Operativa
          </span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-black tracking-tight text-slate-900 mb-6 leading-[1.1]">
          El viaje que mereces, <br className="hidden md:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-500 to-amber-600">
            seguro y confiable.
          </span>
        </h1>
        
        <p className="text-slate-600 text-lg md:text-xl max-w-2xl mx-auto mb-12 leading-relaxed">
          Rastreo en tiempo real, choferes certificados y la mayor comodidad directo a tu ubicación.
        </p>

        {/* Feature Badges */}
        <div className="flex flex-wrap gap-4 justify-center items-center">
          <div className="bg-white border border-slate-200/80 shadow-sm hover:shadow transition-shadow px-5 py-3.5 rounded-2xl text-sm font-semibold text-slate-700 flex items-center space-x-3">
            <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span>Ruta Fija Garantizada</span>
          </div>
          
          <div className="bg-white border border-slate-200/80 shadow-sm hover:shadow transition-shadow px-5 py-3.5 rounded-2xl text-sm font-semibold text-slate-700 flex items-center space-x-3">
            <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <span>Espacio para Equipaje</span>
          </div>

          <div className="bg-white border border-slate-200/80 shadow-sm hover:shadow transition-shadow px-5 py-3.5 rounded-2xl text-sm font-semibold text-slate-700 flex items-center space-x-3">
            <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
            </svg>
            <span>Visualización 3D</span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-8 text-center text-slate-500 text-sm border-t border-slate-200 bg-white">
        <p>&copy; 2026 CentralTaxi. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}