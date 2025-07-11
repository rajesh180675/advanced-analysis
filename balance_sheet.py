import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import io
import re

def parse_year(year_str):
    """Convert a year string to a readable format."""
    try:
        if isinstance(year_str, (int, float)):
            year_str = str(int(year_str))
        
        year_str = str(year_str).strip()
        
        # Handle different year formats
        if len(year_str) == 6:  # Format: 201103 (YYYYMM)
            year = int(year_str[:4])
            month = int(year_str[4:])
            return datetime(year, month, 1).strftime('%b-%Y')
        elif len(year_str) == 4:  # Format: 2011 (YYYY)
            return f"FY-{year_str}"
        elif len(year_str) == 8:  # Format: 20110331 (YYYYMMDD)
            year = int(year_str[:4])
            month = int(year_str[4:6])
            return datetime(year, month, 1).strftime('%b-%Y')
        else:
            # Try to extract year from string
            year_match = re.search(r'\d{4}', year_str)
            if year_match:
                return f"FY-{year_match.group()}"
            return year_str
    except Exception as e:
        print(f"Warning: Could not parse year '{year_str}': {e}")
        return str(year_str)

def smart_file_reader(file, file_extension):
    """Smart file reader that handles multiple formats"""
    try:
        if file_extension in ['.xls', '.xlsx']:
            # Try different engines for Excel files
            engines = ['openpyxl', 'xlrd', 'calamine'] if file_extension == '.xlsx' else ['xlrd', 'openpyxl']
            
            for engine in engines:
                try:
                    df = pd.read_excel(file, engine=engine, header=None)
                    if not df.empty:
                        return df, None
                except Exception as e:
                    continue
            return None, "Failed to read Excel file with any engine"
            
        elif file_extension == '.csv':
            # Try different delimiters for CSV
            for delimiter in [',', ';', '|']:
                try:
                    file.seek(0)
                    df = pd.read_csv(file, delimiter=delimiter, header=None)
                    if df.shape[1] > 1:  # Must have multiple columns
                        return df, None
                except Exception:
                    continue
            return None, "Failed to parse CSV file"
            
        elif file_extension == '.gp':
            # Handle GP files (assume they are tab or comma delimited)
            file.seek(0)
            content = file.read().decode('utf-8')
            
            # Try to determine delimiter
            lines = content.split('\n')[:5]
            delimiters = ['\t', ',', ';', '|']
            best_delimiter = '\t'
            max_columns = 0
            
            for delimiter in delimiters:
                for line in lines:
                    if line.strip():
                        columns = len(line.split(delimiter))
                        if columns > max_columns:
                            max_columns = columns
                            best_delimiter = delimiter
            
            # Read with best delimiter
            file.seek(0)
            df = pd.read_csv(io.StringIO(content), delimiter=best_delimiter, header=None)
            return df, None
            
        elif file_extension in ['.txt', '.tsv']:
            # Handle text files
            file.seek(0)
            content = file.read().decode('utf-8')
            delimiter = '\t' if file_extension == '.tsv' else None
            
            # Auto-detect delimiter if not specified
            if delimiter is None:
                first_line = content.split('\n')[0]
                if '\t' in first_line:
                    delimiter = '\t'
                elif ',' in first_line:
                    delimiter = ','
                elif ';' in first_line:
                    delimiter = ';'
                else:
                    delimiter = '\s+'  # Whitespace
            
            df = pd.read_csv(io.StringIO(content), delimiter=delimiter, header=None)
            return df, None
            
        else:
            return None, f"Unsupported file format: {file_extension}"
            
    except Exception as e:
        return None, f"Error reading file: {str(e)}"

def find_data_structure(df):
    """Intelligently find year row and data start in the dataframe"""
    year_patterns = [
        r'year',
        r'\d{4}',  # 4-digit year
        r'\d{6}',  # YYYYMM format
        r'fy.*\d{4}',  # FY2023 format
        r'\d{4}-\d{2}',  # 2023-24 format
    ]
    
    balance_sheet_patterns = [
        r'balance.*sheet',
        r'assets',
        r'liabilities',
        r'equity',
        r'current.*assets',
        r'total.*assets',
        r'shareholders.*funds',
    ]
    
    year_row_idx = None
    data_start_idx = None
    
    # Search for year row
    for idx, row in df.iterrows():
        row_str = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
        
        for pattern in year_patterns:
            if re.search(pattern, row_str, re.IGNORECASE):
                year_row_idx = idx
                break
        
        if year_row_idx is not None:
            break
    
    # For balance sheet, data often starts right after the year row
    if year_row_idx is not None:
        data_start_idx = year_row_idx + 1
    else:
        # Search for balance sheet data indicators
        for idx, row in df.iterrows():
            row_str = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
            
            for pattern in balance_sheet_patterns:
                if re.search(pattern, row_str, re.IGNORECASE):
                    data_start_idx = idx
                    break
            
            if data_start_idx is not None:
                break
    
    return year_row_idx, data_start_idx

