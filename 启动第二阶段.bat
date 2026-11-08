@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Please follow stage2\README.md to create .venv and install dependencies.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m stage2
if errorlevel 1 pause
