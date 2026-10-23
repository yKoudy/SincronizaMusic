@echo off
chcp 65001 >nul
title Criar executavel Windows
cd /d "%~dp0"
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto erro
py -m PyInstaller --noconfirm --clean --windowed --name "Sincroniza Music" --collect-all pygame src\main.py
if errorlevel 1 goto erro
echo.
echo EXE criado em dist\Sincroniza Music\Sincroniza Music.exe
echo Copie a pasta inteira para o local desejado.
pause
exit /b 0
:erro
echo Falha ao criar o executavel. Verifique se Python esta instalado.
pause
exit /b 1
