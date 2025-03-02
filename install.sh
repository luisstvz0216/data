#!/bin/bash

   # Actualizar paquetes e instalar dependencias
   pkg update -y
   pkg install python -y
   pip install requests tqdm aiohttp

   # Descargar el script desde GitHub
   curl -L -o mi_script.py https://raw.githubusercontent.com/tu_usuario/tu_repositorio/main/mi_script.py

   # Dar permisos de ejecución al script
   chmod +x mi_script.py

   # Ejecutar el script
   python mi_script.py
