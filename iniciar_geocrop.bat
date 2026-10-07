@echo off
REM Inicia o GeoAquaCrop (WebGIS) e abre o navegador em http://127.0.0.1:8050
cd /d "%~dp0"
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python run.py
pause
