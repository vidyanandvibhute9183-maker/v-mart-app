import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="V.MART Enterprise System", layout="wide")
st.title("📊 V.MART — Multi-Commodity B2B Analytics")

master_csv = "v_mart_master_data.csv"

# --- LIGHTWEIGHT CLOUD DATA LOADER ---
def load_master_data():
    if os.path.exists(master_csv) and os.path.getsize(master_csv) > 0:
        df = pd.read_csv(master_csv)
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"], format="mixed")
            df = df.sort_values("Date")
        return df
    else:
        # Create an initial clean sugar placeholder database if file is completely fresh
        df = pd.DataFrame([
            {"Product": "SUGAR", "Date": "2026-08-01", "Open": 50.0, "High": 52.0, "Low": 49.0, "Close": 51.5, "Volume": 150.0},
            {"Product": "SUGAR", "Date": "2026-08-02", "Open": 51.5, "High": 55.0, "Low": 51.0, "Close": 54.0, "Volume": 200.0}
        ])
        df["Date"] = pd.to_datetime(df["Date"])
        return df

master_df = load_master_data()

st.sidebar.header("⚙️ View Configurations")

if not master_df.empty:
    unique_products = sorted(master_df["Product"].unique().tolist())
    selected_product = st.sidebar.selectbox("🎯 Select Product View", unique_products)
    
    # Isolate data for the user-selected product dynamically
    df = master_df[master_df["Product"] == selected_product].copy()
    
    chart_type = st.sidebar.selectbox("Select Chart Visual", ["Line Chart", "Candlestick"])
    ma_window = st.sidebar.slider("Moving Average Filters", min_value=2, max_value=10, value=2)
else:
    df = pd.DataFrame()

# --- MAIN SYSTEM INTERFACE ---
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
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines+markers", line=dict(color="#00CC96", width=3), name="Close Price"))

    fig.add_trace(go.Scatter(x=df["Date"], y=df[f"MA_{ma_window}"], mode="lines", line=dict(color="#FF9900", width=2, dash="dash"), name="Trend Line"))
    fig.add_hline(y=support_price, line_dash="dot", line_color="green", annotation_text="Support Floor")
    fig.add_hline(y=resistance_price, line_dash="dot", line_color="red", annotation_text="Resistance Peak")

    fig.update_layout(template="plotly_dark", height=520, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader(f"📋 Price Ledger Table: {selected_product}")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No data available to plot charts.")
