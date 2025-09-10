@echo off
setlocal

:: ================================
:: 🚀 Configuración inicial
:: ================================
set "EXE=BasculaMonitor.exe"
set "SHORTCUT=BasculaMonitor.lnk"

:: Carpeta donde está este .bat (y el exe)
set "APPDIR=%~dp0"

echo ================================
echo 🚀 Configurando %EXE%
echo Carpeta actual: %APPDIR%
echo ================================

:: ================================
:: 1. Crear acceso directo en Inicio de Windows
:: ================================
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
echo 📌 Creando acceso directo en: %STARTUP_FOLDER%

:: Crear acceso directo usando PowerShell, de manera robusta
powershell -NoProfile -Command ^
"$WshShell = New-Object -ComObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\%SHORTCUT%'); ^
$Shortcut.TargetPath = '%APPDIR%%EXE%'; ^
$Shortcut.WorkingDirectory = '%APPDIR%'; ^
$Shortcut.Save()"

if exist "%STARTUP_FOLDER%\%SHORTCUT%" (
    echo ✅ Acceso directo creado correctamente.
) else (
    echo ⚠️ No se pudo crear el acceso directo.
)

:: ================================
:: 2. Lanzar el servicio inmediatamente sin ventana de CMD
:: ================================
echo ▶️ Iniciando %EXE% ahora mismo...
start "" /b "" "%APPDIR%%EXE%"

echo ================================
echo ✅ Configuración finalizada.
echo ================================
timeout /t 3 >nul
