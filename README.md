# Zoom Recordings Backup Script

Este script en Python permite automatizar la descarga y respaldo de grabaciones de reuniones de Zoom en un servidor local, organizando las grabaciones en carpetas estructuradas por mes y día. Utiliza la API de Zoom y maneja la autenticación mediante OAuth Server-to-Server. Los archivos de grabación se almacenan en una carpeta específica en el sistema local, con nombres de archivo sanitizados para evitar problemas de caracteres no permitidos.

## Características

- **Autenticación**: Obtención de un token de acceso OAuth Server-to-Server para la autenticación con la API de Zoom.
- **Gestión de Usuarios**: Recupera todos los usuarios en la cuenta de Zoom.
- **Descarga de Grabaciones**: Descarga las grabaciones de reuniones para cada usuario en un rango de fechas específico.
- **Manejo de Errores**: Registro de errores en un archivo `error_log.txt` para facilitar el seguimiento y diagnóstico.
- **Log de Ejecución**: Archivo de log `execution_log.txt` para registrar eventos importantes durante la ejecución.
- **Estructura de Carpetas**: Las grabaciones se almacenan en carpetas estructuradas por año, mes y día.
- **Sanitización de Nombres de Archivos**: Remueve caracteres no permitidos y asegura la compatibilidad con sistemas de archivos.

## Requisitos Previos

1. **Python 3.7+**
2. **Paquetes Python**: `requests`, `python-dotenv`
3. **Cuenta Zoom** con autenticación Server-to-Server habilitada y credenciales OAuth configuradas.

### Instalación de dependencias

```bash
pip install requests python-dotenv
```

## Configuración

1. **Variables de entorno**: Este script requiere un archivo `.env` para almacenar las credenciales de la API de Zoom. Crea un archivo `.env` en el directorio raíz del proyecto con el siguiente contenido:

    ```plaintext
    ZOOM_ACCOUNT_ID=your_zoom_account_id
    ZOOM_CLIENT_ID=your_zoom_client_id
    ZOOM_CLIENT_SECRET=your_zoom_client_secret
    ```

2. **Carpeta de Descarga**: Asegúrate de que la carpeta especificada en `DOWNLOAD_FOLDER` (`D:\\reunioneszoom` por defecto) exista o se creará automáticamente.

## Uso

Para ejecutar el script y comenzar el proceso de respaldo de grabaciones:

```bash
python nombre_del_script.py
```

El script descargará las grabaciones de reuniones en la carpeta configurada y organizará los archivos por estructura de año/mes/día.

### Ejecución en Windows

Para programar la ejecución periódica en un entorno de Windows, se puede usar el Programador de Tareas, configurando una tarea que ejecute el script en los intervalos deseados.

## Estructura del Código

### Funciones Principales

1. **sanitizar_nombre_archivo(nombre_archivo)**  
   Sanitiza los nombres de archivo eliminando caracteres no permitidos y ajustando la longitud máxima del nombre a 255 caracteres.

2. **log_error(message)**  
   Registra errores en un archivo `error_log.txt`.

3. **log_execution(message)**  
   Registra eventos importantes en el archivo `execution_log.txt`.

4. **get_zoom_access_token()**  
   Obtiene un token de acceso utilizando la autenticación Server-to-Server OAuth. 

5. **ensure_valid_token()**  
   Verifica y renueva el token de acceso si es necesario antes de realizar una solicitud a la API de Zoom.

6. **get_all_users()**  
   Recupera todos los usuarios de la cuenta de Zoom mediante paginación. Esta función está limitada a 4000 páginas para prevenir excesivos tiempos de ejecución.

7. **get_all_zoom_recordings(user_id, from_date, to_date)**  
   Recupera las grabaciones de un usuario específico en un rango de fechas definido, con un límite de 2000 páginas para manejar grandes volúmenes de datos.

8. **get_start_date() y get_end_date()**  
   Obtiene las fechas de inicio y fin para el rango de búsqueda de grabaciones (de 5 días atrás a la fecha actual).

9. **format_month_folder_name(date_string) y format_date_folder_name(date_string)**  
   Formatean los nombres de carpetas para organizar las grabaciones por mes y día, incluyendo nombres del mes y del día en español.

10. **download_recording(download_url, file_path, expected_size, retries=5, validate_size=True)**  
    Descarga un archivo de grabación desde la API de Zoom. Incluye lógica para reintentar descargas en caso de errores temporales.

11. **list_and_backup_recordings()**  
    Función principal que coordina el respaldo de las grabaciones, llama a las funciones de usuarios, grabaciones y descarga, y maneja la estructura de carpetas para almacenar las grabaciones.

### Archivos de Registro

- **error_log.txt**: Registra errores y excepciones durante la ejecución.
- **execution_log.txt**: Registra eventos importantes y estados de ejecución.

## Personalización

- **Carpeta de Descarga**: Cambia la variable `DOWNLOAD_FOLDER` para especificar una ruta personalizada.
- **Rango de Fechas**: Ajusta las funciones `get_start_date()` y `get_end_date()` para modificar el período de grabaciones a descargar.

## Estructura de Carpetas de Salida

Las grabaciones descargadas se almacenarán de la siguiente manera:

```plaintext
D:\
└── reunioneszoom\
    └── usuario@dominio.com\
        └── AAAA_MM_Mes\
            └── dd-mm-aaaa_Día\
                └── {Nombre de la Reunión}_{Tipo de Grabación}_{ID de Grabación}.ext
```

Por ejemplo:

```plaintext
D:\
└── reunioneszoom\
    └── usuario@example.com\
        └── 2023_10_Octubre\
            └── 29-10-2023_Domingo\
                └── Reunión Importante_share_audio_12345.mp4
```

## Manejo de Errores y Reintentos

El script implementa un sistema de reintentos para la descarga de archivos y maneja códigos de error HTTP específicos (e.g., 429 para limitar la tasa de peticiones). Los errores se registran en `error_log.txt` con detalles del intento y el mensaje de error.

## Contribuciones

Si deseas contribuir a este proyecto, crea una rama con tus cambios y envía un pull request. Las mejoras en la optimización y seguridad del script son bienvenidas.

## Licencia

Este proyecto está bajo la Licencia MIT.
```

