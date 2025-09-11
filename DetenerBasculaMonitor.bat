@echo off
title 🔴 Detener BasculaMonitor
echo =======================================
echo  🛑 Deteniendo BasculaMonitor.exe...
echo =======================================

:: Matar el monitor convertido en EXE
taskkill /F /IM BasculaMonitor.exe >nul 2>&1

:: Matar cualquier instancia de pythonw (por si sigue viva del loop)
taskkill /F /IM pythonw.exe >nul 2>&1

echo ✅ BasculaMonitor detenido correctamente.
pause