def load_balance_sheet_file(file, file_extension='.xls'):
    """Enhanced load function that handles multiple file formats."""
    try:
        # Read file with smart reader
        df, error = smart_file_reader(file, file_extension)
        if df is None:
            print(f"Error reading file: {error}")
            return None
            
        if df.empty:
            print("File is empty or contains no data")
            return None
        
        # Find data structure intelligently
        year_row_idx, data_start_idx = find_data_structure(df)
        
        if year_row_idx is None:
            print("Could not find year information in the file")
            # Try to use first row as years if it contains numbers
            first_row = df.iloc[0]
            numeric_cols = []
            for i, val in enumerate(first_row):
                try:
                    if pd.notna(val) and (isinstance(val, (int, float)) or str(val).isdigit()):
                        numeric_cols.append(i)
                except:
                    continue
            
            if numeric_cols:
                year_row_idx = 0
                data_start_idx = 1
            else:
                print("Warning: No clear year row found, using default structure")
                year_row_idx = 0
                data_start_idx = 1
        
        if data_start_idx is None:
            # Use a reasonable default
            data_start_idx = year_row_idx + 1
            print(f"Warning: No clear data start found, using row {data_start_idx}")
        
        # For balance sheet, process differently since year row becomes header
        header = df.iloc[year_row_idx]
        data_df = df.iloc[data_start_idx:].reset_index(drop=True)
        data_df.columns = header
        
        # Rename first column to 'Item' if it's called 'Year'
        first_col_name = data_df.columns[0]
        if pd.isna(first_col_name) or str(first_col_name).lower() in ['year', 'nan']:
            data_df.rename(columns={first_col_name: 'Item'}, inplace=True)
        
        # Clean up data
        data_df = data_df.dropna(subset=[col for col in data_df.columns[1:] if pd.notna(col)], how='all')
        
        if data_df.empty:
            print("No data found after processing")
            return None
        
        # Process year columns
        year_cols = data_df.columns[1:]
        year_cols = [col for col in year_cols if pd.notna(col)]
        
        if not year_cols:
            print("No year columns found")
            return None
        
        # Parse year column names
        parsed_year_cols = []
        for col in year_cols:
            try:
                parsed_col = parse_year(str(col))
                parsed_year_cols.append(parsed_col)
            except:
                parsed_year_cols.append(str(col))
        
        # Update column names
        new_columns = ['Item'] + parsed_year_cols
        data_df.columns = new_columns[:len(data_df.columns)]
        
        # Convert numeric columns
        for col in data_df.columns[1:]:
            data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
        
        data_df.fillna(0, inplace=True)
        
        # Remove rows with all zeros in year columns
        year_cols_mask = ~(data_df[data_df.columns[1:]] == 0).all(axis=1)
        data_df = data_df[year_cols_mask]
        
        return data_df
        
    except Exception as e:
        print(f"Error loading Balance Sheet file: {e}")
        import traceback
        traceback.print_exc()
        return None

def rearrange_data(df):
    """Rearrange the data with years as rows and metrics as columns."""
    if df is None or df.empty:
        return None
    try:
        return df.set_index('Item').T
    except Exception as e:
        print(f"Error rearranging data: {e}")
        # Try alternative approach
        try:
            first_col = df.columns[0]
            return df.set_index(first_col).T
        except:
            return df

