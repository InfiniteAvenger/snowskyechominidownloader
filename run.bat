@echo off
title Snowsky Echo File Downloader
echo Starting Snowsky Echo File Downloader...
echo.

:: Check if Python is installed and in PATH
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python was not found in your system PATH.
    echo Please ensure Python is installed and the option "Add Python to PATH" is enabled.
    echo.
    pause
    exit /b
)

:: Execute the server script using venv python if available, otherwise system python
set PYTHON_CMD=python
if exist venv\Scripts\python.exe (
    set PYTHON_CMD=venv\Scripts\python
)

%PYTHON_CMD% run.py

:: If the server crashed or exited with an error, keep the window open
if %errorlevel% neq 0 (
    echo.
    echo Server stopped with an error (Exit Code: %errorlevel%).
    pause
)
