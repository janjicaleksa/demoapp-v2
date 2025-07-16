import pandas as pd
import tabula.io as tabula
from docx import Document
from pathlib import Path
import json
import PyPDF2
import os

class TableExtractor:
    def __init__(self, upload_dir: str, processed_dir: str):
        self.upload_dir = Path(upload_dir)
        self.processed_dir = Path(processed_dir)

    def extract_from_excel(self, file_path: Path) -> list:
        """Extract tables from Excel files."""
        tables = []
        excel_file = pd.ExcelFile(file_path)
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            if not df.empty:
                tables.append({
                    'sheet_name': sheet_name,
                    'data': df.to_dict(orient='records')
                })
        
        return tables

    def extract_from_pdf(self, file_path: Path) -> list:
        """Extract tables from PDF files."""
        tables = []
        
        # Try tabula-py first for table extraction
        pdf_tables = tabula.read_pdf(str(file_path), pages='all', multiple_tables=True)
        
        for idx, table in enumerate(pdf_tables):
            if isinstance(table, pd.DataFrame) and not table.empty:
                tables.append({
                    'table_number': idx + 1,
                    'data': table.to_dict(orient='records')
                })
        
        return tables

    def extract_from_docx(self, file_path: Path) -> list:
        """Extract tables from DOCX files."""
        tables = []
        doc = Document(str(file_path))
        
        for idx, table in enumerate(doc.tables):
            data = []
            # Get headers from the first row
            headers = [cell.text.strip() for cell in table.rows[0].cells]
            
            # Get data from remaining rows
            for row in table.rows[1:]:
                row_data = {}
                for header, cell in zip(headers, row.cells):
                    row_data[header] = cell.text.strip()
                data.append(row_data)
            
            tables.append({
                'table_number': idx + 1,
                'data': data
            })
        
        return tables

    def process_file(self, filename: str) -> dict:
        """Process a single file and extract tables."""
        file_path = self.upload_dir / filename
        output_path = self.processed_dir / f"{filename}.json"
        
        try:
            if filename.lower().endswith('.xlsx'):
                tables = self.extract_from_excel(file_path)
            elif filename.lower().endswith('.pdf'):
                tables = self.extract_from_pdf(file_path)
            elif filename.lower().endswith('.docx'):
                tables = self.extract_from_docx(file_path)
            else:
                raise ValueError(f"Unsupported file type: {filename}")

            # Save extracted tables to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'filename': filename,
                    'tables': tables
                }, f, ensure_ascii=False, indent=2)

            return {
                'status': 'success',
                'message': f'Successfully extracted tables from {filename}',
                'output_file': str(output_path)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error processing {filename}: {str(e)}'
            }

    def process_all_files(self) -> list:
        """Process all files in the upload directory."""
        results = []
        for file_path in self.upload_dir.glob('*'):
            if file_path.suffix.lower() in ['.xlsx', '.pdf', '.docx']:
                result = self.process_file(file_path.name)
                results.append(result)
        return results 