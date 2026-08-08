import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import { apiFetch } from '../api';

const taxiIcon = L.icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png',
  iconSize: [36, 36],
  iconAnchor: [18, 18],
  popupAnchor: [0, -18],
});

export default function Dashboard() {
  const [choferes, setChoferes] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);

  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markers = useRef({});

  // =========================================================
  // ANIMACIÓN DEL MARCADOR
  // =========================================================

  const moverMarcadorFluidamente = (
    marker,
    targetLat,
    targetLng,
    duracion = 2000
  ) => {
    const startLatLng = marker.getLatLng();

    const startLat = startLatLng.lat;
    const startLng = startLatLng.lng;

    if (startLat === targetLat && startLng === targetLng) return;

    const startTime = performance.now();

    function animar(currentTime) {
      const elapsedTime = currentTime - startTime;

      const progress = Math.min(
        elapsedTime / duracion,
        1
      );

      const currentLat =
        startLat +
        (targetLat - startLat) * progress;

      const currentLng =
        startLng +
        (targetLng - startLng) * progress;

      marker.setLatLng([
        currentLat,
        currentLng,
      ]);

      if (progress < 1) {
        requestAnimationFrame(animar);
      }
    }

    requestAnimationFrame(animar);
  };


  // =========================================================
  // CREAR / ACTUALIZAR MARCADOR
  // =========================================================

  const crearOActualizarMarcador = (
    id,
    lat,
    lng,
    nombre,
    auto,
    sketchfabId,
    asientos
  ) => {
    if (
      !lat ||
      !lng ||
      parseFloat(lat) === 0.0
    ) {
      return;
    }

    const iframe3D = sketchfabId
      ? `
        <iframe
          src="https://sketchfab.com/models/${sketchfabId}/embed?autostart=1&internal=1"
          style="
            width:100%;
            height:160px;
            margin-top:12px;
            border-radius:14px;
            border:1px solid #e2e8f0;
          "
          frameborder="0"
          allow="autoplay; fullscreen; xr-spatial-tracking"
        ></iframe>
      `
      : '';


    const popupContent = `
      <div
        style="
          width:260px;
          padding:4px;
          font-family:Inter,system-ui,sans-serif;
          color:#0f172a;
        "
      >

        <div
          style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:10px;
          "
        >

          <div>
            <div
              style="
                font-size:10px;
                text-transform:uppercase;
                letter-spacing:.12em;
                color:#94a3b8;
                margin-bottom:3px;
              "
            >
              Conductor
            </div>

            <div
              style="
                font-size:15px;
                font-weight:700;
                color:#0f172a;
              "
            >
              ${nombre}
            </div>
          </div>

          <div
            style="
              width:32px;
              height:32px;
              border-radius:50%;
              background:#fef3c7;
              display:flex;
              align-items:center;
              justify-content:center;
              font-size:15px;
            "
          >
            🚕
          </div>

        </div>


        <div
          style="
            padding:12px;
            background:#f8fafc;
            border-radius:12px;
            margin-bottom:8px;
          "
        >

          <div
            style="
              font-size:10px;
              color:#94a3b8;
              margin-bottom:3px;
            "
          >
            Vehículo
          </div>

          <div
            style="
              font-size:13px;
              font-weight:600;
              color:#334155;
            "
          >
            ${auto}
          </div>

        </div>


        <div
          style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            font-size:12px;
          "
        >

          <span style="color:#64748b;">
            Asientos libres
          </span>

          <strong style="color:#0f172a;">
            ${asientos}
          </strong>

        </div>

        ${iframe3D}

      </div>
    `;


    if (markers.current[id]) {

      moverMarcadorFluidamente(
        markers.current[id],
        parseFloat(lat),
        parseFloat(lng)
      );

      markers.current[id]
        .getPopup()
        .setContent(popupContent);

    } else {

      markers.current[id] = L
        .marker(
          [
            parseFloat(lat),
            parseFloat(lng),
          ],
          {
            icon: taxiIcon,
          }
        )
        .addTo(mapInstance.current)
        .bindPopup(popupContent);

    }
  };


  // =========================================================
  // MAPA + WEBSOCKET
  // =========================================================

  useEffect(() => {

    if (!mapInstance.current) {

      mapInstance.current = L
        .map(mapRef.current, {
          zoomControl: false,
        })
        .setView(
          [19.4326, -99.1332],
          13
        );


      L.control
        .zoom({
          position: 'bottomright',
        })
        .addTo(mapInstance.current);


      L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        {
          attribution:
            '© OpenStreetMap © CARTO',
        }
      ).addTo(mapInstance.current);

    }


    // =======================================================
    // CARGA INICIAL
    // =======================================================

    apiFetch('/api/v1/admin/choferes/mapa/')
      .then((res) => res.json())
      .then((data) => {

        setChoferes(
          data.choferes || []
        );

        data.choferes?.forEach((c) => {

          crearOActualizarMarcador(
            c.chofer_id,
            c.lat,
            c.lng,
            c.nombre,
            c.vehiculo,
            c.sketchfab_id,
            c.asientos_disponibles
          );

        });

      })
      .catch(() => {
        console.error(
          'No se pudieron cargar los conductores.'
        );
      });


    // =======================================================
    // WEBSOCKET
    // =======================================================

    const wsScheme =
      window.location.protocol === 'https:'
        ? 'wss'
        : 'ws';

    const socket = new WebSocket(
      `${wsScheme}://${window.location.host}/ws/tracking/`
    );


    socket.onmessage = (e) => {

      const data = JSON.parse(e.data);

      crearOActualizarMarcador(
        data.chofer_id,
        data.lat,
        data.lng,
        data.nombre || 'Chofer en Ruta',
        data.vehiculo || 'Vehículo Activo',
        data.sketchfab_id || '',
        data.asientos_disponibles ?? 0
      );


      // Actualizar lista
      setChoferes((prev) => {

        const existe = prev.some(
          (c) =>
            c.chofer_id === data.chofer_id
        );


        if (!existe) {

          return [
            ...prev,
            {
              chofer_id: data.chofer_id,
              nombre:
                data.nombre ||
                'Chofer en Ruta',
              vehiculo:
                data.vehiculo ||
                'Vehículo Activo',
              asientos_disponibles:
                data.asientos_disponibles ?? 0,
              estado: 'En Ruta',
            },
          ];

        }


        return prev.map((c) =>
          c.chofer_id === data.chofer_id
            ? {
                ...c,
                lat: data.lat,
                lng: data.lng,
                asientos_disponibles:
                  data.asientos_disponibles ??
                  c.asientos_disponibles,
                estado:
                  data.estado ||
                  c.estado,
              }
            : c
        );

      });

    };


    return () => {
      socket.close();

      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }

    };

  }, []);


  // =========================================================
  // SELECCIONAR CONDUCTOR
  // =========================================================

  const seleccionarConductor = (chofer) => {

    setSelectedDriver(
      chofer.chofer_id
    );

    const marker =
      markers.current[
        chofer.chofer_id
      ];


    if (
      marker &&
      mapInstance.current
    ) {

      mapInstance.current.flyTo(
        marker.getLatLng(),
        16,
        {
          duration: 0.8,
        }
      );

      marker.openPopup();

    }

  };


  // =========================================================
  // UI
  // =========================================================

  return (

    <div className="
      min-h-screen
      w-full
      bg-slate-50
      text-slate-900
      flex
      flex-col
    ">


      {/* =====================================================
          HEADER
      ====================================================== */}

      <header className="
        w-full
        h-16
        sm:h-20
        bg-white
        border-b
        border-slate-200
        flex
        items-center
        justify-between
        px-5
        sm:px-8
        lg:px-10
        xl:px-14
        shrink-0
      ">


        {/* Logo */}

        <div className="
          flex
          items-center
          gap-3
        ">

          <div className="
            w-9
            h-9
            sm:w-10
            sm:h-10
            rounded-xl
            bg-slate-950
            flex
            items-center
            justify-center
          ">

            <svg
              className="w-5 h-5 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >

              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.8"
                d="M8 17h8M6 17h-.5A1.5 1.5 0 014 15.5v-5A1.5 1.5 0 015.5 9H7l1.5-3h7L17 9h1.5A1.5 1.5 0 0120 10.5v5a1.5 1.5 0 01-1.5 1.5H18"
              />

            </svg>

          </div>


          <div>

            <p className="
              text-base
              sm:text-lg
              font-bold
              tracking-tight
            ">
              CentralTaxi
            </p>

            <p className="
              hidden
              sm:block
              text-[10px]
              uppercase
              tracking-widest
              text-slate-400
            ">
              Panel administrativo
            </p>

          </div>

        </div>


        {/* Estado */}

        <div className="
          flex
          items-center
          gap-2
          bg-emerald-50
          border
          border-emerald-100
          px-3
          py-1.5
          rounded-full
        ">

          <span className="
            w-2
            h-2
            rounded-full
            bg-emerald-500
            animate-pulse
          "></span>

          <span className="
            text-xs
            font-semibold
            text-emerald-700
          ">
            Sistema operativo
          </span>

        </div>

      </header>



      {/* =====================================================
          CONTENIDO PRINCIPAL
      ====================================================== */}

      <main className="
        flex-1
        w-full
        p-4
        sm:p-5
        lg:p-6
        xl:p-8
        overflow-hidden
      ">


        <div className="
          w-full
          h-full
          min-h-[calc(100vh-112px)]
          grid
          grid-cols-1
          lg:grid-cols-12
          gap-4
          lg:gap-5
        ">


          {/* =================================================
              PANEL DE VEHÍCULOS
          ================================================== */}

          <aside className="
            lg:col-span-4
            xl:col-span-3
            bg-white
            rounded-3xl
            border
            border-slate-200
            flex
            flex-col
            overflow-hidden
            min-h-[420px]
            lg:min-h-0
          ">


            {/* Cabecera */}

            <div className="
              p-5
              sm:p-6
              border-b
              border-slate-100
              shrink-0
            ">

              <div className="
                flex
                items-start
                justify-between
                gap-4
              ">

                <div>

                  <p className="
                    text-[10px]
                    uppercase
                    tracking-[0.15em]
                    font-semibold
                    text-slate-400
                    mb-1
                  ">
                    Operaciones
                  </p>

                  <h1 className="
                    text-xl
                    sm:text-2xl
                    font-bold
                    tracking-tight
                    text-slate-950
                  ">
                    Vehículos
                  </h1>

                </div>


                {/* Contador */}

                <div className="
                  w-11
                  h-11
                  rounded-2xl
                  bg-slate-950
                  text-white
                  flex
                  items-center
                  justify-center
                  text-sm
                  font-bold
                ">
                  {choferes.length}
                </div>

              </div>


              <div className="
                mt-4
                flex
                items-center
                gap-2
                text-xs
                text-slate-400
              ">

                <span className="
                  w-2
                  h-2
                  rounded-full
                  bg-emerald-500
                "></span>

                Conductores activos en tiempo real

              </div>

            </div>


            {/* Lista */}

            <div className="
              flex-1
              overflow-y-auto
              p-4
              sm:p-5
              space-y-2.5
            ">

              {choferes.length > 0 ? (

                choferes.map((c) => {

                  const seleccionado =
                    selectedDriver ===
                    c.chofer_id;

                  const enRuta =
                    c.estado === 'En Ruta';


                  return (

                    <button
                      key={c.chofer_id}
                      type="button"
                      onClick={() =>
                        seleccionarConductor(c)
                      }
                      className={`
                        w-full
                        text-left
                        p-4
                        rounded-2xl
                        border
                        transition-all
                        cursor-pointer
                        ${
                          seleccionado
                            ? 'bg-slate-950 border-slate-950 text-white shadow-md'
                            : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                        }
                      `}
                    >

                      <div className="
                        flex
                        items-center
                        justify-between
                        gap-3
                      ">


                        {/* Avatar */}

                        <div className="
                          flex
                          items-center
                          gap-3
                          min-w-0
                        ">

                          <div
                            className={`
                              w-10
                              h-10
                              shrink-0
                              rounded-xl
                              flex
                              items-center
                              justify-center
                              text-sm
                              ${
                                seleccionado
                                  ? 'bg-white/10 text-white'
                                  : 'bg-amber-50 text-amber-600'
                              }
                            `}
                          >

                            🚕

                          </div>


                          <div className="min-w-0">

                            <p
                              className={`
                                font-semibold
                                text-sm
                                truncate
                                ${
                                  seleccionado
                                    ? 'text-white'
                                    : 'text-slate-900'
                                }
                              `}
                            >
                              {c.nombre}
                            </p>

                            <p
                              className={`
                                text-xs
                                truncate
                                mt-0.5
                                ${
                                  seleccionado
                                    ? 'text-slate-400'
                                    : 'text-slate-500'
                                }
                              `}
                            >
                              {c.vehiculo}
                            </p>

                          </div>

                        </div>


                        {/* Estado */}

                        <span
                          className={`
                            shrink-0
                            w-2
                            h-2
                            rounded-full
                            ${
                              enRuta
                                ? 'bg-emerald-500'
                                : 'bg-amber-500'
                            }
                          `}
                        ></span>

                      </div>


                      {/* Información */}

                      <div className="
                        mt-4
                        flex
                        items-center
                        justify-between
                      ">

                        <span
                          className={`
                            text-[10px]
                            uppercase
                            tracking-wider
                            font-semibold
                            ${
                              seleccionado
                                ? 'text-slate-400'
                                : enRuta
                                ? 'text-emerald-600'
                                : 'text-amber-600'
                            }
                          `}
                        >
                          {c.estado}
                        </span>


                        <span
                          className={`
                            text-xs
                            ${
                              seleccionado
                                ? 'text-slate-400'
                                : 'text-slate-400'
                            }
                          `}
                        >
                          <b
                            className={
                              seleccionado
                                ? 'text-white'
                                : 'text-slate-700'
                            }
                          >
                            {c.asientos_disponibles}
                          </b>{' '}
                          asientos libres
                        </span>

                      </div>

                    </button>

                  );

                })

              ) : (

                <div className="
                  h-full
                  min-h-[250px]
                  flex
                  flex-col
                  items-center
                  justify-center
                  text-center
                  px-6
                ">

                  <div className="
                    w-14
                    h-14
                    rounded-2xl
                    bg-slate-50
                    flex
                    items-center
                    justify-center
                    text-xl
                    mb-4
                  ">
                    🚕
                  </div>

                  <p className="
                    text-sm
                    font-semibold
                    text-slate-700
                  ">
                    No hay vehículos activos
                  </p>

                  <p className="
                    text-xs
                    text-slate-400
                    mt-1
                    max-w-xs
                    leading-relaxed
                  ">
                    Los vehículos conectados aparecerán
                    aquí automáticamente.
                  </p>

                </div>

              )}

            </div>

          </aside>



          {/* =================================================
              MAPA
          ================================================== */}

          <section className="
            lg:col-span-8
            xl:col-span-9
            relative
            min-h-[500px]
            lg:min-h-0
            bg-white
            rounded-3xl
            border
            border-slate-200
            overflow-hidden
          ">


            {/* Header flotante del mapa */}

            <div className="
              absolute
              top-4
              left-4
              sm:top-5
              sm:left-5
              z-[500]
              bg-white/95
              backdrop-blur-sm
              rounded-2xl
              border
              border-slate-200
              shadow-sm
              px-4
              py-3
            ">

              <div className="
                flex
                items-center
                gap-3
              ">

                <div className="
                  w-9
                  h-9
                  rounded-xl
                  bg-amber-50
                  flex
                  items-center
                  justify-center
                ">
                  📍
                </div>

                <div>

                  <p className="
                    text-xs
                    font-bold
                    text-slate-900
                  ">
                    Seguimiento en vivo
                  </p>

                  <p className="
                    text-[10px]
                    text-slate-400
                    mt-0.5
                  ">
                    Ubicación de la flota
                  </p>

                </div>

              </div>

            </div>


            {/* Contador flotante */}

            <div className="
              absolute
              top-4
              right-4
              sm:top-5
              sm:right-5
              z-[500]
              bg-white/95
              backdrop-blur-sm
              rounded-full
              border
              border-slate-200
              shadow-sm
              px-3
              py-2
              flex
              items-center
              gap-2
            ">

              <span className="
                w-2
                h-2
                rounded-full
                bg-emerald-500
              "></span>

              <span className="
                text-xs
                font-semibold
                text-slate-700
              ">
                {choferes.length} activos
              </span>

            </div>


            {/* Leaflet */}

            <div
              ref={mapRef}
              className="
                absolute
                inset-0
                z-0
              "
            />

          </section>

        </div>

      </main>

    </div>

  );
}