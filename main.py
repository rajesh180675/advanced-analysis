import streamlit as st
from cash_flow import process_cash_flow_file
from profit_loss import process_profit_loss_file
from balance_sheet import process_balance_sheet_file
from typing import Optional

# Set up the Streamlit app
st.set_page_config(page_title="Financial Analysis App", layout="wide")
st.title("Financial Analysis App")
st.write("This app allows you to analyze financial data from Excel files for Cash Flow, Profit and Loss, or Balance Sheet.")
st.write("Select the analysis type and upload the corresponding Excel file.")

# Dropdown to select analysis type
analysis_type = st.selectbox("Select Analysis Type", ["Cash Flow", "Profit and Loss", "Balance Sheet"])

# Dictionary mapping analysis types to their processing functions
def get_process_function(analysis_type: str):
    return {
        "Cash Flow": process_cash_flow_file,
        "Profit and Loss": process_profit_loss_file,
        "Balance Sheet": process_balance_sheet_file
    }[analysis_type]

# File uploader with dynamic label
uploaded_file = st.file_uploader(f"Upload {analysis_type} Excel File", type=["xls", "xlsx"])

# Process the uploaded file and display results
def display_results(df1: Optional[object], df2: Optional[object], df3: Optional[object], fig: Optional[object]):
    if df1 is not None:
        st.subheader("Preprocessed Data")
        st.dataframe(df1)
        st.subheader("Rearranged Data")
        st.dataframe(df2)
        st.subheader("Financial Analysis")
        st.dataframe(df3)
        st.subheader("Trends")
        st.pyplot(fig)
    else:
        st.error("Error processing the file. Please check the file format.")

if uploaded_file is not None:
    with st.spinner("Processing file..."):
        process_func = get_process_function(analysis_type)
        try:
            df1, df2, df3, fig = process_func(uploaded_file)
            display_results(df1, df2, df3, fig)
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
