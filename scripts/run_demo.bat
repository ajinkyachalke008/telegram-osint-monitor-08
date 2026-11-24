@echo off
REM telegram-osint-monitor-08 1-Command Demo Launcher for Windows CMD
setlocal
cd /d "%~dp0\.."
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe scripts\run_demo.py %*
) else (
    python scripts\run_demo.py %*
)
