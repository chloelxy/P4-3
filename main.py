from datetime import datetime
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# -----------------------------
# Your existing stuff (unchanged)
# -----------------------------
PERIOD = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "5Y": "5y", "MAX": "max"}
DATE_FORMATS = ("%d-%b-%y", "%Y-%m-%d")

def fmt_range(rr):
    if rr is None:
        return "-"
    s, e = rr
    return f"{s.date()} → {e.date()}"

def dataset(stock, period):
    stock = yf.Ticker(stock)
    hist = stock.history(period=period)
    df = pd.DataFrame(hist)
    print("Your dataframe is:\n")
    print(df)
    if df.empty is None or df.empty or "Close" not in df.columns:
        print("Stock period not valid")
    return df

# ---------CORE FUNCTIONS START ---------
def calculate_sma(df, window):
    sma_values = []
    closes = df['Close'].tolist()
    #window_sum = 0
    for i in range(len(closes)):
        if i < window - 1:
            sma_values.append(None) #Not enough data
        else:
            window_sum = sum(closes[i - window + 1: i+1])
            sma = window_sum /window
            sma_values.append(sma)
    df['SMA'] = sma_values
    return df

def daily_returns(df):
    returns = []
    closes = df['Close'].tolist()
    for i in range(1, len(closes)):
        prev = closes[i-1]
        curr = closes[i]
        daily_return = (((curr - prev) / prev) * 100)
        daily_return = round(daily_return, 2)
        returns.append(f"{daily_return}%")
    returns = [None] + returns
    df['Daily Returns'] = returns
    return df

def movement_direction(df: pd.DataFrame) -> pd.DataFrame:
    stocks = df.copy()
    closing_price_change = stocks["Close"].diff()
    direction = closing_price_change.where(closing_price_change.notna(), 0.0).apply(
        lambda x: "UP" if x > 0 else ("DOWN" if x < 0 else "FLAT"))
    stocks["Direction"] = direction
    streak_type = stocks["Direction"].isin(["UP", "DOWN"])
    run_change = (stocks["Direction"] != stocks["Direction"].shift(1)) & streak_type
    stocks["RunID"] = 0
    stocks.loc[streak_type, "RunID"] = run_change[streak_type].cumsum()
    stocks["RunLength"] = 0
    for runid, grp in stocks[streak_type].groupby("RunID"):
        stocks.loc[grp.index, "RunLength"] = range(1, len(grp) + 1)
    return stocks

def run_summary(df: pd.DataFrame) -> dict:
    runs = df[df["Direction"].isin(["UP", "DOWN"])].copy()
    if runs.empty:
        return{
            "no_up_runs": 0, "no_down_runs": 0, "longest_up_length": 0, "longest_up_range": None,
            "longest_down_length": 0, "longest_down_range": None
        }
    run_groups = runs.groupby(["RunID", "Direction"])
    run_lengths = run_groups.size().rename("Length").reset_index()
    no_up_runs = (run_lengths["Direction"] == "UP").sum()
    no_down_runs = (run_lengths["Direction"] == "DOWN").sum()

    up_runs = run_lengths[run_lengths["Direction"] == "UP"]
    if not up_runs.empty:
        up_max_length = up_runs["Length"].max()
        up_rid = up_runs.loc[up_runs["Length"].idxmax(), "RunID"]
        up_idx = runs[runs["RunID"] == up_rid].index
        up_range = (up_idx.min(), up_idx.max())
    else:
        up_max_length, up_range = 0, None

    down_runs = run_lengths[run_lengths["Direction"] == "DOWN"]
    if not down_runs.empty:
        down_max_length = down_runs["Length"].max()
        down_rid = down_runs.loc[down_runs["Length"].idxmax(), "RunID"]
        down_idx = runs[runs["RunID"] == down_rid].index
        down_range = (down_idx.min(), down_idx.max())
    else:
        down_max_length, down_range = 0, None

    return{
        "no_up_runs": int(no_up_runs), "no_down_runs": int(no_down_runs), 
        "longest_up_length": int(up_max_length), "longest_up_range": up_range,
        "longest_down_length": int(down_max_length), "longest_down_range": down_range
    }
# --------- CORE FUNCTIONS END ---------

# -----------------------------
# WEB INTERFACE
# -----------------------------
st.set_page_config(page_title="Stock Market Analysis", layout="wide")
st.title("Stock Market Visualisation Dashboard")

