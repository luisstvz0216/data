import os
import requests

# URL del script en GitHub
script_url = "https://raw.githubusercontent.com/luisstvz0216/data/refs/heads/main/vpnv1.py"

# Descargar el script
print("Descargando el script...")
response = requests.get(script_url)
if response.status_code == 200:
    with open("mi_script.py", "wb") as file:
        file.write(response.content)
    print("Script descargado correctamente.")
else:
    print(f"Error al descargar el script. Código de estado: {response.status_code}")
    exit(1)

# Instalar dependencias
print("Instalando dependencias...")
os.system("pip3 install aiohttp tqdm")  # Agrega aquí las dependencias necesarias

# Ejecutar el script
print("Ejecutando el script...")
os.system("python3 vpnv1.py")
