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

// ==========================================
// 3. CONEXIÓN WEBSOCKET
// ==========================================

let socket = null;
let pingInterval = null;

export function conectarWebSocket() {
    const token = localStorage.getItem(ACCESS_KEY);

    if (!token || token.trim() === "") {
        console.warn("⚠️ No se encontró token JWT en localStorage ('taxicom_access'). Conexión WebSocket cancelada.");
        return;
    }

    const wsUrl = `wss://taxicom.onrender.com/ws/colectivos/?token=${encodeURIComponent(token)}`;
    console.log("⚡ Intentando conectar WebSocket a:", wsUrl);

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log("✅ WebSocket conectado exitosamente");

        if (pingInterval) clearInterval(pingInterval);

        // Mantener la conexión activa (evita desconexiones 1006 en Render)
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

            console.log("📩 Mensaje recibido:", data);

            switch (data.event) {
                case "ubicacion_actualizada":
                    break;
                case "nuevo_cliente_colectivo":
                    break;
                case "nueva_solicitud_especial":
                    break;
                default:
                    break;
            }
        } catch (error) {
            console.error("Error al procesar mensaje JSON del WebSocket:", error);
        }
    };

    socket.onerror = (error) => {
        console.error("❌ Error en WebSocket:", error);
    };

    socket.onclose = (event) => {
        console.warn(`⚠️ WebSocket Cerrado (Código: ${event.code})`);
        
        if (pingInterval) {
            clearInterval(pingInterval);
            pingInterval = null;
        }

        if (event.code === 4001) {
            console.error("Token rechazado por el servidor WebSocket. Inicie sesión nuevamente.");
            cerrarSesion();
            window.location.href = '/login';
            return;
        }

        if (event.code !== 1000) {
            console.log("🔄 Intentando reconectar en 5 segundos...");
            setTimeout(() => {
                conectarWebSocket();
            }, 5000);
        }
    };
}