"""Dataset Loader - Warmup version (auto-adapts column names)"""

import csv
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class WarmupCase:
    """Single Warmup dataset record"""
    statement: str
    rating: str
    full_analysis: str
    row_number: int  # For tracking progress


class WarmupDatasetLoader:
    """Warmup Dataset Loader - Supports multiple column name formats"""
    
    def __init__(self, csv_path: str = "data/warmup.csv"):
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.csv_path}")
    
    def _detect_delimiter(self) -> str:
        """Auto-detect CSV delimiter"""
        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
            # Detect comma, semicolon, or tab
            if '\t' in first_line:
                return '\t'
            elif ';' in first_line:
                return ';'
            else:
                return ','
    
    def _map_column_names(self, headers: List[str]) -> Dict[str, str]:
        """
        Map various possible column names to standard column names
        Returns: {standard_name: actual_name}
        """
        # Remove BOM and spaces
        headers = [h.strip().strip('\ufeff') for h in headers]
        
        column_map = {}
        
        # Possible Statement column names
        statement_variants = [
            'Statement', 'statement', 'STATEMENT',
            'Claim', 'claim', 'CLAIM',
            'Text', 'text', 'TEXT',
            'Statement ', ' Statement'
        ]
        
        # Possible Rating column names
        rating_variants = [
            'Rating', 'rating', 'RATING',
            'Label', 'label', 'LABEL',
            'Verdict', 'verdict', 'VERDICT',
            'Truth', 'truth', 'TRUTH',
            'Rating ', ' Rating'
        ]
        
        # Possible Full_Analysis column names
        analysis_variants = [
            'Full_Analysis', 'full_analysis', 'FULL_ANALYSIS',
            'Analysis', 'analysis', 'ANALYSIS',
            'Explanation', 'explanation', 'EXPLANATION',
            'Justification', 'justification',
            'Full Analysis', 'full analysis',
            'Full_Analysis ', ' Full_Analysis'
        ]
        
        # Map Statement
        for variant in statement_variants:
            if variant in headers:
                column_map['statement'] = variant
                break
        
        # Map Rating
        for variant in rating_variants:
            if variant in headers:
                column_map['rating'] = variant
                break
        
        # Map Full_Analysis
        for variant in analysis_variants:
            if variant in headers:
                column_map['full_analysis'] = variant
                break
        
        return column_map
    
    def load_warmup_dataset(self) -> List[WarmupCase]:
        """Load warmup.csv dataset"""
        cases = []
        
        try:
            # Try multiple encodings
            encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'latin-1']
            csv_data = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(self.csv_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        csv_data = content
                        used_encoding = encoding
                        break
                except UnicodeDecodeError:
                    continue
            
            if csv_data is None:
                raise ValueError("Unable to read CSV file with any known encoding")
            
            print(f"Using encoding: {used_encoding}")
            
            # Detect delimiter
            delimiter = self._detect_delimiter()
            print(f"Detected delimiter: {repr(delimiter)}")
            
            # Parse CSV
            from io import StringIO
            csv_reader = csv.DictReader(StringIO(csv_data), delimiter=delimiter)
            
            # Get headers
            headers = csv_reader.fieldnames
            if not headers:
                raise ValueError("CSV file is empty or has invalid format")
            
            print(f"Detected columns: {headers}")
            
            # Map column names
            column_map = self._map_column_names(headers)
            print(f"Column mapping: {column_map}")
            
            # Check if all required columns are found
            required = ['statement', 'rating', 'full_analysis']
            missing = [col for col in required if col not in column_map]
            
            if missing:
                print(f"\nError: Unable to find corresponding column names for:")
                for col in missing:
                    print(f"   - {col}")
                print(f"\nActual CSV columns: {headers}")
                print(f"\nPlease ensure CSV file contains the following columns:")
                print(f"   1. Statement / Claim / Text")
                print(f"   2. Rating / Label / Verdict")
                print(f"   3. Full_Analysis / Analysis / Explanation")
                raise ValueError(f"CSV file missing required columns: {missing}")
            
            # Read data
            for idx, row in enumerate(csv_reader, start=1):
                try:
                    case = WarmupCase(
                        statement=row[column_map['statement']].strip(),
                        rating=row[column_map['rating']].strip(),
                        full_analysis=row[column_map['full_analysis']].strip(),
                        row_number=idx
                    )
                    
                    # Skip empty rows
                    if not case.statement:
                        continue
                    
                    cases.append(case)
                    
                except KeyError as e:
                    print(f"Warning: Row {idx} has incomplete data, skipping: {e}")
                    continue
            
            print(f"Successfully loaded {len(cases)} records")
            
            # Show first 2 records as preview
            if cases:
                print(f"\nData Preview (first 2 records):")
                for i, case in enumerate(cases[:2], 1):
                    print(f"\n  Case {i}:")
                    print(f"    Statement: {case.statement[:80]}...")
                    print(f"    Rating: {case.rating}")
                    print(f"    Analysis: {case.full_analysis[:80]}...")
            
            return cases
            
        except Exception as e:
            print(f"\nFailed to load dataset: {e}")
            print(f"\nDebug info:")
            print(f"  File path: {self.csv_path}")
            print(f"  File exists: {self.csv_path.exists()}")
            if self.csv_path.exists():
                print(f"  File size: {self.csv_path.stat().st_size} bytes")
            raise
    
    def get_case_by_index(self, cases: List[WarmupCase], index: int) -> WarmupCase:
        """Get case by index"""
        if 0 <= index < len(cases):
            return cases[index]
        else:
            raise IndexError(f"Index {index} out of range [0, {len(cases)-1}]")
