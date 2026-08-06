const ACCESS_KEY = 'taxicom_access';
const REFRESH_KEY = 'taxicom_refresh';
const USUARIO_KEY = 'taxicom_usuario';

export function guardarSesion({ access, refresh, usuario }) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
  localStorage.setItem(USUARIO_KEY, JSON.stringify(usuario));
}

export function obtenerUsuario() {
  const raw = localStorage.getItem(USUARIO_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function haySesion() {
  return !!localStorage.getItem(ACCESS_KEY);
}

export function cerrarSesion() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USUARIO_KEY);
}

async function refrescarToken() {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) return null;

  const res = await fetch('/api/v1/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) return null;

  const data = await res.json();
  localStorage.setItem(ACCESS_KEY, data.access);
  return data.access;
}

export async function apiFetch(path, options = {}) {
  const access = localStorage.getItem(ACCESS_KEY);
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
    ...(access ? { Authorization: `Bearer ${access}` } : {}),
  };

  let res = await fetch(path, { ...options, headers });

  if (res.status === 401 && access) {
    const nuevoAccess = await refrescarToken();
    if (nuevoAccess) {
      res = await fetch(path, {
        ...options,
        headers: { ...headers, Authorization: `Bearer ${nuevoAccess}` },
      });
    } else {
      cerrarSesion();
      window.location.href = '/login';
      return res;
    }
  }

  return res;
}