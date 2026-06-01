@echo off
echo Starting SmartPlan Web Application...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
  echo Python is not installed or not in PATH. Please install Python 3.8 or higher.
  pause
  exit /b
)

REM Check if virtual environment exists, if not create it
if not exist venv\ (
  echo Creating virtual environment...
  python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if requirements.txt is newer than last install
if not exist .installed (
  echo Installing dependencies...
  pip install -r requirements.txt
  echo. > .installed
) else (
  for %%i in (requirements.txt) do set reqtime=%%~ti
  for %%i in (.installed) do set insttime=%%~ti
  if "%reqtime%" gtr "%insttime%" (
    echo Updating dependencies...
    pip install -r requirements.txt
    echo. > .installed
  )
)

REM Run the Flask application
echo Starting the application...
python app.py

pause
