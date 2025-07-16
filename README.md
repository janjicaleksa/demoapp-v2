# Table Extraction and Processing Application

This application allows users to upload multiple files (DOCX, PDF, XLSX) containing tables, extracts the tables into JSON format, and processes them using AI to combine and analyze the data.

## Features

- Multiple file upload support (.docx, .pdf, .xlsx)
- Automatic table extraction from various file formats
- JSON conversion and storage
- AI-powered table data combination and analysis
- User-friendly web interface

## Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Virtual Environment Setup

1. Open a terminal in the project root directory

2. Create a virtual environment:
   ```bash
   # On Windows
   python -m venv venv
   
   # On macOS/Linux
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   # On Windows (Command Prompt)
   venv\Scripts\activate.bat
   
   # On Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   
   # On macOS/Linux
   source venv/bin/activate
   ```

   You should see `(venv)` at the beginning of your terminal prompt, indicating that the virtual environment is active.

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Make sure your virtual environment is activated (you should see `(venv)` in your terminal prompt)

2. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

3. Open your browser and navigate to `http://localhost:8000`

### Deactivating the Virtual Environment

When you're done working on the project, you can deactivate the virtual environment:
```bash
deactivate
```

## Project Structure

- `/app` - Main application directory
  - `/api` - API endpoints
  - `/services` - Business logic services
  - `/models` - Data models
  - `/static` - Static files (CSS, JS)
  - `/templates` - HTML templates
- `/uploads` - Temporary file storage
- `/processed` - Processed JSON files
- `/venv` - Virtual environment (do not commit to version control)

## Development Notes

- Always activate the virtual environment before running or developing the application
- If you install new dependencies, update requirements.txt:
  ```bash
  pip freeze > requirements.txt
  ```
- Add `venv/` to your `.gitignore` file if you're using version control 