@echo off
chcp 65001 >nul

title Monitor de Presión y Temperatura

REM Cambiar al directorio de la aplicación
cd /d "%~dp0"

REM Verificar que app.py existe
if not exist "app.py" (
    echo Error: No se encontró app.py
    pause
    exit /b 1
)

REM Ejecutar la aplicación
echo Iniciando la aplicación...
echo.
echo La aplicación se abrirá en tu navegador en http://localhost:8501
echo.
echo Presiona Ctrl+C en esta ventana para detener la aplicación.
echo.

streamlit run app.py

pause