# Inputs on web interface
col1, col2 = st.columns([2, 1])
with col1:
    ticker = st.text_input("Ticker", value="AAPL").strip().upper()
with col2:
    period_key = st.selectbox("Period", list(PERIOD.keys()), index=3)  # default 1Y
period = PERIOD[period_key]

if not ticker: #check validity of ticker
    st.warning("Enter a ticker to begin.")
    st.stop()

def _get_df(_ticker: str, _period: str) -> pd.DataFrame: #gets base df from dataset function for graph visualisations
    return dataset(_ticker, _period)

base_df = _get_df(ticker, period)
if base_df is None or base_df.empty or "Close" not in base_df.columns: #checks if base df is empty or has no close value
    st.error("No usable price data returned.")                         #stops the web interface
    st.stop()

# Tabs
tab1, tab2, tab3= st.tabs(["Close vs SMA", "Candlestick + Streak shading", "Max profit (Buy/Sell)"]) #tabs on web interface

# ---------------- Tab 1: Close vs SMA (graph + slider only) ----------------
with tab1:
    sma_window = st.slider("SMA period", min_value=5, max_value=60, value=30, step=1) #can change min,max value of SMA slider
    df1 = calculate_sma(base_df.copy(), window=sma_window) # creating temp dataframe to store sma values
    if "Daily Returns" not in df1.columns: #ensure daily returns exist in dataframe
        df1 = daily_returns(df1)

    # "—" for first day (None), then to numpy for Plotly customdata
    #.fillna("-") replaces first value to - as there is not previous data to compare
    #.to_numpy converts the series to plain numpy array as it is more efficient and guarantees the length matches 
    hover_ret = df1["Daily Returns"].fillna("—").to_numpy()                                           

    fig1 = go.Figure()
    #fig1.add_trace(go.Scatter(x=df1.index, y=df1["Close"], mode="lines", name="Close")) #close line graph
    fig1.add_trace(go.Scatter(
        x=df1.index,
        y=df1["Close"],
        mode="lines",
        name="Close",
        customdata=hover_ret,
        hovertemplate="Date:%{x|%Y-%m-%d}<br>"
                      "Close:%{y:.2f}<br>"
                      "Daily Return:%{customdata}<extra></extra>"
    ))
    #fig1.add_trace(go.Scatter(x=df1.index, y=df1["SMA"],   mode="lines", name=f"SMA{str(sma_window)}")) #sma line graph
    fig1.add_trace(go.Scatter(
        x=df1.index,
        y=df1["SMA"],
        mode="lines",
        name=f"SMA{sma_window}",
        hovertemplate="Date=%{x|%Y-%m-%d}<br>"
                      f"SMA{sma_window}=%{{y:.2f}}<extra></extra>"
    ))
    fig1.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend_title=None) #graph layout
    st.plotly_chart(fig1, use_container_width=True)

# ---------------- Tab 2: Candlestick + Streak shading ----------------
with tab2:
    df2 = calculate_sma(base_df.copy(), window=sma_window)
    df2 = daily_returns(df2)             # unchanged function (even if not shown in the table)
    enriched = movement_direction(df2)   # needed to get Direction & RunLength

    # Chart on top
    fig2 = go.Figure([
        go.Candlestick(
            x=enriched.index,
            open=enriched["Open"], high=enriched["High"],
            low=enriched["Low"], close=enriched["Close"],
            increasing_line_color="green", decreasing_line_color="red",
            name="OHLC"
        )
    ])
    runs = enriched[enriched["Direction"].isin(["UP","DOWN"])].copy()
    # identify run boundaries
    is_new = (runs["Direction"] != runs["Direction"].shift(1)).fillna(True)
    run_ids = is_new.cumsum()
    for _, grp in runs.groupby(run_ids):
        d = grp["Direction"].iloc[0]
        x0, x1 = grp.index.min(), grp.index.max() + pd.Timedelta(days=1)
        fig2.add_vrect(
            x0=x0, x1=x1,
            fillcolor=("green" if d == "UP" else "red"),
            opacity=0.08, line_width=0
    )
    fig2.update_layout(margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig2, use_container_width=True)

    # Table below: only Close, SMA, Direction, RunLength
    show_cols = ["Close", "SMA", "Direction", "RunLength"]
    missing = [c for c in show_cols if c not in enriched.columns]
    if missing:
        st.error(f"Missing columns for table: {missing}") #checks if 
    else:
        st.dataframe(enriched[show_cols].tail(20)) #shows 20 table rows
