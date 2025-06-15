@echo off
echo Running database schema update...

REM Activate the virtual environment
call ..\venv\Scripts\activate.bat

REM Run the schema update script
python update_schema.py

echo Schema update completed.
pause
