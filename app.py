import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime

st.set_page_config(page_title="V.MART Enterprise Hub", layout="wide")
st.title("📊 V.MART — Live Multi-Commodity Network Terminal")

master_csv = "v_mart_master_data.csv"

# --- CORE HIGH-SPEED MEMORY DATABASE LOADER ---
def load_master_data():
    if os.path.exists(master_csv) and os.path.getsize(master_csv) > 0:
        df = pd.read_csv(master_csv)
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        return df.dropna(subset=["Date"]).sort_values("Date")
    else:
        # Standard initial baseline rows to populate charts immediately
        df = pd.DataFrame([
            {"Product": "DIAMOND WHEAT", "Date": "2026-09-27", "Open": 40.0, "High": 42.0, "Low": 39.5, "Close": 41.0, "Volume": 100.0},
            {"Product": "SUGAR", "Date": "2026-09-27", "Open": 50.0, "High": 52.0, "Low": 49.0, "Close": 51.5, "Volume": 150.0}
        ])
        df["Date"] = pd.to_datetime(df["Date"])
        df.to_csv(master_csv, index=False)
        return df

def inject_single_row(product_name, date_val, open_p, high_p, low_p, close_p, volume_p):
    master_df = load_master_data()
    prod_clean = str(product_name).strip().upper()
    date_clean = pd.to_datetime(str(date_val))
    new_data = pd.DataFrame([{"Product": prod_clean, "Date": date_clean, "Open": float(open_p), "High": float(high_p), "Low": float(low_p), "Close": float(close_p), "Volume": float(volume_p)}])
    if not master_df.empty:
        # Overwrite matching duplicate lines to maintain pure database records
        master_df = master_df[~((master_df["Product"] == prod_clean) & (master_df["Date"] == date_clean))]
        combined_df = pd.concat([master_df, new_data], ignore_index=True)
    else:
        combined_df = new_data
    combined_df.to_csv(master_csv, index=False)
    return True

master_df = load_master_data()

# --- SIDEBAR INTERFACE: CLEAN LIVE PRICE CHANGER ONLY ---
st.sidebar.header("✏️ V.MART Live Rate Changer")
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
m_vol = st.sidebar.number_input("Quantity Sold Today (units/kg)", min_value=1.0, value=100.0, step=5.0)

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
    chart_style = st.sidebar.selectbox("Select Chart Visual", ["Candlestick", "Line Chart"])
else:
    df = pd.DataFrame()

# --- GRAPHICAL MAIN WORKSPACE ---
if not df.empty:
    support_val = float(df["Low"].min())
    resistance_val = float(df["High"].max())
    latest_val = float(df["Close"].iloc[-1])
    total_volume = float(df["Volume"].sum())

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(f"Latest {target_view} Price", f"₹{latest_val:.2f}")
    with col2: st.metric("Support Buy Zone Floor", f"₹{support_val:.2f}")
    with col3: st.metric("Resistance Sell Peak", f"₹{resistance_val:.2f}")
    with col4: st.metric("Accumulated Stock Volume", f"{total_volume:.1f} units")

    st.markdown("---")

    fig = go.Figure()
    if chart_style == "Candlestick":
        fig.add_trace(go.Candlestick(x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=target_view))
    else:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines+markers", line=dict(color="#00CC96", width=3), name="Close Rate"))

    fig.add_hline(y=support_val, line_dash="dot", line_color="green", annotation_text="Support Floor")
    fig.add_hline(y=resistance_val, line_dash="dot", line_color="red", annotation_text="Resistance Ceiling")

    fig.update_layout(template="plotly_dark", height=520, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader(f"📋 Price Record Ledger History: {target_view}")
    st.dataframe(df, use_container_width=True)
else:
    st.info("System operational. Deploy sidebar controllers to stream data maps.")
