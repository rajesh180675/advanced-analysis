import pandas as pd
from datetime import datetime
from typing import Optional

def parse_year(year_str: str) -> str:
    """
    Convert a year string (e.g., '201103') to a readable format (e.g., 'Mar-2011').
    Returns the original string if parsing fails.
    """
    try:
        year = int(year_str[:4])
        month = int(year_str[4:])
        return datetime(year, month, 1).strftime('%b-%Y')
    except Exception:
        return year_str

def rearrange_data(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Rearrange the data with years as rows and metrics as columns.
    Returns None if input is None.
    """
    if df is None:
        return None
    return df.T