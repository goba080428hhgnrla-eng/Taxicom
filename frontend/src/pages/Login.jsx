import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { guardarSesion, cerrarSesion } from '../api.js'; 

export default function Login() {
  const [formData, setFormData] = useState({
    correo_o_usuario: '',
    password: '',
  });

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError('');
    setLoading(true);

    try {
      const res = await fetch('/api/v1/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await res.json();

      if (!res.ok) {
        const mensaje =
          data.non_field_errors?.[0] ||
          data.detail ||
          'Credenciales inválidas. Verifica tus datos.';

        setError(mensaje);
        return;
      }

      if (!data.usuario?.es_admin) {
        cerrarSesion();
        setError('Acceso denegado. No eres administrador.');
        return;
      }

      guardarSesion(data);
      navigate('/admin');

    } catch (err) {
      setError('Error de conexión con el servidor.');

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-white text-slate-900 flex flex-col">

      {/* =====================================================
          NAVBAR
      ====================================================== */}
      <header className="w-full border-b border-slate-100">

        <div className="
          w-full
          h-16
          sm:h-20
          px-5
          sm:px-8
          lg:px-12
          xl:px-16
          flex
          items-center
          justify-between
        ">

          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-2.5"
          >

            <div className="
              w-8
              h-8
              sm:w-9
              sm:h-9
              rounded-lg
              bg-slate-950
              flex
              items-center
              justify-center
            ">

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

            <span className="
              text-lg
              sm:text-xl
              font-bold
              tracking-tight
            ">
              CentralTaxi
            </span>

          </Link>


          {/* Indicador */}
          <div className="flex items-center gap-2">

            <span className="
              w-2
              h-2
              rounded-full
              bg-amber-500
            "></span>

            <span className="
              hidden
              sm:block
              text-xs
              sm:text-sm
              text-slate-500
            ">
              Panel de administración
            </span>

          </div>

        </div>

      </header>


      {/* =====================================================
          CONTENIDO
      ====================================================== */}
      <main className="flex-1 w-full">

        <div className="
          min-h-[calc(100vh-136px)]
          w-full
          grid
          grid-cols-1
          lg:grid-cols-2
        ">


          {/* =================================================
              FORMULARIO
          ================================================== */}
          <section className="
            w-full
            flex
            items-center
            justify-center
            px-5
            sm:px-8
            lg:px-12
            xl:px-20
            py-12
            sm:py-16
            lg:py-20
          ">

            <div className="
              w-full
              max-w-md
            ">


              {/* Label superior */}
              <div className="
                flex
                items-center
                gap-2
                mb-7
              ">

                <span className="
                  w-2
                  h-2
                  rounded-full
                  bg-amber-500
                "></span>

                <span className="
                  text-[10px]
                  sm:text-xs
                  font-semibold
                  uppercase
                  tracking-[0.16em]
                  text-slate-500
                ">
                  Acceso administrativo
                </span>

              </div>


              {/* Título */}
              <h1 className="
                text-4xl
                sm:text-5xl
                font-bold
                tracking-[-0.04em]
                leading-tight
                text-slate-950
              ">
                Bienvenido
                <br />
                de nuevo.
              </h1>


              <p className="
                mt-4
                text-base
                sm:text-lg
                leading-relaxed
                text-slate-500
                max-w-md
              ">
                Inicia sesión para administrar
                CentralTaxi desde un solo lugar.
              </p>


              {/* =================================================
                  ERROR
              ================================================== */}
              {error && (

                <div className="
                  mt-7
                  p-4
                  bg-red-50
                  border
                  border-red-100
                  rounded-2xl
                  flex
                  items-start
                  gap-3
                ">

                  <div className="
                    w-8
                    h-8
                    shrink-0
                    rounded-full
                    bg-red-100
                    flex
                    items-center
                    justify-center
                  ">

                    <svg
                      className="w-4 h-4 text-red-600"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>

                  </div>

                  <p className="
                    text-sm
                    leading-relaxed
                    text-red-700
                    pt-1
                  ">
                    {error}
                  </p>

                </div>

              )}


              {/* =================================================
                  FORM
              ================================================== */}
              <form
                onSubmit={handleSubmit}
                className="mt-8 space-y-5"
              >


                {/* Usuario */}
                <div>

                  <label
                    htmlFor="correo_o_usuario"
                    className="
                      block
                      text-sm
                      font-semibold
                      text-slate-900
                      mb-2.5
                    "
                  >
                    Usuario o correo electrónico
                  </label>

                  <div className="relative">

                    <div className="
                      absolute
                      left-4
                      top-1/2
                      -translate-y-1/2
                      pointer-events-none
                    ">

                      <svg
                        className="w-5 h-5 text-slate-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="1.8"
                          d="M16 12a4 4 0 10-8 0 4 4 0 008 0z"
                        />

                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="1.8"
                          d="M4 20a8 8 0 0116 0"
                        />
                      </svg>

                    </div>


                    <input
                      id="correo_o_usuario"
                      type="text"
                      required
                      autoComplete="username"
                      placeholder="nombre@ejemplo.com"
                      value={formData.correo_o_usuario}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          correo_o_usuario: e.target.value,
                        })
                      }
                      className="
                        w-full
                        h-14
                        bg-white
                        border
                        border-slate-200
                        rounded-xl
                        pl-12
                        pr-4
                        text-sm
                        text-slate-900
                        placeholder:text-slate-400
                        outline-none
                        transition
                        focus:border-slate-950
                        focus:ring-4
                        focus:ring-slate-950/5
                      "
                    />

                  </div>

                </div>


                {/* Contraseña */}
                <div>

                  <label
                    htmlFor="password"
                    className="
                      block
                      text-sm
                      font-semibold
                      text-slate-900
                      mb-2.5
                    "
                  >
                    Contraseña
                  </label>


                  <div className="relative">

                    <div className="
                      absolute
                      left-4
                      top-1/2
                      -translate-y-1/2
                      pointer-events-none
                    ">

                      <svg
                        className="w-5 h-5 text-slate-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <rect
                          x="4"
                          y="10"
                          width="16"
                          height="11"
                          rx="2"
                          strokeWidth="1.8"
                        />

                        <path
                          strokeLinecap="round"
                          strokeWidth="1.8"
                          d="M8 10V7a4 4 0 118 0v3"
                        />

                      </svg>

                    </div>


                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      autoComplete="current-password"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          password: e.target.value,
                        })
                      }
                      className="
                        w-full
                        h-14
                        bg-white
                        border
                        border-slate-200
                        rounded-xl
                        pl-12
                        pr-12
                        text-sm
                        text-slate-900
                        placeholder:text-slate-400
                        outline-none
                        transition
                        focus:border-slate-950
                        focus:ring-4
                        focus:ring-slate-950/5
                      "
                    />


                    {/* Mostrar contraseña */}
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="
                        absolute
                        right-4
                        top-1/2
                        -translate-y-1/2
                        text-slate-400
                        hover:text-slate-900
                        transition
                      "
                      aria-label={
                        showPassword
                          ? 'Ocultar contraseña'
                          : 'Mostrar contraseña'
                      }
                    >

                      {showPassword ? (

                        <svg
                          className="w-5 h-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="1.8"
                            d="M3 3l18 18"
                          />

                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="1.8"
                            d="M10.6 10.6a2 2 0 002.8 2.8"
                          />

                        </svg>

                      ) : (

                        <svg
                          className="w-5 h-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="1.8"
                            d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"
                          />

                          <circle
                            cx="12"
                            cy="12"
                            r="2.5"
                            strokeWidth="1.8"
                          />

                        </svg>

                      )}

                    </button>

                  </div>

                </div>


                {/* =================================================
                    BOTÓN
                ================================================== */}
                <button
                  type="submit"
                  disabled={loading}
                  className="
                    w-full
                    h-14
                    mt-2
                    bg-slate-950
                    hover:bg-slate-800
                    active:scale-[0.99]
                    disabled:opacity-50
                    disabled:cursor-not-allowed
                    text-white
                    rounded-xl
                    font-semibold
                    text-sm
                    flex
                    items-center
                    justify-center
                    gap-3
                    transition-all
                  "
                >

                  {loading ? (

                    <>
                      <svg
                        className="w-5 h-5 animate-spin"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />

                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                        />
                      </svg>

                      Validando...

                    </>

                  ) : (

                    <>
                      Entrar al sistema

                      <svg
                        className="w-4 h-4"
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
                    </>

                  )}

                </button>

              </form>


              {/* Volver */}
              <div className="
                mt-8
                pt-6
                border-t
                border-slate-100
                text-center
              ">

                <Link
                  to="/"
                  className="
                    inline-flex
                    items-center
                    gap-2
                    text-sm
                    text-slate-500
                    hover:text-slate-950
                    transition
                  "
                >

                  <span>←</span>

                  <span>
                    Volver al sitio principal
                  </span>

                </Link>

              </div>

            </div>

          </section>


          {/* =================================================
              PANEL VISUAL
          ================================================== */}
          <section className="
            hidden
            lg:flex
            relative
            bg-slate-50
            overflow-hidden
            min-h-[calc(100vh-136px)]
            items-center
            justify-center
            px-12
            xl:px-20
          ">


            {/* Decoración */}
            <div className="
              absolute
              w-[500px]
              h-[500px]
              rounded-full
              bg-amber-100/70
              -top-40
              -right-40
            "></div>


            <div className="
              absolute
              w-[400px]
              h-[400px]
              rounded-full
              bg-white
              -bottom-48
              -left-32
            "></div>


            {/* Contenido */}
            <div className="
              relative
              z-10
              w-full
              max-w-xl
            ">


              {/* Logo grande */}
              <div className="
                flex
                items-center
                gap-3
                mb-12
              ">

                <div className="
                  w-12
                  h-12
                  rounded-xl
                  bg-slate-950
                  flex
                  items-center
                  justify-center
                ">

                  <svg
                    className="w-6 h-6 text-white"
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

                <span className="
                  text-2xl
                  font-bold
                  tracking-tight
                ">
                  CentralTaxi
                </span>

              </div>


              {/* Heading */}
              <h2 className="
                text-5xl
                xl:text-6xl
                font-bold
                tracking-[-0.05em]
                leading-[1]
                text-slate-950
              ">
                Todo bajo
                <br />
                control.
              </h2>


              <p className="
                mt-6
                text-lg
                leading-relaxed
                text-slate-500
                max-w-md
              ">
                Administra viajes, conductores y operaciones
                desde una plataforma simple y eficiente.
              </p>


              {/* Mini dashboard */}
              <div className="
                mt-12
                bg-white
                rounded-[28px]
                border
                border-slate-200
                shadow-xl
                p-6
                max-w-md
              ">

                <div className="
                  flex
                  items-center
                  justify-between
                  mb-6
                ">

                  <div>

                    <p className="
                      text-xs
                      text-slate-400
                    ">
                      Estado del servicio
                    </p>

                    <p className="
                      text-lg
                      font-bold
                      text-slate-950
                      mt-1
                    ">
                      Operativo
                    </p>

                  </div>


                  <div className="
                    flex
                    items-center
                    gap-2
                    bg-green-50
                    text-green-700
                    px-3
                    py-1.5
                    rounded-full
                    text-xs
                    font-semibold
                  ">

                    <span className="
                      w-2
                      h-2
                      rounded-full
                      bg-green-500
                    "></span>

                    En línea

                  </div>

                </div>


                <div className="
                  grid
                  grid-cols-2
                  gap-3
                ">

                  <div className="
                    bg-slate-50
                    rounded-xl
                    p-4
                  ">

                    <p className="
                      text-xs
                      text-slate-400
                    ">
                      Viajes hoy
                    </p>

                    <p className="
                      text-2xl
                      font-bold
                      text-slate-950
                      mt-1
                    ">
                      128
                    </p>

                  </div>


                  <div className="
                    bg-slate-50
                    rounded-xl
                    p-4
                  ">

                    <p className="
                      text-xs
                      text-slate-400
                    ">
                      Conductores
                    </p>

                    <p className="
                      text-2xl
                      font-bold
                      text-slate-950
                      mt-1
                    ">
                      42
                    </p>

                  </div>

                </div>

              </div>


              {/* Frase */}
              <div className="
                mt-8
                flex
                items-center
                gap-3
                text-sm
                text-slate-400
              ">

                <span className="
                  w-2
                  h-2
                  rounded-full
                  bg-amber-500
                "></span>

                Gestión simple. Operación eficiente.

              </div>

            </div>

          </section>

        </div>

      </main>


      {/* =====================================================
          FOOTER
      ====================================================== */}
      <footer className="
        w-full
        border-t
        border-slate-100
        bg-white
      ">

        <div className="
          w-full
          px-5
          sm:px-8
          lg:px-12
          xl:px-16
          py-5
        ">

          <div className="
            flex
            flex-col
            sm:flex-row
            items-center
            justify-between
            gap-3
            text-center
            sm:text-left
          ">

            <p className="text-xs text-slate-400">
              © 2026 CentralTaxi. Todos los derechos reservados.
            </p>

            <Link
              to="/"
              className="
                text-xs
                text-slate-400
                hover:text-slate-900
                transition
              "
            >
              Sitio principal
            </Link>

          </div>

        </div>

      </footer>

    </div>
  );
}