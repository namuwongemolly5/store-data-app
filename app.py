import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- Page setup ---
st.set_page_config(page_title="TLM Store Inventory", layout="centered")
st.title("📦 TLM Store Inventory")

# --- Google Sheets Auth ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# --- Connect to Sheet ---
SHEET_NAME = "TLM Store Inventory"
worksheet = client.open(SHEET_NAME).worksheet("TLM Store Iventory")  # Note: matches your sheet tab name

# --- Form to Add Data ---
with st.form("add_item_form"):
    st.subheader("Add New Item")
    item_name = st.text_input("Item Name")
    quantity = st.number_input("Quantity", min_value=0, step=1)
    price = st.number_input("Price", min_value=0.0, step=0.01)
    submitted = st.form_submit_button("Add to Sheet")
    
    if submitted:
        if item_name:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([timestamp, item_name, quantity, price])
            st.success(f"Added {item_name} to sheet!")
        else:
            st.error("Please enter an item name")

# --- Display Data ---
st.subheader("Current Inventory")
data = worksheet.get_all_records()
if data:
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No data yet. Add your first item above.")

# --- Show last updated time ---
st.caption(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}")
