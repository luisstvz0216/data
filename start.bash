#!/bin/bash
# Script para clonar el repositorio, instalar dependencias y ejecutar el script de Python en Pydroid 3

# URL de tu repositorio en GitHub (reemplaza con tu URL real)
REPO_URL="https://github.com/tu_usuario/mi-proyecto.git"

# Nombre del directorio que se creará al clonar el repositorio
DIR="mi-proyecto"

# Clonar el repositorio o actualizarlo si ya existe
if [ -d "$DIR" ]; then
    echo "El repositorio ya existe, actualizando..."
    cd "$DIR" || exit 1
    git pull || { echo "Error actualizando el repositorio"; exit 1; }
else
    echo "Clonando repositorio desde $REPO_URL..."
    git clone "$REPO_URL" || { echo "Error clonando el repositorio"; exit 1; }
    cd "$DIR" || exit 1
fi

# Instalar las dependencias
echo "Instalando dependencias..."
pip install -r requirements.txt || { echo "Error instalando dependencias"; exit 1; }

# Ejecutar el script de Python
echo "Ejecutando el script de Python..."
python app.py
