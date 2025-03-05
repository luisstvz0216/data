import aiohttp
import asyncio
import re
import sys
from aiohttp import web

# URL donde se obtienen las credenciales
INFO_URL = "https://raw.githubusercontent.com/luisstvz0216/data/refs/heads/main/infos.txt"

# URL base para construir los enlaces remotos
BASE_DOWNLOAD_URL = "http://medisur.sld.cu/index.php/medisur/author/download/"

# Headers generales para las peticiones
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

remote_session = None
REMOTE_HOST = None

async def fetch_info():
    """Descarga el archivo de credenciales y extrae HOST, USER y PASSWORD."""
    async with aiohttp.ClientSession() as session:
        async with session.get(INFO_URL, headers=HEADERS, ssl=False) as response:
            if response.status != 200:
                print("Error al obtener la información de inicio de sesión.")
                return None
            text = await response.text()
            host_match = re.search(r'HOST\s*=\s*[\'"]([^\'"]+)[\'"]', text)
            user_match = re.search(r'USER\s*=\s*[\'"]([^\'"]+)[\'"]', text)
            password_match = re.search(r'PASSWORD\s*=\s*[\'"]([^\'"]+)[\'"]', text)
            if not (host_match and user_match and password_match):
                print("No se encontraron todas las credenciales en el archivo info.py.")
                return None
            return host_match.group(1), user_match.group(1), password_match.group(1)

async def login_remote(app):
    """En el startup del servidor se inicia sesión en el servidor remoto y se guarda la sesión."""
    global remote_session, REMOTE_HOST
   # credentials = await fetch_info()
   # if credentials is None:
     #   print("No se pudieron obtener credenciales, abortando.")
     #   return
   # host, user, password = credentials
    user = "qwqjuzlj"
    password = "qwqjuzlj@telegmail.com"
    host = "http://medisur.sld.cu/index.php/medisur"
    REMOTE_HOST = host
    login_url = f"{host}/login/signIn"
    remote_session = aiohttp.ClientSession()
    data = {
        "source": "",
        "username": user,
        "password": password,
        "remember": "1"
    }
    async with remote_session.post(login_url, data=data, headers=HEADERS, ssl=False) as response:
        text = await response.text(encoding='utf-8', errors='replace')
        if "deshabilitada" in text:
            print("**Cuenta de la Nube Deshabilitada**")
        elif "Iniciar sesión" in text:
            print("**Datos Erróneos de La Nube**")
        else:
            print("**~~VPN Stvz Establecida~~**")
    app["remote_session"] = remote_session

def construct_remote_url(identifier: str) -> str:
    """
    Construye la URL remota a partir de un identificador en formato 'parte1-parte2'
    de forma que quede: BASE_DOWNLOAD_URL + "parte1/parte2"
    """
    parts = identifier.split("-")
    if len(parts) != 2:
        return BASE_DOWNLOAD_URL + identifier
    first, second = parts
    return BASE_DOWNLOAD_URL + f"{first}/{second}"

