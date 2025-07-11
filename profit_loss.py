import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

def parse_year(year_str):
    """Convert a year string to a readable format."""
    try:
        year = int(year_str[:4])
        month = int(year_str[4:])
        return datetime(year, month, 1).strftime('%b-%Y')
    except:
        return year_str

def load_profit_loss_file(file):
    """Load and preprocess the Profit and Loss Excel file."""
    try:
        df = pd.read_excel(file, engine='xlrd', skiprows=5, header=None)
        year_row_idx = df.index[df.iloc[:, 0].str.match('Year', na=False)].tolist()[0]
        years = df.iloc[year_row_idx, 1:].dropna().tolist()
        parsed_years = [parse_year(str(y)) for y in years]
        data_start_idx = df.index[df.iloc[:, 0].str.contains('INCOME :', na=False)].tolist()[0] + 1
        data_df = df.iloc[data_start_idx:].reset_index(drop=True)
        data_df.set_index(data_df.columns[0], inplace=True)
        data_df = data_df.iloc[:, 1:len(years) + 1]
        data_df.columns = parsed_years
        data_df = data_df.apply(pd.to_numeric, errors='coerce').fillna(0)
        return data_df
    except Exception as e:
        print(f"Error loading Profit and Loss file: {e}")
        return None

def rearrange_data(df):
    """Rearrange the data with years as rows and metrics as columns."""
    if df is None:
        return None
    return df.T

def analyze_profit_loss(df):
    """Analyze the Profit and Loss data, calculating growth rates and margins."""
    if df is None:
        return None
    analysis = {}
    key_metrics = ['Net Sales', 'Operating Profit', 'Reported Net Profit']
    for metric in key_metrics:
        if metric in df.columns:
            growth = df[metric].pct_change() * 100
            analysis[f'{metric} YoY Growth (%)'] = growth
    if 'Operating Profit' in df.columns and 'Net Sales' in df.columns:
        analysis['Operating Profit Margin (%)'] = (df['Operating Profit'] / df['Net Sales']) * 100
    return pd.DataFrame(analysis)

def visualize_trends(df):
    """Visualize trends in Profit and Loss data."""
    if df is None:
        return None
    key_metrics = ['Net Sales', 'Operating Profit', 'Reported Net Profit']
    fig, ax = plt.subplots(figsize=(12, 6))
    for metric in key_metrics:
        if metric in df.columns:
            ax.plot(df.index, df[metric], label=metric, marker='o')
    ax.set_title('Profit & Loss Trends Over Time')
    ax.set_xlabel('Year')
    ax.set_ylabel('Amount (Rs in)')
    ax.legend()
    ax.grid(True)
    ax.set_xticks(df.index)
    ax.set_xticklabels(df.index, rotation=45)
    plt.tight_layout()
    return fig

def process_profit_loss_file(file):
    """Tie together all steps for Profit and Loss analysis."""
    profit_loss_df = load_profit_loss_file(file)
    if profit_loss_df is None:
        return None, None, None, None
    rearranged_df = rearrange_data(profit_loss_df)
    analysis_df = analyze_profit_loss(rearranged_df)
    fig = visualize_trends(rearranged_df)
    return profit_loss_df, rearranged_df, analysis_df, fig
