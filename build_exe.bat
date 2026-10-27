@echo off
chcp 65001 > nul
echo ========================================
echo  Build CopiloteEntretien.exe
echo ========================================

if not exist .venv (
    echo Venv absent. Lancez lancer.bat d'abord.
    pause & exit /b 1
)

call .venv\Scripts\activate.bat

echo Construction avec PyInstaller...
pyinstaller --onefile --windowed --name CopiloteEntretien main.py
if errorlevel 1 (
    echo ERREUR lors du build PyInstaller.
    pause & exit /b 1
)

echo.
echo Copie des fichiers de configuration dans dist\...
if exist .env       copy /Y .env       dist\
if exist cv.txt     copy /Y cv.txt     dist\
if exist contexte.txt copy /Y contexte.txt dist\

echo.
echo Build termine !
echo L'executable est dans : dist\CopiloteEntretien.exe
echo Pensez a copier votre .env si ce n'est pas fait.
pause
