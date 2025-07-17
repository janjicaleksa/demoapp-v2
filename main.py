from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn
import os
from app.services.table_extractor import TableExtractor
from app.services.ai_processor import AIProcessor
from typing import Literal, Optional

# Create required directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)
os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)

app = FastAPI(title="Table Extraction and Processing")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# File type definitions
FileType = Literal[
    "kraj-fiskalne-kupci",
    "presek-bilansa-kupci",
    "kraj-fiskalne-prodavci",
    "presek-bilansa-prodavci"
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/create-client-folder")
async def create_client_folder(client_name: str = Form(...)):
    # Sanitize client name for folder creation
    safe_client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).strip()
    if not safe_client_name:
        raise HTTPException(status_code=400, detail="Invalid client name")
    
    # Create client directories
    client_upload_dir = Path("uploads") / safe_client_name
    client_processed_dir = Path("processed") / safe_client_name
    
    os.makedirs(client_upload_dir, exist_ok=True)
    os.makedirs(client_processed_dir, exist_ok=True)
    
    return JSONResponse(content={
        "status": "success",
        "client_name": safe_client_name,
        "message": f"Created folders for client: {client_name}"
    })

@app.post("/upload/{client_name}/{file_type}")
async def upload_file(
    client_name: str,
    file_type: FileType,
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File has no name")
    
    # Validate file type
    if not file.filename.lower().endswith(('.xlsx', '.pdf', '.docx')):
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported file type: {file.filename}"}
        )
    
    # Ensure client directory exists
    client_dir = Path("uploads") / client_name
    if not client_dir.exists():
        raise HTTPException(status_code=404, detail=f"Client folder not found: {client_name}")
    
    # Save file with type-specific name
    file_extension = Path(file.filename).suffix
    new_filename = f"{file_type}{file_extension}"
    file_path = client_dir / new_filename
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return JSONResponse(content={
        "status": "success",
        "message": f"File uploaded successfully as {new_filename}",
        "file_type": file_type,
        "client_name": client_name
    })

@app.get("/download/json/{client_name}/{filename}")
async def download_json(client_name: str, filename: str):
    file_path = Path("processed") / client_name / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/json"
    )

@app.get("/download/processed/{client_name}/{filename}")
async def download_processed(client_name: str, filename: str):
    file_path = Path("processed") / client_name / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if filename.endswith('.xlsx') else "text/csv"
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )

@app.get("/list/files/{client_name}")
async def list_files(client_name: str):
    processed_dir = Path("processed") / client_name
    
    if not processed_dir.exists():
        raise HTTPException(status_code=404, detail=f"Client folder not found: {client_name}")
    
    json_files = [f.name for f in processed_dir.glob("*.json")]
    excel_files = [f.name for f in processed_dir.glob("*.xlsx")]
    csv_files = [f.name for f in processed_dir.glob("*.csv")]
    
    return {
        "json_files": json_files,
        "processed_files": excel_files + csv_files
    }

@app.post("/process/{client_name}")
async def process_files(client_name: str, table_type: Optional[str] = None):
    # Initialize services with client-specific directories
    client_upload_dir = str(Path("uploads") / client_name)
    client_processed_dir = str(Path("processed") / client_name)
    
    table_extractor = TableExtractor(client_upload_dir, client_processed_dir)
    ai_processor = AIProcessor(client_processed_dir)
    
    # Extract tables from all files
    extraction_results = table_extractor.process_all_files()
    
    # Check if any extraction failed
    failed_extractions = [
        result for result in extraction_results 
        if result['status'] == 'error'
    ]
    
    if failed_extractions:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Some files failed to process",
                "details": failed_extractions
            }
        )
    
    # Process extracted tables with AI
    ai_result = ai_processor.process_tables_with_ai(table_type)
    
    if ai_result['status'] == 'error':
        return JSONResponse(
            status_code=500,
            content=ai_result
        )
    
    return JSONResponse(content={
        "status": "success",
        "message": "Files processed successfully",
        "client_name": client_name,
        "extraction_results": extraction_results,
        "ai_results": ai_result
    })

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 