async def stream_and_extract(remote_sess, url: str, resp):
    """
    Descarga la imagen falsa en modo streaming, descarta el header PNG y el chunk IHDR,
    y escribe en el stream de respuesta los bytes del chunk real a medida que se reciben.
    """
    async with remote_sess.get(url, headers=HEADERS, ssl=False) as remote_resp:
        if remote_resp.status != 200:
            error_msg = f"\nError al descargar {url}\n"
            try:
                await resp.write(error_msg.encode())
            except aiohttp.client_exceptions.ClientConnectionResetError:
                print("La descarga se ha cerrado inesperadamente (conexión cerrada).")
            return 0
        
        # Constantes conocidas del formato PNG falso:
        png_header = b'\x89PNG\r\n\x1a\n'
        ihdr_chunk = b'\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        iend_chunk = b'\x00\x00\x00\x00IEND\xaeB`\x82'
        
        header_len = len(png_header) + len(ihdr_chunk)
        try:
            # Leer y descartar la cabecera completa (header + IHDR)
            await remote_resp.content.readexactly(header_len)
        except Exception as e:
            error_msg = f"\nError al leer la cabecera de {url}: {e}\n"
            try:
                await resp.write(error_msg.encode())
            except aiohttp.client_exceptions.ClientConnectionResetError:
                print("La descarga se ha cerrado inesperadamente (conexión cerrada).")
            return 0
        
        buffer = b""
        bytes_written = 0
        
        try:
            # Leer en bloques pequeños y detectar el chunk IEND para finalizar
            async for chunk in remote_resp.content.iter_chunked(1024):
                buffer += chunk
                # Si se detecta el chunk IEND, escribir lo que hay antes y finalizar
                if iend_chunk in buffer:
                    index = buffer.index(iend_chunk)
                    data_to_write = buffer[:index]
                    try:
                        await resp.write(data_to_write)
                    except aiohttp.client_exceptions.ClientConnectionResetError:
                        print("La descarga se ha cerrado inesperadamente (conexión cerrada).")
                        return bytes_written
                    bytes_written += len(data_to_write)
                    return bytes_written
                else:
                    # Escribir todo excepto los últimos bytes que pueden contener parte de IEND
                    if len(buffer) > len(iend_chunk):
                        to_write = buffer[:-len(iend_chunk)]
                        try:
                            await resp.write(to_write)
                        except aiohttp.client_exceptions.ClientConnectionResetError:
                            print("La descarga se ha cerrado inesperadamente (conexión cerrada).")
                            return bytes_written
                        bytes_written += len(to_write)
                        buffer = buffer[-len(iend_chunk):]
            return bytes_written
        except aiohttp.client_exceptions.ClientConnectionResetError:
            print("La descarga se ha cerrado inesperadamente (conexión cerrada).")
            return bytes_written

async def handle_download(request):
    """
    Handler para la descarga.
    La URL debe tener la forma:
      /{tamaño_en_MB}/{id1}/{id2}/.../{nombrearchivo}
    
    Ejemplo:
      http://127.0.0.1:8080/2.3879594802856445/47295-549498/47296-549499/idm.v6.41.build.20.crack.zip
    
    Se itera sobre cada identificador para construir la URL remota, se extrae
    el contenido real en streaming y se escribe inmediatamente en la respuesta.
    """
    path_parts = request.path.strip("/").split("/")
    if len(path_parts) < 2:
        return web.Response(text="URL inválida", status=400)
    
    try:
        file_size_mb = float(path_parts[0])
    except ValueError:
        return web.Response(text="Tamaño inválido", status=400)
    expected_size = int(file_size_mb * 1024 * 1024)
    
    filename = path_parts[-1]
    download_ids = path_parts[1:-1]
    if not download_ids:
        return web.Response(text="No hay enlaces de descarga", status=400)
    
    remote_urls = [construct_remote_url(identifier) for identifier in download_ids]
    
    headers = {
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Length': str(expected_size)
    }
    resp = web.StreamResponse(status=200, headers=headers)
    await resp.prepare(request)
    
    total_extracted = 0
    remote_sess = request.app["remote_session"]

    # Procesar cada enlace remoto en streaming
    for url in remote_urls:
        bytes_written = await stream_and_extract(remote_sess, url, resp)
        total_extracted += bytes_written
    
    await resp.write_eof()
    return resp

async def on_shutdown(app):
    """Cierra la sesión remota al detener el servidor."""
    global remote_session
    if remote_session:
        await remote_session.close()

app = web.Application()
app.add_routes([web.get('/{tail:.*}', handle_download)])
app.on_startup.append(login_remote)
app.on_shutdown.append(on_shutdown)

if __name__ == '__main__':
    web.run_app(app, host="127.0.0.1", port=8080)
