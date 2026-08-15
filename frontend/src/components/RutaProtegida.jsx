import React from 'react';
import { Navigate } from 'react-router-dom';
import { haySesion, obtenerUsuario } from '../api.js'; 
export default function RutaProtegida({ children }) {
  if (!haySesion()) {
    return <Navigate to="/login" replace />;
  }

  const usuario = obtenerUsuario();
  if (!usuario?.es_admin) {
    return <Navigate to="/login" replace />;
  }

  return children;
}