import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image
import pytesseract
import re
import os

st.set_page_config(page_title="TLM Store Management Software", layout="wide")

# Set Tesseract path - change this if yours is different
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

st.title("TLM Store Management Software")
st.caption("Track inventory with manual entry and OCR document scanning")

# Initialize data storage
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=[
        "Item", "Item No.", "Date", "Old Stock", "New Stock", "Total",
        "Amount In", "Amount Out", "Balance"
    ])

# --- Sidebar: Item Selection ---
st.sidebar.header("Item Management")
search_term = st.sidebar.text_input("Search Item")

items = sorted(st.session_state.inventory["Item"].unique().tolist())

if search_term:
    filtered_items = [i for i in items if search_term.lower() in i.lower()]
else:
    filtered_items = items

selected_item = st.sidebar.selectbox("Select Item", options=[""] + filtered_items)

st.sidebar.markdown("---")
new_item = st.sidebar.text_input("Create New Item")
if st.sidebar.button("Add Item", use_container_width=True) and new_item:
    if new_item not in items:
        new_row = pd.DataFrame([{
            "Item": new_item,
            "Item No.": len(items) + 1,
            "Date": date.today(),
            "Old Stock": 0, "New Stock": 0, "Total": 0,
            "Amount In": 0, "Amount Out": 0, "Balance": 0
        }])
        st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
        st.success(f"Added {new_item}")
        st.rerun()
    else:
        st.warning("Item already exists")

# --- Main Page: One Item at a Time ---
if selected_item:
    df_item = st.session_state.inventory[st.session_state.inventory["Item"] == selected_item].copy()
    df_item = df_item.sort_values("Date")

    item_no = df_item["Item No."].iloc[0] if not df_item.empty else len(items) + 1

    st.subheader(f"{selected_item}")
    st.caption(f"Item No.: {item_no}")

    # --- Data Entry Tabs ---
    tab1, tab2 = st.tabs(["Manual Entry", "Scan Document"])

    with tab1:
        st.markdown("**Add transaction manually**")
        col1, col2, col3 = st.columns(3)
        with col1:
            entry_date = st.date_input("Date", value=date.today(), key="m_date")
        with col2:
            new_stock = st.number_input("New Stock Qty", min_value=0, step=1, key="m_new")
        with col3:
            amount_out = st.number_input("Amount Out Qty", min_value=0, step=1, key="m_out")

        if st.button("Add Manual Entry", use_container_width=True):
            old_stock = df_item["Total"].iloc[-1] if not df_item.empty else 0
            total = old_stock + new_stock
            balance = total - amount_out

            new_row = pd.DataFrame([{
                "Item": selected_item,
                "Item No.": item_no,
                "Date": entry_date,
                "Old Stock": old_stock,
                "New Stock": new_stock,
                "Total": total,
                "Amount In": new_stock,
                "Amount Out": amount_out,
                "Balance": balance
            }])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            st.success("Entry added!")
            st.rerun()

    with tab2:
        st.info("Upload a clear photo of your delivery note or requisition. Works best with printed text.")

        if not os.path.exists(TESSERACT_PATH):
            st.error("Tesseract not found. Install it from https://github.com/UB-Mannheim/tesseract/wiki")
        else:
            uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, width=400)

                if st.button("Extract Data with OCR", use_container_width=True):
                    with st.spinner("Reading document..."):
                        try:
                            text = pytesseract.image_to_string(image)
                            st.text_area("Extracted Text", text, height=150)

                            # Extract numbers - adjust regex for your document
                            nums = re.findall(r'\d+', text)
                            if len(nums) >= 2:
                                new_stock = int(nums[0])
                                amount_out = int(nums[1])

                                old_stock = df_item["Total"].iloc[-1] if not df_item.empty else 0
                                total = old_stock + new_stock
                                balance = total - amount_out

                                new_row = pd.DataFrame([{
                                    "Item": selected_item,
                                    "Item No.": item_no,
                                    "Date": date.today(),
                                    "Old Stock": old_stock,
                                    "New Stock": new_stock,
                                    "Total": total,
                                    "Amount In": new_stock,
                                    "Amount Out": amount_out,
                                    "Balance": balance
                                }])
                                st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
                                st.success(f"Extracted: New Stock={new_stock}, Amount Out={amount_out}")
                                st.rerun()
                            else:
                                st.warning("Couldn't find enough numbers. Check the extracted text and enter manually.")
                        except Exception as e:
                            st.error(f"OCR Error: {e}")

    # --- Transaction Table ---
    st.markdown("---")
    st.subheader("Transaction History")

    if not df_item.empty:
        display_df = df_item[["Date", "New Stock", "Amount Out", "Total", "Balance"]].copy()
        display_df.columns = ["Date", "Amount In", "Amount Out", "Total Stock", "Balance"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Download
        csv = df_item.to_csv(index=False).encode('utf-8')
        st.download_button("Download This Item CSV", csv, f"{selected_item}.csv", "text/csv")
    else:
        st.info("No transactions yet for this item.")

else:
    st.info("Select or create an item from the sidebar to start.")

# --- Technical Notes ---
with st.expander("Setup & Notes"):
    st.markdown("""
    **Setup:**
    1. Install packages: `pip install pytesseract pillow pandas openpyxl streamlit`
    2. Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
    3. Run: `streamlit run app.py`

    **OCR Tips:**
    - Use high contrast, well-lit photos
    - Printed text works best. Handwriting depends on clarity
    - If OCR pulls wrong numbers, check the "Extracted Text" box and tell me your document format. I’ll fix the regex.

    **Data Storage:**
    Currently uses session state - data resets when you close the app.
    For permanent storage, connect this to a CSV file or SQLite database.
    """)