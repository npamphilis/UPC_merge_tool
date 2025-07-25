
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="🔄 Flexible UPC Merge Tool", layout="wide")

st.title("🔄 UPC Merge Tool (Flexible Version)")
st.markdown("""
This version supports **any cleaned file format**.
Just tell us which columns to use for:
- UPC
- Product name (description)
- Brand
- Department/category

We'll merge the file with your Partner Dashboard product file as usual.
""")

# Upload section
upc_file = st.file_uploader("📤 Upload Cleaned UPC List (any format)", type=["xlsx"])
partner_file = st.file_uploader("📤 Upload Partner Product File (standard format)", type=["xlsx"])

if upc_file and partner_file:
    upc_df = pd.read_excel(upc_file)
    partner_df = pd.read_excel(partner_file)

    st.subheader("🧩 Step 1: Map Your Columns")
    st.write("We detected the following columns from your cleaned UPC list:")
    st.dataframe(upc_df.head())

    columns = upc_df.columns.tolist()

    upc_col = st.selectbox("🔑 Which column contains UPCs?", columns, index=0)
    desc_col = st.selectbox("📝 Which column contains Product Descriptions?", columns, index=1)
    brand_col = st.selectbox("🏷️ Which column contains Brand? (Optional)", ["(None)"] + columns)
    dept_col = st.selectbox("📦 Department / Category 1 (Optional)", ["(None)"] + columns)
    cat2_col = st.selectbox("📁 Category 2 (Optional)", ["(None)"] + columns)
    cat3_col = st.selectbox("📂 Category 3 (Optional)", ["(None)"] + columns)

    if st.button("🚀 Process & Merge Files"):
        # Normalize barcodes
        upc_df[upc_col] = upc_df[upc_col].astype(str).str.zfill(12)
        partner_df['barcode'] = partner_df['barcode'].astype(str).str.zfill(12)

        # Identify new UPCs
        existing_barcodes = set(partner_df['barcode'])
        upc_df['STATUS'] = upc_df[upc_col].apply(lambda x: 'Existing' if x in existing_barcodes else 'New')
        new_upcs_df = upc_df[upc_df['STATUS'] == 'New']

        st.success(f"✅ Found {len(new_upcs_df)} new UPCs not in the Partner Dashboard file.")
        st.write(new_upcs_df)

        # Build new formatted rows
        new_rows = pd.DataFrame({
            'barcode': new_upcs_df[upc_col],
            'bh2Brand': new_upcs_df[brand_col].str.upper() if brand_col != "(None)" else "N/A",
            'name': new_upcs_df[desc_col],
            'description': new_upcs_df[desc_col],
            'ch1Department': new_upcs_df[dept_col].str.upper() if dept_col != "(None)" else "N/A",
            'ch2Category': new_upcs_df[cat2_col].str.upper() if cat2_col != "(None)" else "N/A",
            'ch3Segment': new_upcs_df[cat3_col].str.upper() if cat3_col != "(None)" else "N/A",
            'partnerProduct': 'Y',
            'awardPoints': 'N'
        })

        # Add any missing columns
        for col in partner_df.columns:
            if col not in new_rows.columns:
                new_rows[col] = None
        new_rows = new_rows[partner_df.columns]

        # Merge
        merged_df = pd.concat([partner_df, new_rows], ignore_index=True)

        # Download output
        output = BytesIO()
        merged_df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.download_button(
            label="📥 Download Merged Partner File",
            data=output,
            file_name="merged_flexible_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
