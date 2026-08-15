const ACCESS_KEY = 'taxicom_access';
const REFRESH_KEY = 'taxicom_refresh';
const USUARIO_KEY = 'taxicom_usuario';

// ==========================================
// 1. GESTIÓN DE SESIÓN Y LOCALSTORAGE
// ==========================================

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

// ==========================================
// 2. PETICIONES HTTP / API FETCH
// ==========================================

async function refrescarToken() {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) return null;

  try {
    const res = await fetch('/api/v1/auth/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return null;

    const data = await res.json();
    localStorage.setItem(ACCESS_KEY, data.access);
    return data.access;
  } catch (err) {
    console.error("Error al refrescar token:", err);
    return null;
  }
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

// ==========================================
// 3. CONEXIÓN WEBSOCKET Y SUSCRIPCIONES
// ==========================================

let socket = null;
let pingInterval = null;
const suscriptores = new Set();

/**
 * Permite a los componentes suscribirse a los eventos del WebSocket
 */
export function suscribirWebSocket(callback) {
  suscriptores.add(callback);
  return () => suscriptores.delete(callback);
}

export function conectarWebSocket() {
  const token = localStorage.getItem(ACCESS_KEY);

  if (!token || token.trim() === "") {
    console.warn("⚠️ No se encontró token JWT en localStorage ('taxicom_access'). Conexión cancelada.");
    return;
  }

  // Evita duplicar conexiones abiertas
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const wsUrl = `wss://taxicom.onrender.com/ws/colectivos/?token=${encodeURIComponent(token)}`;
  console.log("⚡ Conectando a WebSocket:", wsUrl);

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("✅ WebSocket conectado exitosamente");

    if (pingInterval) clearInterval(pingInterval);

    // Heartbeat para mantener viva la conexión en Render
    pingInterval = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action: "ping" }));
      }
    }, 25000);
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.event === "pong") return;

      console.log("📩 Mensaje WS recibido:", data);

      // Notificar a todos los componentes suscritos (ej. el Dashboard)
      suscriptores.forEach((callback) => callback(data));
    } catch (error) {
      console.error("Error al procesar mensaje JSON del WebSocket:", error);
    }
  };

  socket.onerror = (error) => console.error("❌ Error en WebSocket:", error);

  socket.onclose = (event) => {
    console.warn(`⚠️ WebSocket cerrado (Código: ${event.code})`);

    if (pingInterval) {
      clearInterval(pingInterval);
      pingInterval = null;
    }

    if (event.code === 4001) {
      console.error("Token rechazado. Redirigiendo a Login...");
      cerrarSesion();
      window.location.href = '/login';
      return;
    }

    // Reconexión automática si no fue un cierre intencional
    if (event.code !== 1000) {
      setTimeout(() => conectarWebSocket(), 5000);
    }
  };
}