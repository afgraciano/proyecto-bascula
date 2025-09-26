@echo off
setlocal

:: ================================
:: 🗑️ Configuración
:: ================================
set "SHORTCUT=BasculaServicio.lnk"
set "STARTUP_FOLDER=C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\%SHORTCUT%"

echo ================================
echo 🗑️ Eliminando acceso directo de Inicio global
echo Archivo: %SHORTCUT_PATH%
echo ================================

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    if exist "%SHORTCUT_PATH%" (
        echo ⚠️ No se pudo eliminar el acceso directo.
    ) else (
        echo ✅ Acceso directo eliminado correctamente.
    )
) else (
    echo ⚠️ El acceso directo no existe en Inicio.
)

echo ================================
echo ✅ Proceso finalizado.
echo ================================
pause
