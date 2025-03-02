import os
import asyncio
import aiohttp
from aiohttp import web
from tqdm import tqdm
import re
import logging

logging.basicConfig(level=logging.INFO)

# Funci贸n para extraer el contenido real de un archivo camuflajeado en una imagen PNG
def extraer_contenido_imagen(image_content: bytes) -> bytes:
    png_header = b'\x89PNG\r\n\x1a\n'
    ihdr_chunk = b'\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
    iend_chunk = b'\x00\x00\x00\x00IEND\xaeB`\x82'
    
    start_data = len(png_header) + len(ihdr_chunk)
    end_data = len(image_content) - len(iend_chunk)
    
    if start_data >= end_data:
        raise ValueError("No se encontraron archivos incrustados")
    
    return image_content[start_data:end_data]

async def iniciar_sesion(session, host, user, pasw):
    """Inicia sesi贸n y devuelve la cookie de sesi贸n."""
    headers = {
  #      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8,gl;q=0.7",
        #"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }

    data = {
        "source": "",
        "username": user,
        "password": pasw,
        "remember": "1"
    }

    try:
        print("**Iniciando sesi贸n...**")
        async with session.post(host + '/login/signIn', data=data, headers=headers, ssl=False) as response:
            if response.status != 200:
                print(f"Error al iniciar sesi贸n. C贸digo de estado: {response.status}")
                return None

            cookies = response.cookies
            print("Sesi贸n iniciada con 茅xito.")
            return cookies

    except Exception as e:
        print(f"Error al iniciar sesi贸n: {e}")
        return None

async def descargar_chunk(session, enlace_chunk, i, total_chunks, response, barra_progreso, cookies):
    """Descarga un chunk camuflajeado, extrae el contenido real y lo transmite en streaming mientras se actualiza la barra de progreso."""
    intentos = 0
    max_intentos = 10
    while intentos < max_intentos:
        try:
            headers = {
           #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8,gl;q=0.7",
         #       "Cookie": f'OJSSID={cookies["OJSSID"].value}',
                "Host": "medisur.sld.cu",
                "Proxy-Connection": "keep-alive",
           #     "Referer": "http://medisur.sld.cu/index.php/medisur/author/submit/5?articleId=46410",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            }

            url_chunk = f"http://medisur.sld.cu/index.php/medisur/author/download/{enlace_chunk}"
            print(f"Descargando chunk {i+1} de {total_chunks} desde: {url_chunk}")

            async with session.get(url_chunk, headers=headers, ssl=False) as respuesta:
                if respuesta.status != 200:
                    print(f"Error al descargar chunk {i+1}. Status code: {respuesta.status}")
                    return False
                respuesta.raise_for_status()

                # Descargamos el contenido completo del archivo camuflajeado
                chunk_camuflado = await respuesta.read()

                # Extraemos el contenido real del chunk
                try:
                    chunk_real = extraer_contenido_imagen(chunk_camuflado)
                except ValueError as ve:
                    print(f"Error extrayendo chunk {i+1}: {ve}")
                    return False

                # Transmitimos el chunk real
                await response.write(chunk_real)
                barra_progreso.update(len(chunk_real))
                print(f"Chunk {i+1} transmitido.")
                return True

        except (aiohttp.ClientError, Exception) as e:
            intentos += 1
            print(f"Error en chunk {i+1} (Intento {intentos}/{max_intentos}): {e}")
            if intentos < max_intentos:
                await asyncio.sleep(2 ** intentos)  # Espera exponencial
            else:
                print(f"Error persistente en chunk {i+1}.")
                return False

async def handle_request(request):
    """
    URL esperado: /tama帽o/chunk1/chunk2/.../filename
    Ejemplo: /10/chunk-1/chunk-2/archivo.zip   (donde 10 es el tama帽o en MB)
    """
    path = request.path.strip('/')
    if not path:
        return web.Response(text="URL inv谩lida. Formato: /tama帽o/chunk1/chunk2/.../filename")

    parts = path.split('/')
    if len(parts) < 3:
        return web.Response(text="URL incompleta.", status=400)

    try:
        # Convertimos el tama帽o de MB a bytes
        tamano_total = float(parts[0]) * 1024 * 1024
    except ValueError:
        return web.Response(text="El primer par谩metro debe ser el tama帽o total en MB.", status=400)

    chunks = parts[1:-1]
    filename = parts[-1]

    # Reemplaza '-' por '/' en cada chunk y ord茅nalos si el nombre termina en d铆gitos
    enlaces_chunks = [chunk.replace('-', '/') for chunk in chunks]
    try:
        enlaces_chunks = sorted(enlaces_chunks, key=lambda x: int(re.search(r'(\d+)$', x).group(1)))
    except Exception:
        pass

    host = "http://medisur.sld.cu/index.php/medisur"
    user = "ondnvdor"  # Reemplaza con el usuario real
    pasw = "ondnvdor@telegmail.com"  # Reemplaza con la contrase帽a real

    async with aiohttp.ClientSession() as session:
        cookies = await iniciar_sesion(session, host, user, pasw)
        if not cookies:
            return web.Response(text="Error al iniciar sesi贸n.", status=500)

        # Preparamos la respuesta para streaming, se env铆a el Content-Length con el tama帽o total
        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Length': str(int(tamano_total))
            }
        )
        await response.prepare(request)

        try:
            with tqdm(total=tamano_total, unit='B', unit_scale=True, desc="Descargando") as barra_progreso:
                for i, enlace in enumerate(enlaces_chunks):
                    exito = await descargar_chunk(session, enlace, i, len(enlaces_chunks), response, barra_progreso, cookies)
                    if not exito:
                        await response.write_eof()
                        return response
                await response.write_eof()

        except Exception as e:
            logging.error(f"Error durante la transmisi贸n: {e}")
            return web.Response(text=f"Error: {str(e)}", status=500)

        return response

app = web.Application()
app.router.add_get('/{path:.*}', handle_request)

if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=8080)
              
