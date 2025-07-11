import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple
from utils import parse_year, rearrange_data

def load_cash_flow_file(file) -> Optional[pd.DataFrame]:
    """Load and preprocess the Cash Flow Excel file."""
    try:
        df = pd.read_excel(file, engine='xlrd', skiprows=5, header=None)
        year_row_idx = df.index[df.iloc[:, 0].str.match('Year', na=False)].tolist()[0]
        years = df.iloc[year_row_idx, 1:].dropna().tolist()
        parsed_years = [parse_year(str(y)) for y in years]
        data_start_idx = df.index[df.iloc[:, 0].str.contains('Cash Flow Summary', na=False)].tolist()[0] + 2
        data_df = df.iloc[data_start_idx:].reset_index(drop=True)
        data_df.set_index(data_df.columns[0], inplace=True)
        data_df = data_df.iloc[:, 1:len(years) + 1]
        data_df.columns = parsed_years
        data_df = data_df.apply(pd.to_numeric, errors='coerce').fillna(0)
        return data_df
    except Exception as e:
        print(f"Error loading Cash Flow file: {e}")
        return None

def analyze_cash_flow(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Analyze the Cash Flow data, calculating growth rates and ratios."""
    if df is None:
        return None
    analysis = {}
    key_metrics = ['Net Cash from Operating Activities', 'Net Cash Used in Investing Activities', 'Net Cash Used in Financing Activities']
    for metric in key_metrics:
        if metric in df.columns:
            growth = df[metric].pct_change() * 100
            analysis[f'{metric} YoY Growth (%)'] = growth
    if 'Net Cash from Operating Activities' in df.columns and 'Net Cash Used in Investing Activities' in df.columns:
        analysis['Op. CF to Inv. CF Ratio'] = df['Net Cash from Operating Activities'] / df['Net Cash Used in Investing Activities'].replace(0, np.nan)
    return pd.DataFrame(analysis)

def visualize_trends(df: Optional[pd.DataFrame]):
    """Visualize trends in Cash Flow data."""
    if df is None:
        return None
    key_metrics = ['Net Cash from Operating Activities', 'Net Cash Used in Investing Activities', 'Net Cash Used in Financing Activities']
    fig, ax = plt.subplots(figsize=(12, 6))
    for metric in key_metrics:
        if metric in df.columns:
            ax.plot(df.index, df[metric], label=metric, marker='o')
    ax.set_title('Cash Flow Trends Over Time')
    ax.set_xlabel('Year')
    ax.set_ylabel('Amount (Rs in)')
    ax.legend()
    ax.grid(True)
    ax.set_xticks(df.index)
    ax.set_xticklabels(df.index, rotation=45)
    plt.tight_layout()
    return fig

def process_cash_flow_file(file) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[plt.Figure]]:
    """Tie together all steps for Cash Flow analysis."""
    cash_flow_df = load_cash_flow_file(file)
    if cash_flow_df is None:
        return None, None, None, None
    rearranged_df = rearrange_data(cash_flow_df)
    analysis_df = analyze_cash_flow(rearranged_df)
    fig = visualize_trends(rearranged_df)
    return cash_flow_df, rearranged_df, analysis_df, fig
