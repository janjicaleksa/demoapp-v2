import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any

class AIProcessor:
    def __init__(self, processed_dir: str):
        self.processed_dir = Path(processed_dir)

    def load_json_files(self) -> List[Dict[str, Any]]:
        """Load all JSON files from the processed directory."""
        all_data = []
        for json_file in self.processed_dir.glob('*.json'):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.append(data)
        return all_data

    def analyze_table_structure(self, tables: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Analyze the structure of tables to find common columns."""
        all_columns = {}
        for table in tables:
            for table_data in table.get('tables', []):
                data = table_data.get('data', [])
                if data:
                    columns = list(data[0].keys())
                    table_name = table_data.get('sheet_name', table_data.get('table_number', 'unknown'))
                    all_columns[f"{table['filename']}_{table_name}"] = columns
        return all_columns

    def find_common_columns(self, table_structures: Dict[str, List[str]]) -> List[str]:
        """Find columns that appear in multiple tables."""
        column_frequency = {}
        for columns in table_structures.values():
            for col in columns:
                column_frequency[col.lower()] = column_frequency.get(col.lower(), 0) + 1
        
        # Consider columns that appear in at least 2 tables as common
        common_columns = [col for col, freq in column_frequency.items() if freq >= 2]
        return common_columns

    def combine_tables(self, all_data: List[Dict[str, Any]], common_columns: List[str]) -> pd.DataFrame:
        """Combine tables based on common columns."""
        combined_data = []
        
        for file_data in all_data:
            filename = file_data['filename']
            for table in file_data['tables']:
                table_name = table.get('sheet_name', table.get('table_number', 'unknown'))
                for row in table['data']:
                    processed_row = {
                        'source_file': filename,
                        'table_name': table_name
                    }
                    
                    # Add data for common columns
                    for col in common_columns:
                        # Try to find the column with case-insensitive matching
                        matching_col = next(
                            (k for k in row.keys() if k.lower() == col.lower()),
                            None
                        )
                        processed_row[col] = row.get(matching_col, None)
                    
                    combined_data.append(processed_row)
        
        return pd.DataFrame(combined_data)

    def process_tables(self) -> Dict[str, Any]:
        """Process and combine all tables from JSON files."""
        try:
            # Load all JSON files
            all_data = self.load_json_files()
            if not all_data:
                return {
                    'status': 'error',
                    'message': 'No processed files found'
                }

            # Analyze table structures
            table_structures = self.analyze_table_structure(all_data)
            
            # Find common columns
            common_columns = self.find_common_columns(table_structures)
            
            if not common_columns:
                return {
                    'status': 'error',
                    'message': 'No common columns found between tables'
                }

            # Combine tables
            combined_df = self.combine_tables(all_data, common_columns)
            
            # Save the combined result
            output_path = self.processed_dir / 'combined_result.json'
            result_dict = {
                'common_columns': common_columns,
                'table_structures': table_structures,
                'combined_data': combined_df.to_dict(orient='records')
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)

            return {
                'status': 'success',
                'message': 'Successfully combined and analyzed tables',
                'output_file': str(output_path),
                'summary': {
                    'total_files': len(all_data),
                    'common_columns': common_columns,
                    'total_rows': len(combined_df)
                }
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error processing tables: {str(e)}'
            } 