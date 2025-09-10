@echo off
setlocal

:: ================================
:: 🚀 Configuración inicial
:: ================================
set EXE=BasculaMonitor.exe
set SHORTCUT=BasculaMonitor.lnk

:: Carpeta donde está este .bat (y el exe)
set APPDIR=%~dp0

echo ================================
echo 🚀 Configurando %EXE%
echo Carpeta actual: %APPDIR%
echo ================================

:: ================================
:: 1. Crear acceso directo en Inicio de Windows
:: ================================
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
echo 📌 Creando acceso directo en: %STARTUP_FOLDER%

:: Crear acceso directo con PowerShell
powershell -command ^
  "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTUP_FOLDER%\%SHORTCUT%'); ^
   $s.TargetPath='%APPDIR%%EXE%'; ^
   $s.WorkingDirectory='%APPDIR%'; ^
   $s.Save()"

if exist "%STARTUP_FOLDER%\%SHORTCUT%" (
    echo ✅ Acceso directo creado correctamente.
) else (
    echo ⚠️ No se pudo crear el acceso directo.
)

:: ================================
:: 2. Lanzar el servicio inmediatamente
:: ================================
echo ▶️ Iniciando %EXE% ahora mismo...
start "" "%APPDIR%%EXE%"

echo ================================
echo ✅ Configuración finalizada.
echo ================================
pause
