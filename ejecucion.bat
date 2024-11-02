@echo off
:: Activar el entorno virtual
call D:\web\zoom_py\venv\Scripts\activate.bat
:: Navegar al directorio del script (si es diferente al actual)
cd /d D:\web\zoom_py
:: Ejecutar el script Python
python main.py
:: Pausar para ver resultados (opcional, comentar o eliminar si no es necesario)
:: pause