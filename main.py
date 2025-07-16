from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn
import os
from app.services.table_extractor import TableExtractor
from app.services.ai_processor import AIProcessor

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

# Initialize services
table_extractor = TableExtractor("uploads", "processed")
ai_processor = AIProcessor("processed")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    uploaded_files = []
    
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="File has no name")
            
        # Validate file type
        if not file.filename.lower().endswith(('.xlsx', '.pdf', '.docx')):
            return JSONResponse(
                status_code=400,
                content={"error": f"Unsupported file type: {file.filename}"}
            )
        
        # Save file
        file_path = Path("uploads") / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        uploaded_files.append(file.filename)
    
    return JSONResponse(content={
        "message": "Files uploaded successfully",
        "files": uploaded_files
    })

@app.post("/process")
async def process_files():
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
    ai_result = ai_processor.process_tables()
    
    if ai_result['status'] == 'error':
        return JSONResponse(
            status_code=500,
            content=ai_result
        )
    
    return JSONResponse(content={
        "status": "success",
        "message": "Files processed successfully",
        "extraction_results": extraction_results,
        "ai_results": ai_result
    })

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 