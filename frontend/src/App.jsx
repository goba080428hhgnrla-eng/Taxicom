import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePublico from './pages/HomePublico';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import GestionChoferes from './pages/GestionChoferes';
import AsignarRoles from './pages/AsignarRoles';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePublico />} />
        <Route path="/login" element={<Login />} />
        <Route path="/admin" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="choferes" element={<GestionChoferes />} />
          <Route path="roles" element={<AsignarRoles />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}