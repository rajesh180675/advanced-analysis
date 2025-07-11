import streamlit as st
import pandas as pd
import os
from cash_flow import process_cash_flow_file
from profit_loss import process_profit_loss_file
from balance_sheet import process_balance_sheet_file

def detect_file_format(uploaded_file):
    """Detect and validate file format"""
    if uploaded_file is None:
        return None, "No file uploaded"
    
    filename = uploaded_file.name.lower()
    file_extension = os.path.splitext(filename)[1]
    
    # Supported formats
    supported_formats = {
        '.xls': 'Excel (old format)',
        '.xlsx': 'Excel (new format)', 
        '.csv': 'Comma Separated Values',
        '.gp': 'GP Data Format',
        '.txt': 'Text file',
        '.tsv': 'Tab Separated Values'
    }
    
    if file_extension in supported_formats:
        return file_extension, f"Detected: {supported_formats[file_extension]}"
    else:
        return None, f"Unsupported file format: {file_extension}. Supported formats: {', '.join(supported_formats.keys())}"

def validate_file_content(uploaded_file, file_extension):
    """Validate file content and provide helpful feedback"""
    try:
        # Reset file pointer
        uploaded_file.seek(0)
        
        if file_extension in ['.csv', '.gp', '.txt', '.tsv']:
            # Try to read as text first to check content
            content = uploaded_file.read().decode('utf-8')
            if len(content.strip()) == 0:
                return False, "File appears to be empty"
            
            # Reset for pandas reading
            uploaded_file.seek(0)
            
            # Check if it looks like tabular data
            lines = content.split('\n')[:10]  # Check first 10 lines
            if not any(',' in line or '\t' in line for line in lines if line.strip()):
                return False, "File doesn't appear to contain tabular data (no commas or tabs found)"
                
        elif file_extension in ['.xls', '.xlsx']:
            # For Excel files, try to read with pandas
            uploaded_file.seek(0)
            try:
                df_test = pd.read_excel(uploaded_file, nrows=1)
                if df_test.empty:
                    return False, "Excel file appears to be empty"
            except Exception as e:
                return False, f"Excel file validation failed: {str(e)}"
                
        return True, "File validation passed"
        
    except UnicodeDecodeError:
        return False, "File encoding error - file may be corrupted or in an unsupported encoding"
    except Exception as e:
        return False, f"File validation error: {str(e)}"

# Set up the Streamlit app
st.set_page_config(page_title="Financial Analysis App", page_icon="📊", layout="wide")

st.title("📊 Enhanced Financial Analysis App")
st.write("Upload financial data files in various formats including Excel (.xls, .xlsx), CSV, GP files (.gp), or text files for comprehensive analysis.")

# Create columns for better layout
col1, col2 = st.columns([1, 2])

with col1:
    # Dropdown to select analysis type
    analysis_type = st.selectbox(
        "Select Analysis Type", 
        ["Cash Flow", "Profit and Loss", "Balance Sheet"],
        help="Choose the type of financial analysis you want to perform"
    )

with col2:
    # Enhanced file uploader with multiple format support
    uploaded_file = st.file_uploader(
        f"Upload {analysis_type} File", 
        type=["xls", "xlsx", "csv", "gp", "txt", "tsv"],
        help="Supported formats: Excel (.xls, .xlsx), CSV, GP files (.gp), Text files (.txt, .tsv)"
    )

# Dictionary mapping analysis types to their processing functions
process_functions = {
    "Cash Flow": process_cash_flow_file,
    "Profit and Loss": process_profit_loss_file,
    "Balance Sheet": process_balance_sheet_file
}

# Process the uploaded file with enhanced error handling
if uploaded_file is not None:
    # File format detection
    file_extension, format_message = detect_file_format(uploaded_file)
    
    if file_extension is None:
        st.error(f"❌ {format_message}")
        st.info("Please upload a file in one of the supported formats.")
    else:
        st.success(f"✅ {format_message}")
        
        # File content validation
        is_valid, validation_message = validate_file_content(uploaded_file, file_extension)
        
        if not is_valid:
            st.error(f"❌ File validation failed: {validation_message}")
            st.info("Please check your file and try again.")
        else:
            st.info(f"✅ {validation_message}")
            
            # Reset file pointer before processing
            uploaded_file.seek(0)
            
            # Progress indicator
            with st.spinner(f'Processing {analysis_type} data...'):
                try:
                    process_func = process_functions[analysis_type]
                    df1, df2, df3, fig = process_func(uploaded_file, file_extension)
                    
                    if df1 is not None:
                        st.success("✅ File processed successfully!")
                        
                        # Display results in tabs for better organization
                        tab1, tab2, tab3, tab4 = st.tabs(["📋 Raw Data", "🔄 Processed Data", "📈 Analysis", "📊 Trends"])
                        
                        with tab1:
                            st.subheader("Preprocessed Data")
                            st.dataframe(df1, use_container_width=True)
                            st.download_button(
                                label="Download Raw Data",
                                data=df1.to_csv(index=False),
                                file_name=f"{analysis_type.lower()}_raw_data.csv",
                                mime="text/csv"
                            )
                        
                        with tab2:
                            st.subheader("Rearranged Data")
                            st.dataframe(df2, use_container_width=True)
                            st.download_button(
                                label="Download Processed Data",
                                data=df2.to_csv(),
                                file_name=f"{analysis_type.lower()}_processed_data.csv",
                                mime="text/csv"
                            )
                        
                        with tab3:
                            st.subheader("Financial Analysis")
                            st.dataframe(df3, use_container_width=True)
                            if not df3.empty:
                                st.download_button(
                                    label="Download Analysis",
                                    data=df3.to_csv(),
                                    file_name=f"{analysis_type.lower()}_analysis.csv",
                                    mime="text/csv"
                                )
                        
                        with tab4:
                            st.subheader("Trends Visualization")
                            if fig is not None:
                                st.pyplot(fig)
                            else:
                                st.info("No trend visualization available for this data.")
                    else:
                        st.error("❌ Error processing the file. Please check the file format and structure.")
                        st.info("""
                        **Troubleshooting tips:**
                        - Ensure your file contains the expected financial data structure
                        - Check that year/date columns are properly formatted
                        - Verify that the file is not corrupted
                        - For .gp files, ensure they follow CSV-like structure
                        """)
                        
                except Exception as e:
                    st.error(f"❌ Unexpected error occurred: {str(e)}")
                    st.info("Please contact support if this error persists.")
                    st.expander("Error Details", expanded=False).code(str(e))

# Add sidebar with information
with st.sidebar:
    st.header("📋 File Format Guide")
    st.write("""
    **Supported Formats:**
    - **.xls/.xlsx**: Excel files
    - **.csv**: Comma-separated values
    - **.gp**: GP data format files  
    - **.txt/.tsv**: Text files
    
    **Data Structure Requirements:**
    - Must contain year/date information
    - Should have financial metrics in rows or columns
    - First few rows may contain metadata
    """)
    
    st.header("🆘 Need Help?")
    st.write("""
    If you encounter issues:
    1. Check file format compatibility
    2. Verify data structure
    3. Ensure file is not corrupted
    4. Try converting to CSV format
    """)