def analyze_balance_sheet(df):
    """Enhanced analysis with flexible metric detection."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    try:
        analysis = {}
        
        # Define possible metric names (case-insensitive)
        metric_patterns = {
            'current_assets': [
                'total current assets',
                'current assets',
                'total ca',
                'current asset'
            ],
            'current_liabilities': [
                'total current liabilities',
                'current liabilities',
                'total cl',
                'current liability'
            ],
            'total_assets': [
                'total assets',
                'total asset',
                'ta'
            ],
            'total_liabilities': [
                'total liabilities',
                'total liability',
                'tl'
            ],
            'shareholders_funds': [
                'total shareholders funds',
                'shareholders funds',
                'shareholders equity',
                'total equity',
                'equity',
                'net worth'
            ],
            'debt': [
                'total debt',
                'total borrowings',
                'debt',
                'borrowings'
            ]
        }
        
        # Find matching columns
        found_metrics = {}
        for category, patterns in metric_patterns.items():
            for col in df.columns:
                col_lower = str(col).lower()
                for pattern in patterns:
                    if pattern in col_lower:
                        found_metrics[category] = col
                        break
                if category in found_metrics:
                    break
        
        # Calculate ratios
        if 'current_assets' in found_metrics and 'current_liabilities' in found_metrics:
            ca_col = found_metrics['current_assets']
            cl_col = found_metrics['current_liabilities']
            
            analysis['Current Ratio'] = (
                df[ca_col] / df[cl_col].replace(0, np.nan)
            )
        
        if 'debt' in found_metrics and 'shareholders_funds' in found_metrics:
            debt_col = found_metrics['debt']
            equity_col = found_metrics['shareholders_funds']
            
            analysis['Debt-to-Equity Ratio'] = (
                df[debt_col] / df[equity_col].replace(0, np.nan)
            )
        
        # Calculate growth rates for key items
        key_items = ['total_assets', 'total_liabilities', 'shareholders_funds']
        for item in key_items:
            if item in found_metrics:
                col_name = found_metrics[item]
                growth = df[col_name].pct_change() * 100
                analysis[f'{col_name} YoY Growth (%)'] = growth
        
        return pd.DataFrame(analysis)
        
    except Exception as e:
        print(f"Error in balance sheet analysis: {e}")
        return pd.DataFrame()

def visualize_trends(df):
    """Enhanced visualization with flexible metric detection."""
    if df is None or df.empty:
        return None
    
    try:
        # Find key metrics using pattern matching
        metric_patterns = [
            r'.*total.*assets.*',
            r'.*total.*liabilities.*',
            r'.*shareholders.*funds.*',
            r'.*equity.*',
            r'.*current.*assets.*',
            r'.*current.*liabilities.*'
        ]
        
        found_metrics = []
        for col in df.columns:
            col_lower = str(col).lower()
            for pattern in metric_patterns:
                if re.search(pattern, col_lower):
                    found_metrics.append(col)
                    break
        
        # Limit to first 5 metrics to avoid cluttered chart
        found_metrics = found_metrics[:5]
        
        if not found_metrics:
            # If no patterns match, use first few numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            found_metrics = numeric_cols[:3]
        
        if not found_metrics:
            print("No suitable metrics found for visualization")
            return None
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for metric in found_metrics:
            if metric in df.columns:
                # Handle potential NaN values
                clean_data = df[metric].dropna()
                if not clean_data.empty:
                    ax.plot(clean_data.index, clean_data.values, 
                           label=metric, marker='o', linewidth=2, markersize=6)
        
        ax.set_title('Balance Sheet Trends Over Time', fontsize=16, fontweight='bold')
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Amount (Rs in)', fontsize=12)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Improve x-axis formatting
        ax.set_xticks(range(len(df.index)))
        ax.set_xticklabels(df.index, rotation=45)
        
        # Add value annotations on data points
        for metric in found_metrics:
            if metric in df.columns:
                clean_data = df[metric].dropna()
                for i, (idx, val) in enumerate(clean_data.items()):
                    if pd.notna(val) and val != 0:
                        ax.annotate(f'{val:.1f}', 
                                  (i, val), 
                                  textcoords="offset points", 
                                  xytext=(0,10), 
                                  ha='center', fontsize=8, alpha=0.7)
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        print(f"Error creating visualization: {e}")
        return None

def process_balance_sheet_file(file, file_extension='.xls'):
    """Enhanced processing function with better error handling."""
    try:
        print(f"Processing balance sheet file with extension: {file_extension}")
        
        balance_sheet_df = load_balance_sheet_file(file, file_extension)
        if balance_sheet_df is None:
            print("Failed to load balance sheet data")
            return None, None, None, None
        
        print(f"Loaded data shape: {balance_sheet_df.shape}")
        
        rearranged_df = rearrange_data(balance_sheet_df)
        if rearranged_df is None:
            print("Failed to rearrange data")
            return balance_sheet_df, None, None, None
        
        analysis_df = analyze_balance_sheet(rearranged_df)
        fig = visualize_trends(rearranged_df)
        
        print("Balance sheet processing completed successfully")
        return balance_sheet_df, rearranged_df, analysis_df, fig
        
    except Exception as e:
        print(f"Error in process_balance_sheet_file: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None
