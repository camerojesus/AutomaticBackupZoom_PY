import os
import requests
import json
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse
import re
import traceback

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configuración: obtener valores de las variables de entorno
ZOOM_ACCOUNT_ID = os.getenv('ZOOM_ACCOUNT_ID')
ZOOM_CLIENT_ID = os.getenv('ZOOM_CLIENT_ID')
ZOOM_CLIENT_SECRET = os.getenv('ZOOM_CLIENT_SECRET')

# Carpeta donde se guardarán las grabaciones
DOWNLOAD_FOLDER = 'D:\\reunioneszoom'

# Variables para el token de acceso y su tiempo de expiración
accessToken = None
tokenExpirationTime = 0

# Función para sanitizar nombres de archivo
def sanitizar_nombre_archivo(nombre_archivo):
    # Reemplazar caracteres no permitidos en nombres de archivo
    nombre_archivo = nombre_archivo.replace('#', '')
    caracteres_invalidos = r'["*:<>?/\\|#&]'
    nombre_sanitizado = re.sub(caracteres_invalidos, '-', nombre_archivo)
    nombre_sanitizado = nombre_sanitizado.replace('_', ' ')
    nombre_sanitizado = re.sub(r'\s+', ' ', nombre_sanitizado)
    nombre_sanitizado = nombre_sanitizado.lstrip()
    nombre_sanitizado = re.sub(r'^[^a-zA-Z0-9]+', '', nombre_sanitizado)
    nombre_sanitizado = nombre_sanitizado.strip().strip('.')

    if len(nombre_sanitizado) > 255:
        extension = Path(nombre_sanitizado).suffix
        nombre_base = Path(nombre_sanitizado).stem
        nombre_sanitizado = nombre_base[:251 - len(extension)] + extension

    return nombre_sanitizado

# Función para registrar errores en un archivo de registro
def log_error(message):
    with open('error_log.txt', 'a') as log_file:
        log_file.write(f'{datetime.datetime.now()}: {message}\n')

# Función para registrar mensajes de ejecución en un archivo de registro
def log_execution(message):
    with open('execution_log.txt', 'a') as log_file:
        log_file.write(f'{datetime.datetime.now()}: {message}\n')

# Función para obtener el token de acceso usando Server-to-Server OAuth
def get_zoom_access_token():
    global accessToken, tokenExpirationTime
    try:
        data = {
            'grant_type': 'account_credentials',
            'account_id': ZOOM_ACCOUNT_ID
        }
        response = requests.post('https://zoom.us/oauth/token',
                                 data=urllib.parse.urlencode(data),
                                 auth=(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET),
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})

        response.raise_for_status()
        response_data = response.json()
        accessToken = response_data['access_token']
        tokenExpirationTime = time.time() + response_data['expires_in']
        log_execution('Token de acceso obtenido exitosamente')
        return accessToken
    except requests.exceptions.RequestException as e:
        error_message = f'Error al obtener el token de acceso: {e.response.text if e.response else e}'
        log_error(error_message)
        raise

# Función para asegurar que tenemos un token válido
def ensure_valid_token():
    global accessToken, tokenExpirationTime
    if not accessToken or time.time() >= tokenExpirationTime:
        get_zoom_access_token()
    return accessToken

