
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="🔄 UPC Merge Tool (Auto-Mapping)", layout="wide")
st.title("🔄 UPC Merge Tool (Auto-Mapping Version)")

st.markdown("""
This upgraded version:
- Automatically detects common column names like `barcode`, `UPC`, `Product / FIDO ID`, etc.
- Fallbacks to manual mapping **only if needed**
- Merges cleaned UPCs into a Partner Dashboard file with zero friction!
""")

# Common alias lists
UPC_ALIASES = ['barcode', 'Barcode', 'UPC', 'BARCODE']
DESC_ALIASES = ['description', 'name', 'Product / FIDO ID', 'Product Name', 'Product Description']
BRAND_ALIASES = ['brand', 'Brand', 'BRAND']
CAT1_ALIASES = ['department', 'Department', 'CATEGORY_1', 'Category 1']
CAT2_ALIASES = ['category', 'Category', 'CATEGORY_2', 'Category 2']
CAT3_ALIASES = ['segment', 'Segment', 'CATEGORY_3', 'Category 3']

def detect_column(columns, aliases):
    for alias in aliases:
        if alias in columns:
            return alias
    return None

# Upload section
upc_file = st.file_uploader("📤 Upload Cleaned UPC List", type=["xlsx"])
partner_file = st.file_uploader("📤 Upload Partner Product File", type=["xlsx"])

if upc_file and partner_file:
    upc_df = pd.read_excel(upc_file)
    partner_df = pd.read_excel(partner_file)

    st.subheader("🧠 Auto-Mapping Detected:")
    columns = upc_df.columns.tolist()

    # Attempt auto-detection
    upc_col = detect_column(columns, UPC_ALIASES)
    desc_col = detect_column(columns, DESC_ALIASES)
    brand_col = detect_column(columns, BRAND_ALIASES)
    dept_col = detect_column(columns, CAT1_ALIASES)
    cat2_col = detect_column(columns, CAT2_ALIASES)
    cat3_col = detect_column(columns, CAT3_ALIASES)

    st.markdown("#### Column Mapping Overview")
    st.write(f"🔑 **UPC Column**: `{upc_col}`" if upc_col else "🔑 UPC Column: ❌ Not found — please ensure one of: " + ', '.join(UPC_ALIASES))
    st.write(f"📝 **Description Column**: `{desc_col}`" if desc_col else "📝 Description Column: ❌ Not found")
    st.write(f"🏷️ **Brand Column**: `{brand_col}`" if brand_col else "🏷️ Brand Column: ❌ Not found")
    st.write(f"📦 **Department**: `{dept_col}`")
    st.write(f"📁 **Category 2**: `{cat2_col}`")
    st.write(f"📂 **Segment**: `{cat3_col}`")

    # Validate minimum requirements
    if not upc_col or not desc_col:
        st.error("❌ Cannot continue. A UPC and Description column are required.")
    else:
        if st.button("🚀 Process & Merge Files"):
            # Normalize barcodes
            upc_df[upc_col] = upc_df[upc_col].astype(str).str.zfill(12)
            partner_df['barcode'] = partner_df['barcode'].astype(str).str.zfill(12)

            # Identify new UPCs
            existing_barcodes = set(partner_df['barcode'])
            upc_df['STATUS'] = upc_df[upc_col].apply(lambda x: 'Existing' if x in existing_barcodes else 'New')
            new_upcs_df = upc_df[upc_df['STATUS'] == 'New']

            st.success(f"✅ Found {len(new_upcs_df)} new UPCs.")
            st.write(new_upcs_df)

            
            # Build merged data with brand/category fields

            new_rows = pd.DataFrame({
                'barcode': new_upcs_df[upc_col],
                'bh2Brand': new_upcs_df[brand_col].str.upper() if brand_col else "N/A",
                'name': new_upcs_df[desc_col],
                'description': new_upcs_df[desc_col],
                'ch1Department': new_upcs_df[dept_col].str.upper() if dept_col else "N/A",
                'ch2Category': new_upcs_df[cat2_col].str.upper() if cat2_col else "N/A",
                'ch3Segment': new_upcs_df[cat3_col].str.upper() if cat3_col else "N/A",
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

            # Download
            output = BytesIO()
            merged_df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            st.download_button(
                label="📥 Download Merged Product File",
                data=output,
                file_name="merged_auto_mapped_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
