import requests
import os
import subprocess

# URL del código fuente y dependencias
RAW_APP_URL = "https://raw.githubusercontent.com/luisstvz0216/data/refs/heads/main/app.py"
RAW_REQ_URL = "https://raw.githubusercontent.com/luisstvz0216/data/refs/heads/main/requirements.txt"

# Nombres de los archivos locales
APP_FILE = "app.py"
REQ_FILE = "requirements.txt"

# Descargar app.py
print("Descargando archivos desde GitHub...")
try:
    response = requests.get(RAW_APP_URL)
    with open(APP_FILE, 'w') as f:
        f.write(response.text)
    response = requests.get(RAW_REQ_URL)
    with open(REQ_FILE, 'w') as f:
        f.write(response.text)
except Exception as e:
    print(f"Error descargando archivos: {e}")
    exit(1)

# Instalar dependencias
print("Instalando dependencias...")
os.system(f"pip install -r {REQ_FILE}")

# Ejecutar el script de Python
print("Ejecutando el script...")
os.system(f"python3 {APP_FILE}")
