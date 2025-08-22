@echo off
setlocal

:: ================================
:: Configuración
:: ================================
set SCRIPT=modulo1_lector_unificado.py

:loop
pythonw "%~dp0%SCRIPT%"
timeout /t 5 >nul
goto loop