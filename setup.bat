@echo off
echo ============================================
echo   Event Prize Game - Setup Script
echo ============================================
echo.

echo [1/4] Installing dependencies...
pip install -r requirements.txt
echo.

echo [2/4] Running database migrations...
python manage.py makemigrations
python manage.py migrate
echo.

echo [3/4] Creating default users...
python manage.py create_default_users
echo.

echo [4/4] Setup Complete!
echo ============================================
echo   Default Login Credentials:
echo.
echo   ADMIN  : username=admin   password=admin123
echo            (Dashboard + Registration access)
echo.
echo   STAFF  : username=staff   password=staff123
echo            (Registration only access)
echo ============================================
echo.
echo   Run the server:  python manage.py runserver
echo   Open browser  :  http://127.0.0.1:8000/
echo.
echo   IMPORTANT: Change passwords before going live!
echo ============================================
pause
