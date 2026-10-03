@echo off
rem Double-clic : installe au premier lancement, puis démarre le site sur http://localhost:8000
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python est introuvable. Installe-le depuis https://www.python.org/downloads/
    echo en cochant "Add python.exe to PATH", puis relance ce fichier.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Premier lancement : installation, ca prend une minute...
    python -m venv .venv || goto :erreur
    ".venv\Scripts\python" -m pip install --quiet -r requirements.txt || goto :erreur
    ".venv\Scripts\python" seed.py || goto :erreur
)

echo Le site demarre sur http://localhost:8000  (ferme cette fenetre pour l'arreter)
start "" cmd /c "timeout /t 3 >nul & start http://localhost:8000"
".venv\Scripts\python" main.py
exit /b 0

:erreur
echo L'installation a echoue. Verifie ta connexion internet et ta version de Python (3.10 ou plus).
pause
exit /b 1
