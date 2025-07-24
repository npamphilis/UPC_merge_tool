
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="UPC Merge Tool", layout="wide")

st.title("🔄 UPC Merge Tool for Fetch Implementation Team")
st.markdown("""
Upload your cleaned UPC list and Partner Dashboard product file.
This tool will:
- Identify which UPCs are **new**
- Merge them into the existing product file
- Preserve leading zeros
- Let you download the result
""")

# File upload section
upc_file = st.file_uploader("📤 Upload Cleaned UPC List", type=["xlsx"])
partner_file = st.file_uploader("📤 Upload Partner Product File", type=["xlsx"])

if upc_file and partner_file:
    # Read files
    upc_df = pd.read_excel(upc_file)
    partner_df = pd.read_excel(partner_file)

    # Standardize barcode formats
    upc_df['BARCODE'] = upc_df['BARCODE'].astype(str).str.zfill(12)
    partner_df['barcode'] = partner_df['barcode'].astype(str).str.zfill(12)

    # Compare
    existing_barcodes = set(partner_df['barcode'])
    upc_df['STATUS'] = upc_df['BARCODE'].apply(lambda x: 'Existing' if x in existing_barcodes else 'New')
    new_upcs_df = upc_df[upc_df['STATUS'] == 'New']

    st.subheader("🆕 New Products Identified")
    st.write(new_upcs_df)

    # Format for merge
    new_rows = pd.DataFrame({
        'barcode': new_upcs_df['BARCODE'],
        'bh2Brand': new_upcs_df['BRAND'].str.upper(),
        'name': new_upcs_df['DESCRIPTION'],
        'description': new_upcs_df['DESCRIPTION'],
        'ch1Department': new_upcs_df['CATEGORY_1'].str.upper(),
        'ch2Category': new_upcs_df['CATEGORY_2'].str.upper(),
        'ch3Segment': new_upcs_df['CATEGORY_3'].str.upper(),
        'partnerProduct': 'Y',
        'awardPoints': 'N'
    })

    # Match original schema
    for col in partner_df.columns:
        if col not in new_rows.columns:
            new_rows[col] = None
    new_rows = new_rows[partner_df.columns]

    # Final merge
    merged_df = pd.concat([partner_df, new_rows], ignore_index=True)

    # Download link
    output = BytesIO()
    merged_df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label="📥 Download Merged Product File",
        data=output,
        file_name="merged_partner_file.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
