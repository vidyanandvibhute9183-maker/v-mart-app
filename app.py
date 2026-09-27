import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import pdfplumber
from datetime import datetime

st.set_page_config(page_title="V.MART Enterprise Hub", layout="wide")
st.title("📊 V.MART — Live Multi-Commodity Network Terminal")

master_csv = "v_mart_master_data.csv"

# --- CORE STABLE DATABASE LOADER ---
def load_master_data():
    if os.path.exists(master_csv) and os.path.getsize(master_csv) > 0:
        df = pd.read_csv(master_csv)
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        return df.dropna(subset=["Date"]).sort_values("Date")
    else:
        df = pd.DataFrame([
            {"Product": "DIAMOND WHEAT", "Date": "2026-09-27", "Open": 40.0, "High": 40.0, "Low": 40.0, "Close": 40.0, "Volume": 30.0}
        ])
        df["Date"] = pd.to_datetime(df["Date"])
        df.to_csv(master_csv, index=False)
        return df

# FAULT-TOLERANT MATRIX SCROLLER
def robust_grid_pdf_parse(file_bytes_stream):
    valid_records = []
    with pdfplumber.open(file_bytes_stream) as pdf:
        for page in pdf.pages:
            # Reads all structural tables without enforcing strict margin line checks
            matrix = page.extract_table(table_settings={
                "vertical_strategy": "text", 
                "horizontal_strategy": "text",
                "snap_tolerance": 3
            })
            if not matrix:
                continue
                
            for row in matrix:
                # Dynamically filter out empty cells and clean text fragments
                clean_row = [str(cell).strip() for cell in row if cell is not None]
                
                # Check for standard transaction rows by locating item matches or price scales
                if len(clean_row) >= 6:
                    # Look for date structures and isolate rate indices dynamically
                    for cell in clean_row:
                        if ("/" in cell or "-" in cell) and len(cell) >= 8:
                            try:
                                # Safe vector matching rules targeting values out of your POS template layout
                                rate_idx = -3 if len(clean_row) >= 11 else -2
                                qty_idx = -2 if len(clean_row) >= 11 else -1
                                
                                rate_val = float(clean_row[rate_idx].replace(",", ""))
                                qty_val = float(clean_row[qty_idx].replace(",", ""))
                                
                                # Match item tags matching Diamond Wheat lines
                                prod_name = "DIAMOND WHEAT"
                                for text in clean_row:
                                    if "WHEAT" in text.upper() or "DIAMOND" in text.upper():
                                        prod_name = "DIAMOND WHEAT"
                                        break
                                
                                if rate_val > 0:
                                    valid_records.append({
                                        "Product": prod_name,
                                        "Date": cell,
                                        "Rate": rate_val,
                                        "Qnty": qty_val if qty_val > 0 else 1.0
                                    })
                                    break
                            except Exception:
                                continue
                                
    if valid_records:
        raw_df = pd.DataFrame(valid_records)
        raw_df["Date"] = pd.to_datetime(raw_df["Date"], errors='coerce', format="mixed")
        raw_df = raw_df.dropna(subset=["Date"])
        
        compiled_list = []
        for (prod_name, day), group in raw_df.groupby(["Product", raw_df["Date"].dt.date]):
            group = group.sort_index()
            compiled_list.append({
                "Product": str(prod_name),
                "Date": pd.to_datetime(str(day)),
                "Open": float(group["Rate"].iloc[0]),
                "High": float(group["Rate"].max()),
                "Low": float(group["Rate"].min()),
                "Close": float(group["Rate"].iloc[-1]),
                "Volume": float(group["Qnty"].sum())
            })
        return pd.DataFrame(compiled_list)
    return pd.DataFrame()

def inject_single_row(product_name, date_val, open_p, high_p, low_p, close_p, volume_p):
    master_df = load_master_data()
    prod_clean = str(product_name).strip().upper()
    date_clean = pd.to_datetime(str(date_val))
    new_data = pd.DataFrame([{"Product": prod_clean, "Date": date_clean, "Open": float(open_p), "High": float(high_p), "Low": float(low_p), "Close": float(close_p), "Volume": float(volume_p)}])
    if not master_df.empty:
        master_df = master_df[~((master_df["Product"] == prod_clean) & (master_df["Date"] == date_clean))]
        combined_df = pd.concat([master_df, new_data], ignore_index=True)
    else:
        combined_df = new_data
    combined_df.to_csv(master_csv, index=False)
    return True

master_df = load_master_data()

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("🕹️ V.MART Control Room")
input_channel = st.sidebar.radio("Select Input Operation", ["📥 Upload Store Invoice PDF", "✏️ Add/Change Rates Manually"])

