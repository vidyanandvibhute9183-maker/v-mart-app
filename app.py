import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import pdfplumber
from datetime import datetime

st.set_page_config(page_title="V.MART", layout="wide")
st.title("📊 V.MART — Analytics")

master_csv = "v_mart_master_data.csv"

# --- HIGH-SPEED BACKEND ENGINE ---
def load_master_data():
    if os.path.exists(master_csv):
        # Uses pyarrow engine for ultra-fast disk loading speeds
        df = pd.read_csv(master_csv, engine="pyarrow")
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"], format="mixed")
            df = df.sort_values("Date")
        return df
    else:
        df = pd.DataFrame(columns=["Product", "Date", "Open", "High", "Low", "Close", "Volume"])
        df.to_csv(master_csv, index=False)
        return df

@st.cache_data(show_spinner=False)
def speed_parse_pdf(file_bytes):
    """High-speed structural table matrix ingestion algorithm"""
    valid_records = []
    headers = ["Sr No.", "Bill No.", "Bill Date", "Pay Mode", "Customer Name", "Reference By", "Counter Name", "Barcode", "Product Name", "MRP", "Rate", "Qnty", "Amount"]
    
    with pdfplumber.open(file_bytes) as pdf:
        for page in pdf.pages:
            # Drop horizontal line constraints to force fast row grouping speed
            table = page.extract_table(table_settings={"vertical_strategy": "text", "horizontal_strategy": "text"})
            if not table:
                continue
                
            for row in table:
                if len(row) == len(headers):
                    # Direct cell alignment checking without empty layer conversions
                    if row[2] and row[8] and row[10]: 
                        valid_records.append({
                            "Bill Date": row[2].strip(),
                            "Product Name": row[8].strip().upper(),
                            "Rate": row[10].strip(),
                            "Qnty": row[11].strip() if row[11] else "0"
                        })
                        
    if valid_records:
        df = pd.DataFrame(valid_records)
        df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce")
        df["Qnty"] = pd.to_numeric(df["Qnty"], errors="coerce").fillna(0)
        df = df[(df["Rate"] > 0) & (df["Qnty"] > 0)].dropna()
        df["Bill Date"] = pd.to_datetime(df["Bill Date"], format="mixed")
        return df
    return pd.DataFrame()

# Initialize data cache
master_df = load_master_data()

# --- SIDEBAR CONTROL ROOM ---
st.sidebar.header("🕹️ V.MART Control Room")
entry_mode = st.sidebar.radio("Choose Input Method", ["⚡ Upload File Report", "✏️ Add Manual Rates"])

if entry_mode == "⚡ Upload File Report":
    st.sidebar.subheader("📥 Sync Bulk POS Ledger")
    uploaded_file = st.sidebar.file_uploader("Upload Store Sale Report (.pdf)", type=["pdf"])
    
    if uploaded_file is not None:
        if st.sidebar.button("🚀 Process & Extract All Products", use_container_width=True):
            with st.spinner("⚡ Running high-speed text extraction..."):
                raw_df = speed_parse_pdf(uploaded_file)
            
            if not raw_df.empty:
                new_records = []
                # Advanced aggregate vectors grouped instantly via internal indexing slots
                for (product, day), group in raw_df.groupby(["Product Name", raw_df["Bill Date"].dt.date]):
                    new_records.append({
                        "Product": str(product),
                        "Date": str(day),
                        "Open": float(group["Rate"].iloc[0]),
                        "High": float(group["Rate"].max()),
                        "Low": float(group["Rate"].min()),
                        "Close": float(group["Rate"].iloc[-1]),
                        "Volume": float(group["Qnty"].sum())
                    })
                
                new_summary_df = pd.DataFrame(new_records)
                combined_df = pd.concat([master_df, new_summary_df]).drop_duplicates(subset=["Product", "Date"], keep="last")
                combined_df.to_csv(master_csv, index=False)
                st.sidebar.success("✅ Master Ledger Sync Complete!")
                st.rerun()
            else:
                st.sidebar.error("⚠️ No matching table structures found in PDF pages.")
