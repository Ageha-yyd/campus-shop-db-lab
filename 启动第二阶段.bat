@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo 请先按 stage2\README.md 创建 .venv 并安装依赖。
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m stage2
if errorlevel 1 pause
