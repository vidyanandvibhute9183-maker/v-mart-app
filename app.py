import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime

st.set_page_config(page_title="V.MART Enterprise System", layout="wide")
st.title("📊 V.MART — Live Multi-Commodity Network Terminal")

master_csv = "v_mart_master_data.csv"

# --- NETWORK CLOUD DATABASE LOAD ---
def load_master_data():
    if os.path.exists(master_csv) and os.path.getsize(master_csv) > 0:
        df = pd.read_csv(master_csv)
        df["Date"] = pd.to_datetime(df["Date"], format="mixed")
        return df.sort_values("Date")
    else:
        # Create standard starting items if database initializes fresh
        df = pd.DataFrame([
            {"Product": "SUGAR", "Date": "2026-08-01", "Open": 50.0, "High": 52.0, "Low": 49.0, "Close": 51.5, "Volume": 100.0},
            {"Product": "RICE", "Date": "2026-08-01", "Open": 60.0, "High": 65.0, "Low": 59.0, "Close": 64.0, "Volume": 200.0}
        ])
        df["Date"] = pd.to_datetime(df["Date"])
        df.to_csv(master_csv, index=False)
        return df

def save_live_rate_change(product_name, date_val, open_p, high_p, low_p, close_p, volume_p):
    master_df = load_master_data()
    prod_clean = str(product_name).strip().upper()
    date_str = str(date_val)
    
    new_row = pd.DataFrame([{
        "Product": prod_clean,
        "Date": pd.to_datetime(date_str),
        "Open": float(open_p),
        "High": float(high_p),
        "Low": float(low_p),
        "Close": float(close_p),
        "Volume": float(volume_p)
    }])
    
    if not master_df.empty:
        # Clear matching old rows to overwrite fresh rates cleanly
        master_df = master_df[~((master_df["Product"] == prod_clean) & (master_df["Date"] == pd.to_datetime(date_str)))]
        combined_df = pd.concat([master_df, new_row], ignore_index=True)
    else:
        combined_df = new_row
        
    combined_df.to_csv(master_csv, index=False)
    return True

master_df = load_master_data()

# --- SIDEBAR INTERFACE: AVAILABLE TO ALL WEB USERS ---
st.sidebar.header("✏️ V.MART Live Rate Changer")
type_new_item = st.sidebar.checkbox("Register New Product Line?")

if type_new_item or master_df.empty:
    manual_product = st.sidebar.text_input("Type Product Name", "SUGAR")
else:
    existing_list = sorted(master_df["Product"].unique().tolist())
    manual_product = st.sidebar.selectbox("Choose Target Item", existing_list)
    
manual_date = st.sidebar.date_input("Transaction Date", datetime.now().date())
manual_open = st.sidebar.number_input("Open Price (₹)", min_value=1.0, value=50.0, step=0.5)
manual_high = st.sidebar.number_input("High Price (₹)", min_value=1.0, value=52.0, step=0.5)
manual_low = st.sidebar.number_input("Low Price (₹)", min_value=1.0, value=48.0, step=0.5)
manual_close = st.sidebar.number_input("Close Price (₹)", min_value=1.0, value=51.0, step=0.5)
manual_vol = st.sidebar.number_input("Quantity Volume Sold (units/kg)", min_value=1.0, value=50.0, step=1.0)

if st.sidebar.button("🚀 Push Rate Update Live", use_container_width=True):
    if save_live_rate_change(manual_product, manual_date, manual_open, manual_high, manual_low, manual_close, manual_vol):
        st.sidebar.success(f"✅ Rates for {manual_product.upper()} Updated Globally!")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ View Configurations")

if not master_df.empty:
    unique_products = sorted(master_df["Product"].unique().tolist())
    selected_product = st.sidebar.selectbox("🎯 Select Product View", unique_products)
    df = master_df[master_df["Product"] == selected_product].copy()
    chart_type = st.sidebar.selectbox("Select Chart Visual", ["Candlestick", "Line Chart"])
    ma_window = st.sidebar.slider("Moving Average Filters", min_value=2, max_value=10, value=2)
else:
    df = pd.DataFrame()

# --- MAIN GRAPHICAL WORKSPACE INTERFACE ---
if not df.empty:
    df[f"MA_{ma_window}"] = df["Close"].rolling(window=ma_window).mean()
    support_price = float(df["Low"].min())
    resistance_price = float(df["High"].max())
    latest_price = float(df["Close"].iloc[-1])
    total_qty = float(df["Volume"].sum())

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(f"Latest {selected_product} Price", f"₹{latest_price:.2f}")
    with col2: st.metric("Support Floor (Buy Zone)", f"₹{support_price:.2f}")
    with col3: st.metric("Resistance Ceiling (Sell)", f"₹{resistance_price:.2f}")
    with col4: st.metric("Total Volume Sold", f"{total_qty:.1f} units")

    st.markdown("---")

    fig = go.Figure()
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=selected_product))
    else:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines+markers", line=dict(color="#00CC96", width=3), name="Close Price"))

    fig.add_trace(go.Scatter(x=df["Date"], y=df[f"MA_{ma_window}"], mode="lines", line=dict(color="#FF9900", width=2, dash="dash"), name="Trend Line"))
    fig.add_hline(y=support_price, line_dash="dot", line_color="green", annotation_text="Support Floor")
    fig.add_hline(y=resistance_price, line_dash="dot", line_color="red", annotation_text="Resistance Peak")

    fig.update_layout(template="plotly_dark", height=520, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader(f"📋 Price Ledger Table: {selected_product}")
    st.dataframe(df, use_container_width=True)
else:
    st.info("System operational. Update product metrics to generate graphics.")