else:
    st.sidebar.subheader("✏️ Add Manual Item Rates")
    type_new_item = st.sidebar.checkbox("Register New Product Line?")
    
    if type_new_item or master_df.empty:
        manual_product = st.sidebar.text_input("Enter Product Name", "SUGAR")
    else:
        existing_list = sorted(master_df["Product"].unique().tolist())
        manual_product = st.sidebar.selectbox("Choose Target Item", existing_list)
        
    manual_date = st.sidebar.date_input("Transaction Date", datetime.now().date())
    manual_open = st.sidebar.number_input("Open Price (₹)", min_value=1.0, value=50.0, step=0.5)
    manual_high = st.sidebar.number_input("High Price (₹)", min_value=1.0, value=52.0, step=0.5)
    manual_low = st.sidebar.number_input("Low Price (₹)", min_value=1.0, value=48.0, step=0.5)
    manual_close = st.sidebar.number_input("Close Price (₹)", min_value=1.0, value=51.0, step=0.5)
    manual_vol = st.sidebar.number_input("Quantity Sold Today (units/kg)", min_value=1.0, value=50.0, step=1.0)
    
    if st.sidebar.button("🚀 Save Manual Data Line", use_container_width=True):
        # Direct append array logic bypassing loading lags
        new_line = pd.DataFrame([{"Product": manual_product.strip().upper(), "Date": pd.to_datetime(str(manual_date)), "Open": manual_open, "High": manual_high, "Low": manual_low, "Close": manual_close, "Volume": manual_vol}])
        combined_df = pd.concat([master_df, new_line]).drop_duplicates(subset=["Product", "Date"], keep="last")
        combined_df.to_csv(master_csv, index=False)
        st.sidebar.success(f"✅ Saved row successfully!")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ View Configurations")

if not master_df.empty:
    unique_products = sorted(master_df["Product"].unique().tolist())
    selected_product = st.sidebar.selectbox("🎯 Select Product View", unique_products)
    df = master_df[master_df["Product"] == selected_product].copy()
    chart_type = st.sidebar.selectbox("Select Chart Visual", ["Line Chart", "Candlestick"])
    ma_window = st.sidebar.slider("Moving Average Filters", min_value=2, max_value=10, value=3)
    
    if st.sidebar.button("🗑️ Reset All App Data", type="primary", use_container_width=True):
        if os.path.exists(master_csv):
            os.remove(master_csv)
        st.rerun()
else:
    df = pd.DataFrame()
    st.sidebar.info("System database empty.")

# --- MAIN GRAPHICAL INTERFACE WORKSPACE ---
if not df.empty:
    df[f"MA_{ma_window}"] = df["Close"].rolling(window=ma_window).mean()
    support_price = float(df["Low"].min())
    resistance_price = float(df["High"].max())
    latest_price = float(df["Close"].iloc[-1])
    total_qty = float(df["Volume"].sum())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(f"Latest {selected_product} Price", f"₹{latest_price:.2f}")
    with col2:
        st.metric("Support Floor (Buy Zone)", f"₹{support_price:.2f}")
    with col3:
        st.metric("Resistance Ceiling (Sell)", f"₹{resistance_price:.2f}")
    with col4:
        st.metric("Total Volume Sold", f"{total_qty:.1f} units")

    st.markdown("---")

    fig = go.Figure()
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=selected_product
        ))
    else:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines+markers", line=dict(color="#00CC96", width=3), name="Close Rate"))

    fig.add_trace(go.Scatter(x=df["Date"], y=df[f"MA_{ma_window}"], mode="lines", line=dict(color="#FF9900", width=2, dash="dash"), name="Trend Line"))
    fig.add_hline(y=support_price, line_dash="dot", line_color="green", annotation_text="Support Floor")
    fig.add_hline(y=resistance_price, line_dash="dot", line_color="red", annotation_text="Resistance Peak")

    fig.update_layout(template="plotly_dark", height=520, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader(f"📋 Price Ledger Table: {selected_product}")
    st.dataframe(df, use_container_width=True)
else:
    st.info("V.MART Multi-Product Terminal Ready. Provide transaction metrics or drop a bill file report to launch charts!")