# Función para obtener todos los usuarios en la cuenta
def get_all_users():
    all_users = []
    next_page_token = ''
    page_count = 0
    max_pages = 4000

    while True:
        try:
            token = ensure_valid_token()
            headers = {
                'Authorization': f'Bearer {token}'
            }
            params = {
                'page_size': 300
            }
            if next_page_token:
                params['next_page_token'] = next_page_token

            response = requests.get('https://api.zoom.us/v2/users', headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            all_users.extend(data.get('users', []))
            next_page_token = data.get('next_page_token', '')
            page_count += 1

            time.sleep(0.5)

            if page_count >= max_pages:
                log_execution('Límite máximo de páginas alcanzado en get_all_users')
                break

            if not next_page_token:
                break

        except requests.exceptions.RequestException as e:
            error_message = f'Error al obtener usuarios: {e.response.text if e.response else e}'
            log_error(error_message)
            raise

    return all_users

# Función para obtener las grabaciones de Zoom para un usuario y un rango de fechas
def get_all_zoom_recordings(user_id, from_date, to_date):
    all_recordings = []
    next_page_token = ''
    page_count = 0
    max_pages = 2000

    while True:
        try:
            token = ensure_valid_token()
            headers = {
                'Authorization': f'Bearer {token}'
            }
            params = {
                'page_size': 300,
                'from': from_date,
                'to': to_date
            }
            if next_page_token:
                params['next_page_token'] = next_page_token

            response = requests.get(f'https://api.zoom.us/v2/users/{user_id}/recordings', headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            all_recordings.extend(data.get('meetings', []))
            next_page_token = data.get('next_page_token', '')
            page_count += 1

            time.sleep(0.5)

            if page_count >= max_pages:
                log_execution(f'Límite máximo de páginas alcanzado en get_all_zoom_recordings para el usuario {user_id}')
                break

            if not next_page_token:
                break

        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 429:
                time.sleep(60)
                continue
            error_message = f'Error al obtener grabaciones: {e.response.text if e.response else e}'
            log_error(error_message)
            raise

    return all_recordings

# Función para obtener la fecha de hace 5 días
def get_start_date():
    date = datetime.datetime.now() - datetime.timedelta(days=5)
    return date.strftime('%Y-%m-%d')

# Función para obtener la fecha actual
def get_end_date():
    date = datetime.datetime.now()
    return date.strftime('%Y-%m-%d')

# Función para formatear la fecha en AAAA_MM_NombreDelMes
def format_month_folder_name(date_string):
    date = datetime.datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    year = date.year
    month_number = '{:02d}'.format(date.month)
    months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
              'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    month_name = months[date.month - 1]
    return f'{year}_{month_number}_{month_name}'

# Función para formatear la fecha en dd-mm-aaaa_DíaDeLaSemana
def format_date_folder_name(date_string):
    date = datetime.datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    day = '{:02d}'.format(date.day)
    month = '{:02d}'.format(date.month)
    year = date.year
    days = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    day_index = (date.weekday() + 1) % 7  # Domingo=0, Lunes=1, ..., Sábado=6
    day_name = days[day_index]
    return f'{day}-{month}-{year}_{day_name}'

# Función para descargar un archivo de grabación con reintentos
def download_recording(download_url, file_path, expected_size, retries=5, validate_size=True):
    for attempt in range(1, retries + 1):
        try:
            token = ensure_valid_token()
            url_with_token = f'{download_url}?access_token={token}'
            response = requests.get(url_with_token, stream=True)
            response.raise_for_status()

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            if validate_size:
                local_file_size = os.path.getsize(file_path)
                if local_file_size == expected_size:
                    return True
                else:
                    os.remove(file_path)
            else:
                return True
        except Exception as e:
            log_error(f'Error en intento {attempt} al descargar la grabación: {e}')
    return False

# Función principal para listar y respaldar las grabaciones
def list_and_backup_recordings():
    try:
        from_date = get_start_date()
        to_date = get_end_date()

        users = get_all_users()

        if not users or len(users) == 0:
            return

        all_download_records = []

        for user in users:
            user_id = user['id']
            print(f'\nProcesando usuario: {user["email"]}')

            recordings = get_all_zoom_recordings(user_id, from_date, to_date)

            if not recordings or len(recordings) == 0:
                continue

            download_records = []

            for meeting in recordings:
                month_folder_name = format_month_folder_name(meeting['start_time'])
                day_folder_name = format_date_folder_name(meeting['start_time'])
                meeting_folder_path = os.path.join(DOWNLOAD_FOLDER, user['email'], month_folder_name, day_folder_name)

                files_downloaded = False

                for recording_file in meeting.get('recording_files', []):
                    # Omitir archivos que están en proceso
                    if recording_file.get('status') == 'processing':
                        print(f'  El archivo {recording_file.get("id", "desconocido")} aún no está listo para ser descargado. Estado: {recording_file.get("status")}')
                        continue

                    file_extension = recording_file.get('file_extension', 'mp4')
                    sanitized_topic = sanitizar_nombre_archivo(meeting['topic'])
                    recording_type = recording_file.get('recording_type', 'tipo_desconocido')
                    file_name = f'{sanitized_topic} {recording_type} {recording_file["id"]}.{file_extension}'
                    file_path = os.path.join(meeting_folder_path, file_name)

                    status = None

                    # Verificar si el archivo existe
                    if os.path.exists(file_path):
                        # Comparar tamaños solo si no es un archivo .vtt
                        if file_extension.lower() != 'vtt':
                            local_file_size = os.path.getsize(file_path)
                            zoom_file_size = recording_file.get('file_size', 0)

                            if local_file_size == zoom_file_size:
                                # print(f'  El archivo ya existe y es completo: {file_name}')
                                status = 'archivado'
                            else:
                                print(f'  Tamaño incorrecto. Re-descargando: {file_name}')
                                os.remove(file_path)
                                download_success = download_recording(recording_file['download_url'], file_path, recording_file.get('file_size', 0))
                                if download_success:
                                    print(f'  Archivo descargado correctamente: {file_name}')
                                    status = 'descargado'
                                    files_downloaded = True
                                else:
                                    print(f'  Error al descargar el archivo: {file_name}')
                                    status = 'error'
                        else:
                            print(f'  El archivo .vtt ya existe: {file_name}')
                            status = 'archivado'
                    else:
                        # Lógica para cuando el archivo no existe
                        print(f'  Descargando archivo: {file_name}')
                        is_vtt_file = file_extension.lower() == 'vtt'
                        download_success = download_recording(recording_file['download_url'], file_path, recording_file.get('file_size', 0), retries=5, validate_size=not is_vtt_file)

                        if download_success:
                            print(f'  Archivo descargado correctamente: {file_name}')
                            status = 'descargado'
                            files_downloaded = True
                        else:
                            print(f'  Error al descargar el archivo: {file_name}')
                            status = 'error'

                    download_records.append({
                        'userEmail': user['email'],
                        'fileName': file_name,
                        'recordingId': recording_file['id'],
                        'dateTime': recording_file['recording_start'],
                        'status': status
                    })

                if not files_downloaded and os.path.exists(meeting_folder_path):
                    files = os.listdir(meeting_folder_path)
                    if len(files) == 0:
                        os.rmdir(meeting_folder_path)
                        month_folder_path = os.path.dirname(meeting_folder_path)
                        if os.path.exists(month_folder_path):
                            month_files = os.listdir(month_folder_path)
                            if len(month_files) == 0:
                                os.rmdir(month_folder_path)

            all_download_records.extend(download_records)

        print('Proceso de respaldo completado.')

    except Exception as e:
        error_message = f'Error al respaldar las grabaciones: {e}'
        print(error_message)
        traceback.print_exc()
        log_error(error_message)

if __name__ == "__main__":
    print("Iniciando el proceso de respaldo de grabaciones de Zoom...")
    list_and_backup_recordings()
