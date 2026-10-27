@echo off
chcp 65001 > nul
echo ========================================
echo  Copilote d'entretien
echo ========================================

if not exist .venv (
    echo Creation du venv Python...
    py -m venv .venv
    if errorlevel 1 (
        echo ERREUR : impossible de creer le venv.
        pause & exit /b 1
    )
)

call .venv\Scripts\activate.bat

echo Installation des dependances...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERREUR : pip install a echoue.
    pause & exit /b 1
)

echo Lancement...
python main.py %*
