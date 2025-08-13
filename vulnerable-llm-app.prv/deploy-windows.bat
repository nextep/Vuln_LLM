@echo off
REM Windows Deployment Script for Vulnerable LLM Application
REM Designed to work with existing Ollama and Docker installations

echo ========================================
echo   Vulnerable LLM App - Windows Setup
echo ========================================
echo.

REM Check if Docker is running
echo [1/5] Checking Docker status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    echo.
    pause
    exit /b 1
)
echo ✓ Docker is running

REM Check if Ollama is running
echo [2/5] Checking Ollama status...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ollama is not running on port 11434.
    echo Please start Ollama service first.
    echo.
    pause
    exit /b 1
)
echo ✓ Ollama is running on port 11434

REM Check if OpenWebUI is accessible
echo [3/5] Checking OpenWebUI status...
curl -s http://192.168.1.110:8888/health >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: OpenWebUI at 192.168.1.110:8888 is not accessible.
    echo Please ensure OpenWebUI is running and accessible at this address.
    echo Continue anyway? (y/n)
    set /p continue=
    if /i "%continue%" neq "y" exit /b 1
)
echo ✓ OpenWebUI is accessible

REM Set Windows-specific environment variables
echo [4/5] Setting up environment...
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1

REM Import templates to OpenWebUI (optional step)
echo [5/5] Importing vulnerability templates...
cd openwebui_templates
python import_templates.py --url http://192.168.1.110:8888
if %errorlevel% neq 0 (
    echo WARNING: Template import failed. You can import them manually later.
)
cd ..

REM Build and start the application
echo.
echo Building and starting the vulnerable LLM application...
docker-compose down --remove-orphans
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo ERROR: Failed to start the application.
    pause
    exit /b 1
)

echo.
echo ========================================
echo       Deployment Completed Successfully!
echo ========================================
echo.
echo Application URLs:
echo   Main Interface: http://localhost:5001
echo   Advanced Testing: http://localhost:5001/advanced-testing
echo   OpenWebUI: http://192.168.1.110:8888
echo.
echo To stop the application, run:
echo   docker-compose down
echo.
pause