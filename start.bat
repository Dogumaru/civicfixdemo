@echo off
echo ============================================
echo   CivicFix - AI-Powered City Issue Reporter
echo ============================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH.
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo Starting CivicFix with Docker...
echo.

docker-compose up --build

pause
