@echo off
setlocal
pushd "%~dp0"
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo Virtual environment not found at .venv.
  echo Create it and install dependencies as described in README_TH.md.
  pause
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" -m streamlit run "%~dp0app.py" --server.address localhost --server.port 8501
endlocal
