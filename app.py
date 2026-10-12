
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase_auth import check_password, get_user_supabase

st.set_page_config(page_title="V.MART", layout="wide")

if not check_password():
    st.stop()

st.title("📊 V.MART — The Rate Trader")

# Get a Supabase client authenticated as this user.
try:
    supabase = get_user_supabase()
    if supabase is None:
        st.warning("Your login session has expired. Please log in again.")
        st.stop()
except Exception:
    st.error("Could not connect securely to your database.")
    st.stop()


def load_master_data():
    """Load only the signed-in user's rates."""
    try:
        response = (
            supabase.table("v_mart_rates")
            .select(
                "id, product, rate_date, open_price, "
                "high_price, low_price, close_price, owner_id"
            )
            .order("rate_date")
            .execute()
        )

        records = response.data or []

        # Give a new user their own starter records.
        if not records:
            user_id = st.session_state["user_id"]
            starter_rows = [
                {
                    "owner_id": user_id,
                    "product": "DIAMOND WHEAT",
                    "rate_date": "2026-09-27",
                    "open_price": 40.0,
                    "high_price": 42.0,
                    "low_price": 39.5,
                    "close_price": 41.0,
                },
                {
                    "owner_id": user_id,
                    "product": "SUGAR",
                    "rate_date": "2026-09-27",
                    "open_price": 50.0,
                    "high_price": 52.0,
                    "low_price": 49.0,
                    "close_price": 51.5,
                },
            ]

            supabase.table("v_mart_rates").upsert(
                starter_rows,
                on_conflict="owner_id,product,rate_date",
            ).execute()

            response = (
                supabase.table("v_mart_rates")
                .select(
                    "id, product, rate_date, open_price, "
                    "high_price, low_price, close_price, owner_id"
                )
                .order("rate_date")
                .execute()
            )
            records = response.data or []

        columns = [
            "Product", "Date", "Open", "High", "Low", "Close"
        ]

        if not records:
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(records).rename(
            columns={
                "product": "Product",
                "rate_date": "Date",
                "open_price": "Open",
                "high_price": "High",
                "low_price": "Low",
                "close_price": "Close",
            }
        )

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"]).sort_values("Date")

        return df

    except Exception as e:
        st.error(
            "Could not load your rates from Supabase. "
            "Check your table columns, login session, and RLS policies."
        )
        st.caption(str(e))
        st.stop()


def inject_single_row(product_name, date_val, open_p, high_p, low_p, close_p):
    """Insert or update a rate belonging to the signed-in user."""
    prod_clean = str(product_name).strip().upper()

    if not prod_clean:
        st.sidebar.error("Please enter a product name.")
        return False

    if low_p > high_p:
        st.sidebar.error("Low price cannot be greater than high price.")
        return False

    if not low_p <= open_p <= high_p:
        st.sidebar.error("Open price must be between low and high.")
        return False

    if not low_p <= close_p <= high_p:
        st.sidebar.error("Close price must be between low and high.")
        return False

    try:
        record = {
            "owner_id": st.session_state["user_id"],
            "product": prod_clean,
            "rate_date": pd.to_datetime(date_val).strftime("%Y-%m-%d"),
            "open_price": float(open_p),
            "high_price": float(high_p),
            "low_price": float(low_p),
            "close_price": float(close_p),
        }

        supabase.table("v_mart_rates").upsert(
            record,
            on_conflict="owner_id,product,rate_date",
        ).execute()

        return True

    except Exception as e:
        st.sidebar.error("Could not save your rate.")
        st.sidebar.caption(str(e))
        return False


master_df = load_master_data()

# --- SIDEBAR: RATE CHANGER ---
st.sidebar.header("✏️ V.MART Live Rate Changer")
type_new = st.sidebar.checkbox("Register New Product")

if type_new or master_df.empty:
    manual_prod = st.sidebar.text_input(
        "Product Name", "Type Product Name Here"
    )
else:
    available_items = sorted(master_df["Product"].unique().tolist())
    manual_prod = st.sidebar.selectbox("Choose Item", available_items)

manual_date = st.sidebar.date_input(
    "Transaction Date", datetime.now().date()
)
m_open = st.sidebar.number_input(
    "Open Price (₹)", min_value=1.0, value=40.0, step=0.5
)
m_high = st.sidebar.number_input(
    "High Price (₹)", min_value=1.0, value=42.0, step=0.5
)
m_low = st.sidebar.number_input(
    "Low Price (₹)", min_value=1.0, value=39.0, step=0.5
)
m_close = st.sidebar.number_input(
    "Close Price (₹)", min_value=1.0, value=40.0, step=0.5
)

if st.sidebar.button("🚀 Update the Rates", use_container_width=True):
    if inject_single_row(
        manual_prod, manual_date, m_open, m_high, m_low, m_close
    ):
        st.sidebar.success(
            f"✅ Live update complete for {manual_prod.strip().upper()}!"
        )
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ View Configurations")

if not master_df.empty:
    product_catalog = sorted(master_df["Product"].unique().tolist())
    target_view = st.sidebar.selectbox(
        "🎯 Select Product View", product_catalog
    )
    df = (
        master_df[master_df["Product"] == target_view]
        .copy()
        .sort_values("Date")
    )
    chart_style = st.sidebar.selectbox(
        "Select Chart Visual", ["Candlestick", "Line Chart"]
    )
else:
    df = pd.DataFrame()

# --- MAIN DASHBOARD ---
if not df.empty:
    support_val = float(df["Low"].min())
    resistance_val = float(df["High"].max())
    latest_val = float(df["Close"].iloc[-1])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(f"Latest {target_view} Price", f"₹{latest_val:.2f}")
    with col2:
        st.metric("Support Buy Zone Floor", f"₹{support_val:.2f}")
    with col3:
        st.metric("Resistance Sell Peak", f"₹{resistance_val:.2f}")

    st.markdown("---")

    fig = go.Figure()

    if chart_style == "Candlestick":
        fig.add_trace(
            go.Candlestick(
                x=df["Date"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name=target_view,
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                mode="lines+markers",
                line=dict(color="#00CC96", width=3),
                name="Close Rate",
            )
        )

    fig.add_hline(
        y=support_val,
        line_dash="dot",
        line_color="green",
        annotation_text="Support Floor",
    )
    fig.add_hline(
        y=resistance_val,
        line_dash="dot",
        line_color="red",
        annotation_text="Resistance Ceiling",
    )

    fig.update_layout(
        template="plotly_dark",
        height=520,
        xaxis_rangeslider_visible=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"📋 Price Record Ledger History: {target_view}")
    st.dataframe(
        df[["Product", "Date", "Open", "High", "Low", "Close"]],
        use_container_width=True,
    )
else:
    st.info("No rate records are available for your account yet.")
