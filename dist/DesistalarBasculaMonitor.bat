@echo off
setlocal

set SHORTCUT=BasculaMonitor.lnk
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

echo 🗑️ Eliminando acceso directo de inicio automático...
del "%STARTUP_FOLDER%\%SHORTCUT%" >nul 2>&1

if exist "%STARTUP_FOLDER%\%SHORTCUT%" (
    echo ⚠️ No se pudo eliminar el acceso directo.
) else (
    echo ✅ Acceso directo eliminado.
)

echo ✅ Ahora puedes cerrar el programa y no volverá a iniciarse solo.
pause
