@echo off
setlocal

:: ================================
:: 🗑️ Configuración
:: ================================
set "SHORTCUT=BasculaMonitor.lnk"
set "STARTUP_FOLDER=C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"

echo ================================
echo 🗑️ Eliminando acceso directo de Inicio global
echo Archivo: %STARTUP_FOLDER%\%SHORTCUT%
echo ================================

if exist "%STARTUP_FOLDER%\%SHORTCUT%" (
    del "%STARTUP_FOLDER%\%SHORTCUT%"
    echo ✅ Acceso directo eliminado correctamente.
) else (
    echo ⚠️ No se encontró el acceso directo en Inicio global.
)

echo ================================
echo ✅ Proceso finalizado.
echo ================================
pause
