@echo off
chcp 65001 >nul
title Instalar Sincroniza Music
echo ==========================================
echo       INSTALADOR - SINCRONIZA MUSIC
echo ==========================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python nao foi encontrado. Instale Python 3.11+ em https://www.python.org/downloads/
  echo Marque "Add Python to PATH" durante a instalacao.
  pause
  exit /b 1
)
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Falha ao instalar dependencias.
  pause
  exit /b 1
)
echo.
echo Instalacao concluida! Use iniciar.bat para abrir.
pause
