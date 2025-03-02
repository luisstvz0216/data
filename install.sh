#!/bin/bash

   # Actualizar paquetes e instalar dependencias
pkg update -y
pkg install python -y
pip install requests tqdm aiohttp

   # Descargar el script desde GitHub
curl -L -o mi_script.py https://github.com/luisstvz0216/data/blob/e843da8c19fd35cb81311873b873f644d67c26ab/vpnv1.py

   # Dar permisos de ejecución al script
chmod +x mi_script.py

   # Ejecutar el script
python mi_script.py
