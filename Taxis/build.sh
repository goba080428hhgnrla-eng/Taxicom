#!/usr/bin/env bash
set -o errexit

# 1. Instalar dependencias de Python
pip install -r requirements.txt

# 2. Subir un nivel para entrar a frontend y compilar React
cd ../frontend
npm install
npm run build
cd ../Taxis

# 3. Aplicar migraciones y recolectar estáticos
python manage.py migrate
python manage.py collectstatic --no-input