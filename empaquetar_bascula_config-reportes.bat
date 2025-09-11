@echo off
echo ===========================
echo  Empaquetando Ejecutables...
echo ===========================
cd /d "%~dp0"

REM ===== Verificar archivos obligatorios =====
set "ARCHIVOS=modulo2_config.py reportes_bascula.py crear_base_datos_mejorado.py libmysql.dll libcrypto-3-x64.dll libssl-3-x64.dll"

for %%F in (%ARCHIVOS%) do (
    if not exist "%%F" (
        echo [ERROR] No se encuentra el archivo: %%F
        echo Asegúrese de que esté en la misma carpeta que este .bat
        pause
        exit /b 1
    )
)

REM Limpiar compilaciones anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
del /q *.spec 2>nul

REM ================================
REM Ejecutable de configuración (ConfigBascula.exe)
REM ================================
del /q *.spec 2>nul
pyinstaller --onefile --noconsole --clean --noconfirm ^
--exclude-module gssapi ^
--exclude-module spnego ^
--name ConfigBascula ^
modulo2_config.py
del /q ConfigBascula.spec 2>nul

REM ================================
REM Ejecutable de reportes (ReporteBascula.exe)
REM ================================
del /q *.spec 2>nul
pyinstaller --onedir --noconsole --clean --noconfirm ^
--exclude-module gssapi ^
--exclude-module spnego ^
--name ReporteBascula ^
--add-data "libmysql.dll;." ^
--add-data "libcrypto-3-x64.dll;." ^
--add-data "libssl-3-x64.dll;." ^
reportes_bascula.py
del /q ReporteBascula.spec 2>nul

REM ================================
REM Ejecutable para crear base de datos inicial (crearBaseDatosInicial.exe)
REM ================================
del /q *.spec 2>nul
pyinstaller --onefile --noconsole --clean --noconfirm ^
--exclude-module gssapi ^
--exclude-module spnego ^
--name crearBaseDatosInicial ^
--add-data "libmysql.dll;." ^
--add-data "libcrypto-3-x64.dll;." ^
--add-data "libssl-3-x64.dll;." ^
crear_base_datos_mejorado.py
del /q crearBaseDatosInicial.spec 2>nul

echo.
echo =================================
echo   Empaquetado finalizado
echo   Revisar carpeta "dist"
echo =================================
pause
