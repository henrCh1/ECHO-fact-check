"""Benchmark Dataset Loader"""

import csv
from pathlib import Path
from typing import List
from dataclasses import dataclass

@dataclass
class BenchmarkCase:
    """Benchmark dataset single record"""
    statement: str
    rating: str  # 'True' or 'False' (for evaluation, not given to Agent)
    row_number: int

class BenchmarkLoader:
    """Benchmark Dataset Loader"""
    
    def __init__(self, csv_path: str = "data/benchmark.csv"):
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Benchmark dataset file not found: {self.csv_path}")
    
    def _detect_delimiter(self) -> str:
        """Auto-detect CSV delimiter"""
        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
            if '\t' in first_line:
                return '\t'
            elif ';' in first_line:
                return ';'
            else:
                return ','
    
    def _normalize_rating(self, rating: str) -> str:
        """Normalize Rating format"""
        rating_clean = rating.strip().lower()
        
        if rating_clean in ['true', '1', 'yes', 't']:
            return 'True'
        elif rating_clean in ['false', '0', 'no', 'f']:
            return 'False'
        else:
            # If unrecognized, return original and warn
            print(f"⚠️  Warning: Unrecognized Rating value: '{rating}'")
            return rating.strip()
    
    def load_benchmark_dataset(self) -> List[BenchmarkCase]:
        """Load benchmark.csv dataset"""
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
                raise ValueError("Cannot read CSV file with any known encoding")
            
            print(f"✅ Using encoding: {used_encoding}")
            
            # Detect delimiter
            delimiter = self._detect_delimiter()
            print(f"✅ Detected delimiter: {repr(delimiter)}")
            
            # Parse CSV
            from io import StringIO
            csv_reader = csv.DictReader(StringIO(csv_data), delimiter=delimiter)
            
            # Get headers
            headers = csv_reader.fieldnames
            if not headers:
                raise ValueError("CSV file is empty or malformed")
            
            # Clean headers (remove BOM and spaces)
            headers = [h.strip().strip('\ufeff') for h in headers]
            print(f"✅ Detected columns: {headers}")
            
            # Find Statement and Rating columns
            statement_col = None
            rating_col = None
            
            for h in headers:
                h_lower = h.lower()
                if h_lower in ['statement', 'claim', 'text']:
                    statement_col = h
                elif h_lower in ['rating', 'label', 'truth', 'ground_truth']:
                    rating_col = h
            
            if not statement_col:
                raise ValueError(f"Cannot find Statement column. Actual columns: {headers}")
            if not rating_col:
                raise ValueError(f"Cannot find Rating column. Actual columns: {headers}")
            
            print(f"✅ Column mapping: Statement='{statement_col}', Rating='{rating_col}'")
            
            # Read data
            for idx, row in enumerate(csv_reader, start=1):
                try:
                    statement = row[statement_col].strip()
                    rating = self._normalize_rating(row[rating_col])
                    
                    # Skip empty rows
                    if not statement:
                        continue
                    
                    case = BenchmarkCase(
                        statement=statement,
                        rating=rating,
                        row_number=idx
                    )
                    cases.append(case)
                    
                except KeyError as e:
                    print(f"⚠️  Warning: Row {idx} data incomplete, skipping: {e}")
                    continue
            
            print(f"✅ Successfully loaded {len(cases)} records")
            
            # Show first 2 records as preview
            if cases:
                print(f"\n📋 Data preview (first 2 records):")
                for i, case in enumerate(cases[:2], 1):
                    print(f"\n  Case {i}:")
                    print(f"    Statement: {case.statement[:80]}...")
                    print(f"    Rating: {case.rating}")
            
            # Statistics on Rating distribution
            true_count = sum(1 for c in cases if c.rating == 'True')
            false_count = sum(1 for c in cases if c.rating == 'False')
            print(f"\n📊 Data distribution:")
            print(f"    True: {true_count} ({true_count/len(cases)*100:.1f}%)")
            print(f"    False: {false_count} ({false_count/len(cases)*100:.1f}%)")
            
            return cases
            
        except Exception as e:
            print(f"\n❌ Failed to load dataset: {e}")
            print(f"\nDebug info:")
            print(f"  File path: {self.csv_path}")
            print(f"  File exists: {self.csv_path.exists()}")
            if self.csv_path.exists():
                print(f"  File size: {self.csv_path.stat().st_size} bytes")
            raise