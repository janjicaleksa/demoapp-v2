import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import os
from datetime import datetime

class AIProcessor:
    def __init__(self, processed_dir: str):
        self.processed_dir = Path(processed_dir)
        self.api_key = os.getenv('AZURE_AI_FOUNDRY_API_KEY')
        self.api_endpoint = os.getenv('AZURE_AI_FOUNDRY_ENDPOINT')

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

    def _call_azure_ai_foundry(self, table_data: Dict[str, Any], table_type: str) -> Dict[str, Any]:
        """
        Call Azure AI Foundry API to process table data
        
        Args:
            table_data: Dictionary containing table data
            table_type: Either 'kupci' or 'dobavljaci'
        """
        if not self.api_key or not self.api_endpoint:
            raise ValueError("Azure AI Foundry API key and endpoint must be set in environment variables")

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'table_data': table_data,
            'table_type': table_type
        }

        response = requests.post(
            self.api_endpoint,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            raise Exception(f"Azure AI Foundry API call failed: {response.text}")

        return response.json()

    def process_kupci_table(self, table_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Process Kupci table using Azure AI Foundry
        """
        processed_data = self._call_azure_ai_foundry(table_data, 'kupci')
        df = pd.DataFrame(processed_data['processed_table'])
        
        # Save to Excel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.processed_dir / f'kupci_processed_{timestamp}.xlsx'
        df.to_excel(output_path, index=False)
        
        return df

    def process_dobavljaci_table(self, table_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Process Dobavljaci table using Azure AI Foundry
        """
        processed_data = self._call_azure_ai_foundry(table_data, 'dobavljaci')
        df = pd.DataFrame(processed_data['processed_table'])
        
        # Save to Excel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.processed_dir / f'dobavljaci_processed_{timestamp}.xlsx'
        df.to_excel(output_path, index=False)
        
        return df

    def process_tables_with_ai(self, table_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Process either Kupci or Dobavljaci tables using Azure AI Foundry, or both if table_type is None
        
        Args:
            table_type: Optional; Either 'kupci', 'dobavljaci', or None to process both
        """
        try:
            # Load all JSON files
            all_data = self.load_json_files()
            if not all_data:
                return {
                    'status': 'error',
                    'message': 'No processed files found'
                }

            results = {}
            output_files = {}

            # Process tables based on type
            if table_type is None or table_type.lower() == 'kupci':
                kupci_df = self.process_kupci_table({'tables': all_data})
                results['kupci'] = {
                    'total_rows': len(kupci_df),
                    'processed_columns': list(kupci_df.columns)
                }
                # Save Kupci to Excel
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                kupci_path = self.processed_dir / f'kupci_processed_{timestamp}.xlsx'
                kupci_df.to_excel(kupci_path, index=False)
                output_files['kupci'] = str(kupci_path)

            if table_type is None or table_type.lower() == 'dobavljaci':
                dobavljaci_df = self.process_dobavljaci_table({'tables': all_data})
                results['dobavljaci'] = {
                    'total_rows': len(dobavljaci_df),
                    'processed_columns': list(dobavljaci_df.columns)
                }
                # Save Dobavljaci to Excel
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                dobavljaci_path = self.processed_dir / f'dobavljaci_processed_{timestamp}.xlsx'
                dobavljaci_df.to_excel(dobavljaci_path, index=False)
                output_files['dobavljaci'] = str(dobavljaci_path)

            # If both tables were processed, create a merged file
            if table_type is None and 'kupci' in results and 'dobavljaci' in results:
                # Add a type column to each DataFrame
                kupci_df['type'] = 'kupci'
                dobavljaci_df['type'] = 'dobavljaci'
                
                # Merge the DataFrames
                merged_df = pd.concat([kupci_df, dobavljaci_df], ignore_index=True)
                
                # Save merged result
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                merged_path = self.processed_dir / f'merged_results_{timestamp}.xlsx'
                merged_df.to_excel(merged_path, index=False)
                output_files['merged'] = str(merged_path)

            return {
                'status': 'success',
                'message': 'Successfully processed tables',
                'summary': {
                    'total_files': len(all_data),
                    'results': results,
                    'output_files': output_files
                }
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error processing tables: {str(e)}'
            }

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