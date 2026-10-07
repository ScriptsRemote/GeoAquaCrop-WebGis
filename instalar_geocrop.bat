@echo off
REM Instala o GeoAquaCrop (WebGIS) num ambiente virtual (.venv) usando o Python do sistema.
REM Requer Python 3.11, 3.12 ou 3.13 no PATH (py -3.12 tambem funciona).
cd /d "%~dp0"
if not exist .venv (
    py -3.12 -m venv .venv 2>nul || python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Falha na instalacao. Alternativa com conda:
    echo     conda env create -f environment.yml
    echo     conda activate geocrop
    pause
    exit /b 1
)
echo.
echo Pronto. Rode iniciar_geocrop.bat
pause