if input_channel == "📥 Upload Store Invoice PDF":
    st.sidebar.subheader("Bulk Document Parser")
    uploaded_file = st.sidebar.file_uploader("Drop Store Sale Report (.pdf)", type=["pdf"])
    if uploaded_file is not None:
        if st.sidebar.button("🚀 Run Cloud Extraction Engine", use_container_width=True):
            with st.spinner("⚡ Running structural matrix scan..."):
                extracted_df = robust_grid_pdf_parse(uploaded_file)
                
            if not extracted_df.empty:
                combined_master = pd.concat([master_df, extracted_df]).drop_duplicates(subset=["Product", "Date"], keep="last")
                combined_master.to_csv(master_csv, index=False)
                st.sidebar.success("✅ Invoice Data Ingested Flawlessly!")
                st.rerun()
            else:
                st.sidebar.error("⚠️ Pattern layout mismatch. Review raw column contents below.")
                
                # DIAGNOSTICS VIEWER: Prints the first few lines of your file to see how text is split
                with pdfplumber.open(uploaded_file) as pdf:
                    first_page_text = pdf.pages[0].extract_text()
                    st.text_area("📄 Raw Text Structure inside your PDF file:", first_page_text, height=250)
else:
    st.sidebar.subheader("Live Price Changer Form")
    type_new = st.sidebar.checkbox("Register Brand New Product?")
    if type_new or master_df.empty:
        manual_prod = st.sidebar.text_input("Type Product Name", "DIAMOND WHEAT")
    else:
        available_items = sorted(master_df["Product"].unique().tolist())
        manual_prod = st.sidebar.selectbox("Choose Target Item", available_items)
        
    manual_date = st.sidebar.date_input("Transaction Date", datetime.now().date())
    m_open = st.sidebar.number_input("Open Price (₹)", min_value=1.0, value=40.0, step=0.5)
    m_high = st.sidebar.number_input("High Price (₹)", min_value=1.0, value=42.0, step=0.5)
    m_low = st.sidebar.number_input("Low Price (₹)", min_value=1.0, value=39.0, step=0.5)
    m_close = st.sidebar.number_input("Close Price (₹)", min_value=1.0, value=40.0, step=0.5)
    m_vol = st.sidebar.number_input("Quantity Sold Today (units/kg)", min_value=1.0, value=30.0, step=5.0)
    
    if st.sidebar.button("🚀 Push Rate Update Live", use_container_width=True):
        if inject_single_row(manual_prod, manual_date, m_open, m_high, m_low, m_close, m_vol):
            st.sidebar.success(f"✅ Live Update Complete for {manual_prod.upper()}!")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ View Configurations")

if not master_df.empty:
    product_catalog = sorted(master_df["Product"].unique().tolist())
    target_view = st.sidebar.selectbox("🎯 Select Product View", product_catalog)
    df = master_df[master_df["Product"] == target_view].copy().sort_values("Date")
    chart_style = st.sidebar.selectbox("Select Chart Visual", ["Line Chart", "Candlestick"])
    ma_intervals = st.sidebar.slider("Moving Average Filters", min_value=2, max_value=10, value=2)
else:
    df = pd.DataFrame()

# --- GRAPHICAL MAIN WORKSPACE ---
if not df.empty:
    df[f"MA_{ma_intervals}"] = df["Close"].rolling(window=ma_intervals).mean()
    support_val = float(df["Low"].min())
    resistance_val = float(df["High"].max())
    latest_val = float(df["Close"].iloc[-1])
    total_volume = float(df["Volume"].sum())

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(f"Latest {target_view} Rate", f"₹{latest_val:.2f}")
    with col2: st.metric("Support Buy Zone Floor", f"₹{support_val:.2f}")
    with col3: st.metric("Resistance Sell Peak", f"₹{resistance_val:.2f}")
    with col4: st.metric("Accumulated Stock Volume", f"{total_volume:.1f} units")

    st.markdown("---")

    fig = go.Figure()
    if chart_style == "Candlestick":
        fig.add_trace(go.Candlestick(x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=target_view))
    else:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines+markers", line=dict(color="#00CC96", width=3), name="Close Rate"))

    fig.add_trace(go.Scatter(x=df["Date"], y=df[f"MA_{ma_intervals}"], mode="lines", line=dict(color="#FF9900", width=2, dash="dash"), name="Trend Line"))
    fig.add_hline(y=support_val, line_dash="dot", line_color="green", annotation_text="Support Floor")
    fig.add_hline(y=resistance_val, line_dash="dot", line_color="red", annotation_text="Resistance Ceiling")

    fig.update_layout(template="plotly_dark", height=520, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
