import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import RutaProtegida from './components/RutaProtegida.jsx';
import HomePublico from './pages/HomePublico.jsx';
import Login from './pages/Login.jsx';
import Dashboard from './pages/Dashboard.jsx';
import GestionChoferes from './pages/GestionChoferes.jsx';
import AsignarRoles from './pages/AsignarRoles.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePublico />} />
        <Route path="/login" element={<Login />} />

        <Route
          path="/admin"
          element={
            <RutaProtegida>
              <Layout />
            </RutaProtegida>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="choferes" element={<GestionChoferes />} />
          <Route path="roles" element={<AsignarRoles />} />
        </Route>

        <Route path="/dashboard" element={<Navigate to="/admin" replace />} />
      </Routes>
    </BrowserRouter>
  );
}