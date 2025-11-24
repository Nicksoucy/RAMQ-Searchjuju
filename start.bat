@echo off
echo ========================================
echo   RAMQ Billing Assistant - Demarrage
echo ========================================
echo.

REM Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo Telechargez Python depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Verification des dependances...
cd backend
if not exist "venv" (
    echo Creation environnement virtuel...
    python -m venv venv
)

echo [2/4] Activation environnement virtuel...
call venv\Scripts\activate.bat

echo [3/4] Installation des packages Python...
pip install -q -r ..\requirements.txt

echo [4/4] Demarrage du serveur API...
echo.
echo ========================================
echo   Backend API: http://localhost:8080
echo   Documentation: http://localhost:8080/docs
echo   Frontend: http://localhost:3000
echo ========================================
echo.
echo Appuyez sur Ctrl+C pour arreter
echo.

REM Demarrer backend
start "RAMQ API Backend" cmd /k "cd /d %CD% && venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080"

REM Attendre que le backend demarre
timeout /t 5 /nobreak >nul

REM Ouvrir documentation API
start http://localhost:8080/docs

REM Demarrer frontend
cd ..\frontend
echo Demarrage du frontend...
start "RAMQ Frontend" cmd /k "python -m http.server 3000"

REM Attendre et ouvrir frontend
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo Application demarree avec succes!
echo Fermez les fenetres de commande pour arreter l'application.
pause
