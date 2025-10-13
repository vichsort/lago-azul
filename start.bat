@echo off

cd backend

call .\.venv\Scripts\activate.bat

start cmd /k "flask run"

cd ..\frontend

start cmd /k "npm run dev"

ECHO.

timeout /t 5 >nul

start http://localhost:5173/

exit