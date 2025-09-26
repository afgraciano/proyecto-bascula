@echo off
setlocal

:: ================================
:: 🚀 Configuración
:: ================================
set "EXE=C:\Bascula\BasculaServicio.exe"
set "SHORTCUT=BasculaServicio.lnk"
set "STARTUP_FOLDER=C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"

echo ================================
echo 📌 Creando acceso directo en Inicio global
echo EXE: %EXE%
echo Destino: %STARTUP_FOLDER%\%SHORTCUT%
echo ================================

:: Crear acceso directo con PowerShell (igual que al hacerlo a mano)
powershell -NoProfile -Command ^
"$WshShell = New-Object -ComObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\%SHORTCUT%'); ^
$Shortcut.TargetPath = '%EXE%'; ^
$Shortcut.WorkingDirectory = 'C:\Bascula'; ^
$Shortcut.IconLocation = '%EXE%,0'; ^
$Shortcut.Save()"

if exist "%STARTUP_FOLDER%\%SHORTCUT%" (
    echo ✅ Acceso directo creado correctamente.
) else (
    echo ⚠️ No se pudo crear el acceso directo.
)

echo ================================
echo ✅ Proceso finalizado.
echo ================================
pause
