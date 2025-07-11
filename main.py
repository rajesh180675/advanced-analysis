import streamlit as st
from cash_flow import process_cash_flow_file
from profit_loss import process_profit_loss_file
from balance_sheet import process_balance_sheet_file

# Set up the Streamlit app
st.title("Financial Analysis App")
st.write("This app allows you to analyze financial data from Excel files for Cash Flow, Profit and Loss, or Balance Sheet.")
st.write("Select the analysis type and upload the corresponding Excel file.")

# Dropdown to select analysis type
analysis_type = st.selectbox("Select Analysis Type", ["Cash Flow", "Profit and Loss", "Balance Sheet"])

# Dictionary mapping analysis types to their processing functions
process_functions = {
    "Cash Flow": process_cash_flow_file,
    "Profit and Loss": process_profit_loss_file,
    "Balance Sheet": process_balance_sheet_file
}

# File uploader with dynamic label
uploaded_file = st.file_uploader(f"Upload {analysis_type} Excel File", type=["xls"])

# Process the uploaded file and display results
if uploaded_file is not None:
    process_func = process_functions[analysis_type]
    df1, df2, df3, fig = process_func(uploaded_file)
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
