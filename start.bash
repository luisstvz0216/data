#!/bin/bash
# Script para descargar y ejecutar el código directamente desde GitHub en Pydroid 3

# URL del código fuente y dependencias (reemplázalas con las URL correctas de tu repo)
RAW_APP_URL="https://raw.githubusercontent.com/luisstvz0216/data/refs/heads/main/app.py"
RAW_REQ_URL="https://raw.githubusercontent.com/luisstvz0216/data/refs/heads/main/requirements.txt"

# Nombre de los archivos locales
APP_FILE="app.py"
REQ_FILE="requirements.txt"

# Descargar app.py y requirements.txt
echo "Descargando archivos desde GitHub..."
wget -O "$APP_FILE" "$RAW_APP_URL" || { echo "Error descargando app.py"; exit 1; }
wget -O "$REQ_FILE" "$RAW_REQ_URL" || { echo "Error descargando requirements.txt"; exit 1; }

# Instalar dependencias
echo "Instalando dependencias..."
pip install -r "$REQ_FILE" || { echo "Error instalando dependencias"; exit 1; }

# Ejecutar el script de Python
echo "Ejecutando el script..."
python3 "$APP_FILE"
