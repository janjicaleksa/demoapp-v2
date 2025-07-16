@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Setup complete! You can now run the application with:
echo uvicorn main:app --reload
echo.
echo Remember to activate the virtual environment each time you work on the project:
echo venv\Scripts\activate.bat
pause 