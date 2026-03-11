@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title Instalador - Monitor de Presion y Temperatura
color 0B

echo.
echo ============================================================
echo   INSTALADOR: Monitor de Presion y Temperatura
echo ============================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python no encontrado. Instalando Python...
    powershell -Command "Start-Process https://www.python.org/downloads/"
    echo.
    echo Por favor, instala Python desde el navegador que se abrió.
    echo IMPORTANTE: Marca la casilla "Add Python to PATH"
    echo.
    pause
    echo Continuando después de instalar Python...
    echo.
)

REM Verificar Python de nuevo
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python sigue sin estar disponible.
    echo Por favor, instala Python manualmente y ejecuta este script de nuevo.
    pause
    exit /b 1
)

echo [✓] Python encontrado
python --version
echo.

REM Instalar pip upgrade
echo [*] Actualizando pip...
python -m pip install --upgrade pip -q
if errorlevel 1 (
    echo [!] Advertencia: No se pudo actualizar pip
)

echo.
echo [*] Instalando dependencias...
echo.

REM Instalar dependencias del archivo requirements.txt
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo [*] Instalando paquetes individuales...
    python -m pip install streamlit pandas plotly numpy
)

if errorlevel 1 (
    echo.
    echo [ERROR] Hubo un problema instalando las dependencias.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   INSTALACION COMPLETADA CON EXITO
echo ============================================================
echo.
echo La aplicación está lista para usar.
echo.
echo Para ejecutar la app, haz doble click en "Ejecutar.bat"
echo.

pause
