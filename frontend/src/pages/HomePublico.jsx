import React from 'react';
import { Link } from 'react-router-dom';

export default function HomePublico() {
  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-white text-slate-900 flex flex-col">

      {/* =========================
          NAVBAR
      ========================== */}
      <nav className="w-full border-b border-slate-100 bg-white">
        <div className="max-w-7xl mx-auto px-5 sm:px-6 lg:px-10 h-16 sm:h-20 flex items-center justify-between">

          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-2.5"
          >
            <div className="w-8 h-8 sm:w-9 sm:h-9 bg-slate-950 rounded-lg flex items-center justify-center">
              <svg
                className="w-4 h-4 sm:w-5 sm:h-5 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M8 17h8M6 17h-.5A1.5 1.5 0 014 15.5v-5A1.5 1.5 0 015.5 9H7l1.5-3h7L17 9h1.5A1.5 1.5 0 0120 10.5v5a1.5 1.5 0 01-1.5 1.5H18M7 13h.01M17 13h.01"
                />
              </svg>
            </div>

            <span className="text-lg sm:text-xl font-bold tracking-tight">
              CentralTaxi
            </span>
          </Link>


          {/* Navegación */}
          <div className="flex items-center gap-3 sm:gap-6">

            <span className="hidden lg:block text-sm text-slate-500">
              Servicio seguro y confiable
            </span>

            <Link
              to="/login"
              className="
                bg-slate-950
                text-white
                px-4 sm:px-5
                py-2 sm:py-2.5
                rounded-full
                text-xs sm:text-sm
                font-semibold
                whitespace-nowrap
                hover:bg-slate-800
                transition-colors
              "
            >
              Ingresar al Panel
            </Link>

          </div>

        </div>
      </nav>


      {/* =========================
          HERO
      ========================== */}
      <main className="flex-1">

        <section className="max-w-7xl mx-auto px-5 sm:px-6 lg:px-10">

          <div className="
            min-h-[calc(100vh-136px)]
            flex
            items-center
          ">

            <div className="
              w-full
              grid
              grid-cols-1
              lg:grid-cols-2
              gap-12
              lg:gap-20
              xl:gap-28
              items-center
              py-14
              sm:py-20
              lg:py-24
            ">


              {/* =========================
                  CONTENIDO
              ========================== */}
              <div className="w-full max-w-xl mx-auto lg:mx-0 text-center lg:text-left">

                {/* Label */}
                <div className="
                  flex
                  items-center
                  justify-center
                  lg:justify-start
                  gap-2
                  mb-6
                  sm:mb-8
                ">

                  <span className="w-2 h-2 rounded-full bg-amber-500"></span>

                  <span className="
                    text-[10px]
                    sm:text-xs
                    font-semibold
                    uppercase
                    tracking-[0.16em]
                    text-slate-500
                  ">
                    Plataforma de movilidad
                  </span>

                </div>


                {/* Título */}
                <h1 className="
                  text-[42px]
                  leading-[1.05]
                  sm:text-5xl
                  sm:leading-[1.02]
                  md:text-6xl
                  lg:text-7xl
                  font-bold
                  tracking-[-0.045em]
                  text-slate-950
                ">

                  El viaje que
                  <br />

                  mereces.

                </h1>


                <div className="mt-1">

                  <span className="
                    text-[42px]
                    leading-[1.05]
                    sm:text-5xl
                    md:text-6xl
                    lg:text-7xl
                    font-bold
                    tracking-[-0.045em]
                    text-amber-500
                  ">
                    Seguro.
                  </span>

                </div>


                {/* Descripción */}
                <p className="
                  mt-6
                  sm:mt-8
                  text-base
                  sm:text-lg
                  md:text-xl
                  leading-relaxed
                  text-slate-500
                  max-w-lg
                  mx-auto
                  lg:mx-0
                ">
                  Viaja con confianza. Rastreo en tiempo real,
                  choferes certificados y un servicio pensado
                  para que llegues a tu destino.
                </p>


                {/* CTA */}
                <div className="
                  mt-8
                  sm:mt-10
                  flex
                  flex-col
                  sm:flex-row
                  gap-3
                  justify-center
                  lg:justify-start
                ">

                  <Link
                    to="/login"
                    className="
                      inline-flex
                      items-center
                      justify-center
                      gap-3
                      bg-slate-950
                      text-white
                      w-full
                      sm:w-auto
                      px-7
                      py-4
                      rounded-full
                      text-sm
                      font-semibold
                      hover:bg-slate-800
                      transition-all
                      group
                    "
                  >

                    Ingresar al panel

                    <svg
                      className="
                        w-4 h-4
                        group-hover:translate-x-1
                        transition-transform
                      "
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M5 12h14m-6-6l6 6-6 6"
                      />
                    </svg>

                  </Link>

                </div>

              </div>


              {/* =========================
                  VISUAL DEL SERVICIO
              ========================== */}
              <div className="
                relative
                w-full
                max-w-xl
                mx-auto
                lg:max-w-none
              ">

                <div className="
                  relative
                  aspect-[4/3]
                  sm:aspect-square
                  lg:aspect-square
                  max-w-[560px]
                  mx-auto
                  lg:ml-auto
                ">

                  {/* Fondo */}
                  <div className="
                    absolute
                    inset-0
                    rounded-[28px]
                    sm:rounded-[40px]
                    bg-slate-50
                  "></div>


                  {/* Círculo decorativo */}
                  <div className="
                    absolute
                    w-40
                    h-40
                    sm:w-64
                    sm:h-64
                    md:w-72
                    md:h-72
                    rounded-full
                    bg-amber-100/70
                    top-8
                    sm:top-12
                    right-4
                    sm:right-8
                  "></div>


                  {/* Tarjeta */}
                  <div className="
                    absolute
                    inset-0
                    flex
                    items-center
                    justify-center
                    p-5
                    sm:p-8
                  ">

                    <div className="
                      relative
                      w-full
                      max-w-[400px]
                    ">

                      {/* Sombra */}
                      <div className="
                        absolute
                        bottom-0
                        left-8
                        right-8
                        h-6
                        bg-slate-300/40
                        blur-2xl
                        rounded-full
                      "></div>


                      {/* Card */}
                      <div className="
                        relative
                        bg-white
                        rounded-[24px]
                        sm:rounded-[32px]
                        border
                        border-slate-200
                        shadow-xl
                        p-5
                        sm:p-7
                      ">

                        {/* Header */}
                        <div className="
                          flex
                          items-center
                          justify-between
                          mb-6
                          sm:mb-8
                        ">

                          <div>

                            <span className="
                              block
                              text-[10px]
                              sm:text-xs
                              uppercase
                              tracking-widest
                              text-slate-400
                            ">
                              Central
                            </span>

                            <span className="
                              text-xl
                              sm:text-2xl
                              font-bold
                              text-slate-950
                            ">
                              Taxi
                            </span>

                          </div>


                          <div className="
                            w-9
                            h-9
                            sm:w-10
                            sm:h-10
                            rounded-full
                            bg-amber-400
                            flex
                            items-center
                            justify-center
                          ">

                            <svg
                              className="w-5 h-5 text-slate-950"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M5 17h14M7 17v-5l2-4h6l2 4v5M8 13h8M8 17v2M16 17v2"
                              />
                            </svg>

                          </div>

                        </div>


                        {/* Ruta */}
                        <div className="space-y-5">

                          {/* Origen */}
                          <div className="flex items-center gap-3 sm:gap-4">

                            <div className="
                              w-2.5
                              h-2.5
                              sm:w-3
                              sm:h-3
                              rounded-full
                              bg-slate-950
                              shrink-0
                            "></div>

                            <div className="
                              flex-1
                              border-b
                              border-dashed
                              border-slate-300
                              pb-4
                            ">

                              <span className="
                                text-[10px]
                                sm:text-xs
                                text-slate-400
                              ">
                                Recogida
                              </span>

                              <p className="
                                text-sm
                                font-semibold
                                mt-1
                              ">
                                Tu ubicación
                              </p>

                            </div>

                          </div>


                          {/* Destino */}
                          <div className="flex items-center gap-3 sm:gap-4">

                            <div className="
                              w-2.5
                              h-2.5
                              sm:w-3
                              sm:h-3
                              rounded-full
                              bg-amber-500
                              shrink-0
                            "></div>

                            <div className="flex-1">

                              <span className="
                                text-[10px]
                                sm:text-xs
                                text-slate-400
                              ">
                                Destino
                              </span>

                              <p className="
                                text-sm
                                font-semibold
                                mt-1
                              ">
                                Tu destino
                              </p>

                            </div>

                          </div>

                        </div>

                      </div>

                    </div>

                  </div>


                  {/* Estado */}
                  <div className="
                    absolute
                    bottom-4
                    left-4
                    sm:bottom-7
                    sm:left-7
                    bg-white
                    rounded-xl
                    sm:rounded-2xl
                    border
                    border-slate-200
                    shadow-lg
                    px-3
                    sm:px-5
                    py-3
                    sm:py-4
                  ">

                    <div className="flex items-center gap-2.5 sm:gap-3">

                      <div className="
                        w-8
                        h-8
                        sm:w-9
                        sm:h-9
                        rounded-full
                        bg-green-50
                        flex
                        items-center
                        justify-center
                      ">

                        <span className="
                          w-2
                          h-2
                          sm:w-2.5
                          sm:h-2.5
                          rounded-full
                          bg-green-500
                        "></span>

                      </div>


                      <div>

                        <p className="
                          text-xs
                          sm:text-sm
                          font-semibold
                          text-slate-900
                        ">
                          Servicio disponible
                        </p>

                        <p className="
                          hidden
                          sm:block
                          text-xs
                          text-slate-400
                          mt-0.5
                        ">
                          Conductores conectados
                        </p>

                      </div>

                    </div>

                  </div>

                </div>

              </div>

            </div>

          </div>


          {/* =========================
              FEATURES
          ========================== */}
          <section className="
            border-t
            border-slate-100
            py-10
            sm:py-12
          ">

            <div className="
              grid
              grid-cols-1
              md:grid-cols-3
              gap-8
              md:gap-10
            ">


              {/* Feature 1 */}
              <div className="flex gap-4">

                <div className="
                  w-10
                  h-10
                  shrink-0
                  rounded-full
                  bg-slate-100
                  flex
                  items-center
                  justify-center
                ">

                  <svg
                    className="w-5 h-5 text-slate-900"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="1.8"
                      d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
                    />
                  </svg>

                </div>

                <div>

                  <h3 className="font-semibold text-slate-900">
                    Viajes seguros
                  </h3>

                  <p className="
                    text-sm
                    text-slate-500
                    mt-1
                    leading-relaxed
                  ">
                    Conductores certificados y seguimiento durante tu viaje.
                  </p>

                </div>

              </div>


              {/* Feature 2 */}
              <div className="flex gap-4">

                <div className="
                  w-10
                  h-10
                  shrink-0
                  rounded-full
                  bg-slate-100
                  flex
                  items-center
                  justify-center
                ">

                  <svg
                    className="w-5 h-5 text-slate-900"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >

                    <circle
                      cx="12"
                      cy="12"
                      r="9"
                      strokeWidth="1.8"
                    />

                    <path
                      strokeLinecap="round"
                      strokeWidth="1.8"
                      d="M12 6v6l4 2"
                    />

                  </svg>

                </div>

                <div>

                  <h3 className="font-semibold text-slate-900">
                    Disponible cuando lo necesitas
                  </h3>

                  <p className="
                    text-sm
                    text-slate-500
                    mt-1
                    leading-relaxed
                  ">
                    Consulta y gestiona tus servicios en tiempo real.
                  </p>

                </div>

              </div>


              {/* Feature 3 */}
              <div className="flex gap-4">

                <div className="
                  w-10
                  h-10
                  shrink-0
                  rounded-full
                  bg-slate-100
                  flex
                  items-center
                  justify-center
                ">

                  <svg
                    className="w-5 h-5 text-slate-900"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >

                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="1.8"
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />

                  </svg>

                </div>

                <div>

                  <h3 className="font-semibold text-slate-900">
                    Simple y confiable
                  </h3>

                  <p className="
                    text-sm
                    text-slate-500
                    mt-1
                    leading-relaxed
                  ">
                    Todo lo que necesitas desde una sola plataforma.
                  </p>

                </div>

              </div>

            </div>

          </section>

        </section>

      </main>


      {/* =========================
          FOOTER
      ========================== */}
      <footer className="border-t border-slate-100 bg-white">

        <div className="
          max-w-7xl
          mx-auto
          px-5
          sm:px-6
          lg:px-10
          py-6
          sm:py-7
        ">

          <div className="
            flex
            flex-col
            sm:flex-row
            items-center
            justify-between
            gap-4
            text-center
            sm:text-left
          ">

            <p className="text-xs text-slate-400">
              © 2026 CentralTaxi. Todos los derechos reservados.
            </p>

            <div className="
              flex
              items-center
              gap-5
              sm:gap-6
              text-xs
              text-slate-400
            ">
              <span>Privacidad</span>
              <span>Términos</span>
              <span>Soporte</span>
            </div>

          </div>

        </div>

      </footer>

    </div>
  );
}