@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Execute instalar.bat depois de instalar Python 3.11+.
  pause
  exit /b 1
)
py src\main.py
if errorlevel 1 (
  echo.
  echo O aplicativo encerrou com erro. Execute instalar.bat e tente novamente.
  pause
)
