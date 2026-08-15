import { cerrarSesion } from './api.js';

const ACCESS_KEY = 'taxicom_access';
let socket = null;
let pingInterval = null;

export function conectarWebSocket() {
    // 1. Obtener el token con la clave real definida en api.js
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

        // Detener heartbeat previo si existía
        if (pingInterval) clearInterval(pingInterval);

        // 2. Mantener la conexión activa (evita desconexiones 1006 en Render)
        pingInterval = setInterval(() => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ action: "ping" }));
            }
        }, 25000);
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            
            // Responder/ignorar el evento pong del servidor
            if (data.event === "pong") return;

            console.log("📩 Mensaje recibido:", data);

            // Manejo de eventos del backend
            switch (data.event) {
                case "ubicacion_actualizada":
                    // Lógica para actualizar en el mapa
                    break;
                case "nuevo_cliente_colectivo":
                    // Notificación cliente
                    break;
                case "nueva_solicitud_especial":
                    // Notificación especial
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
        
        // Limpiar el heartbeat
        if (pingInterval) {
            clearInterval(pingInterval);
            pingInterval = null;
        }

        // Si el servidor rechazó por token inválido (4001), se redirige al login
        if (event.code === 4001) {
            console.error("Token rechazado por el servidor WebSocket. Inicie sesión nuevamente.");
            cerrarSesion();
            window.location.href = '/login';
            return;
        }

        // Reconexión automática sólo para desconexiones temporales (código 1006, etc.)
        if (event.code !== 1000) {
            console.log("🔄 Intentando reconectar en 5 segundos...");
            setTimeout(() => {
                conectarWebSocket();
            }, 5000);
        }
    };
}