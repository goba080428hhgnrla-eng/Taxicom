#!/usr/bin/env bash
# Detener la ejecución si ocurre cualquier error
set -o errexit

# 1. Instalar dependencias de Python
pip install -r requirements.txt

# 2. Entrar a la carpeta frontend, instalar paquetes y compilar React
cd frontend
npm install
npm run build
cd ..

# 3. Aplicar migraciones en la Base de Datos de Django
python manage.py migrate

# 4. Recolectar todos los archivos estáticos (incluyendo el build de React)
python manage.py collectstatic --no-input