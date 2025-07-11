import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple
from utils import parse_year

def load_balance_sheet_file(file) -> Optional[pd.DataFrame]:
    """Load and preprocess the Balance Sheet Excel file."""
    try:
        df = pd.read_excel(file, engine='xlrd', header=None)
        year_row_idx = df.index[df.iloc[:, 0].str.match('Year', na=False)].tolist()[0]
        header = df.iloc[year_row_idx]
        data_df = df.iloc[year_row_idx + 1:].reset_index(drop=True)
        data_df.columns = header
        data_df.rename(columns={'Year': 'Item'}, inplace=True)
        year_cols = data_df.columns[1:]
        data_df = data_df.dropna(subset=year_cols, how='all')
        data_df.columns = ['Item'] + [parse_year(str(col)) for col in year_cols]
        for col in data_df.columns[1:]:
            data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
        data_df.fillna(0, inplace=True)
        return data_df
    except Exception as e:
        print(f"Error loading Balance Sheet file: {e}")
        return None

def rearrange_data(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Rearrange the data with years as rows and metrics as columns for balance sheet."""
    if df is None:
        return None
    return df.set_index('Item').T

def analyze_balance_sheet(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Analyze the Balance Sheet data, calculating ratios and growth rates."""
    if df is None:
        return None
    analysis = {}
    if 'Total Current Assets' in df.columns and 'Total Current Liabilities' in df.columns:
        analysis['Current Ratio'] = df['Total Current Assets'] / df['Total Current Liabilities']
    if 'Total Debt' in df.columns and 'Total Shareholders Funds' in df.columns:
        analysis['Debt-to-Equity Ratio'] = df['Total Debt'] / df['Total Shareholders Funds']
    key_items = ['Total Assets', 'Total Liabilities', 'Total Shareholders Funds']
    for item in key_items:
        if item in df.columns:
            growth = df[item].pct_change() * 100
            analysis[f'{item} YoY Growth (%)'] = growth
    return pd.DataFrame(analysis)

def visualize_trends(df: Optional[pd.DataFrame]):
    """Visualize trends in Balance Sheet data."""
    if df is None:
        return None
    key_items = ['Total Assets', 'Total Liabilities', 'Total Shareholders Funds']
    fig, ax = plt.subplots(figsize=(12, 6))
    for item in key_items:
        if item in df.columns:
            ax.plot(df.index, df[item], label=item, marker='o')
    ax.set_title('Balance Sheet Trends Over Time')
    ax.set_xlabel('Year')
    ax.set_ylabel('Amount (Rs in)')
    ax.legend()
    ax.grid(True)
    ax.set_xticks(df.index)
    ax.set_xticklabels(df.index, rotation=45)
    plt.tight_layout()
    return fig

def process_balance_sheet_file(file) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[plt.Figure]]:
    """Tie together all steps for Balance Sheet analysis."""
    balance_sheet_df = load_balance_sheet_file(file)
    if balance_sheet_df is None:
        return None, None, None, None
    rearranged_df = rearrange_data(balance_sheet_df)
    analysis_df = analyze_balance_sheet(rearranged_df)
    fig = visualize_trends(rearranged_df)
    return balance_sheet_df, rearranged_df, analysis_df, fig
