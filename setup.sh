#!/bin/bash

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete! You can now run the application with:"
echo "uvicorn main:app --reload"
echo
echo "Remember to activate the virtual environment each time you work on the project:"
echo "source venv/bin/activate" 