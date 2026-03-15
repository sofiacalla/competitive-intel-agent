@echo off
REM ============================================
REM  Competitive Intelligence Agent - Quick Run
REM  Double-click this file or run: run.bat
REM ============================================

echo.
echo ========================================
echo  Competitive Intelligence Agent
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found.
    echo Install from https://python.org/downloads
    echo IMPORTANT: Check "Add python.exe to PATH" during install!
    pause
    exit /b 1
)

REM Check SDK
python -c "import anthropic" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Anthropic SDK...
    pip install anthropic
    echo.
)

REM Check API key
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY not set!
    echo.
    echo 1. Press Win+S, search "environment variables"
    echo 2. Click "Edit the system environment variables"
    echo 3. Click "Environment Variables..."
    echo 4. Under User variables, click "New..."
    echo 5. Name: ANTHROPIC_API_KEY
    echo 6. Value: your sk-ant-... key
    echo 7. Click OK, OK, OK - then reopen this window
    echo.
    echo Get a key at: https://console.anthropic.com/
    pause
    exit /b 1
)

echo Running competitor 1 of 3: OpenAI...
python "%~dp0agent.py" 1
echo.
echo Waiting 2 minutes before next competitor...
timeout /t 120 /nobreak >nul

echo Running competitor 2 of 3: Anthropic (Claude)...
python "%~dp0agent.py" 2
echo.
echo Waiting 2 minutes before next competitor...
timeout /t 120 /nobreak >nul

echo Running competitor 3 of 3: Microsoft Copilot...
python "%~dp0agent.py" 3

REM Open report
if exist "%~dp0reports\latest.html" (
    echo.
    echo Opening report...
    start "" "%~dp0reports\latest.html"
)

echo.
pause
