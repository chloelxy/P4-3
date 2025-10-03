from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from data import dataset
from streak import movement_direction, run_summary
from indicator import calculate_sma, daily_returns
from MaxProfitCalculator import max_profit_with_days


PERIOD = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "5Y": "5y", "MAX": "max"}
DATE_FORMATS = ("%d-%b-%y", "%Y-%m-%d")

def fmt_range(rr):
    if rr is None:
        return "-"
    s, e = rr
    return f"{s.date()} → {e.date()}"


# WEB INTERFACE START
#=========================================================================
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
st.caption(f"Date range: {base_df.index.min().date()} → {base_df.index.max().date()}") # caption to show date range of data
if base_df is None or base_df.empty or "Close" not in base_df.columns: #checks if base df is empty or has no close value
    st.error("No usable price data returned.")                         #stops the web interface
    st.stop()

# Tabs for web interface
tab1, tab2, tab3= st.tabs(["Close vs SMA", "Candlestick + Streak shading", "Max profit (Buy/Sell)"])

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
    fig1.add_trace(go.Scatter(x=df1.index,y=df1["Close"],mode="lines",name="Close",customdata=hover_ret,hovertemplate="Date:%{x|%Y-%m-%d}<br>""Close:%{y:.2f}<br>""Daily Return:%{customdata}<extra></extra>"))
    fig1.add_trace(go.Scatter(x=df1.index,y=df1["SMA"],mode="lines",name=f"SMA{sma_window}",hovertemplate="Date=%{x|%Y-%m-%d}<br>"f"SMA{sma_window}=%{{y:.2f}}<extra></extra>"))
    fig1.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend_title=None) #graph layout
    st.plotly_chart(fig1, use_container_width=True)

# ---------------- Tab 2: Candlestick graph with up/down runs----------------
with tab2:
    df2 = calculate_sma(base_df.copy(), window=sma_window)
    df2 = daily_returns(df2)             # unchanged function (even if not shown in the table)
    enriched = movement_direction(df2)   # needed to get Direction & RunLength

    # Chart on top
    fig2 = go.Figure([
        go.Candlestick(x=enriched.index,open=enriched["Open"], high=enriched["High"],low=enriched["Low"], close=enriched["Close"],increasing_line_color="green", decreasing_line_color="red",name="OHLC")])
    runs = enriched[enriched["Direction"].isin(["UP","DOWN"])].copy()
    # identify run boundaries
    is_new = (runs["Direction"] != runs["Direction"].shift(1)).fillna(True)
    run_ids = is_new.cumsum()
    for _, grp in runs.groupby(run_ids):
        d = grp["Direction"].iloc[0]
        x0, x1 = grp.index.min(), grp.index.max() + pd.Timedelta(days=1)
        fig2.add_vrect(x0=x0, x1=x1,fillcolor=("green" if d == "UP" else "red"),opacity=0.08, line_width=0) # shading of runs
    fig2.update_layout(margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig2, use_container_width=True)

    # Table displaying Close, SMA, Direction, RunLength
    show_cols = ["Close", "SMA", "Direction", "RunLength"]
    missing = [c for c in show_cols if c not in enriched.columns]
    if missing:
        st.error(f"Missing columns for table: {missing}") #checks if any columns are missing and displays error message if true
    else:
        st.dataframe(enriched[show_cols].tail(20)) #shows 20 table rows

# ---------------- Tab 3: Max profit (Buy/Sell) ----------------
with tab3:
    # Reuse the same SMA window as Tab 1
    df3 = calculate_sma(base_df.copy(), window=sma_window)

    # Uses same df as tab1 and tab2
    # makes it so that tab3 is in sync
    prices = df3["Close"].tolist()
    dates = list(df3.index)

    total_profit, transactions = max_profit_with_days(prices) #call function 

    # Build arrays for plotting graph and creating table
    # b = buy date, s = sell date, bp = buy price, sp = sell price
    buy_x   = [dates[b]   for (b, s, bp, sp) in transactions]
    buy_y   = [prices[b]  for (b, s, bp, sp) in transactions]
    sell_x  = [dates[s]   for (b, s, bp, sp) in transactions]
    sell_y  = [prices[s]  for (b, s, bp, sp) in transactions]
    profit = [sp - bp    for (b, s, bp, sp) in transactions] # per trade profit or loss (sell price minus buy price)

    # Chart
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df3.index, y=df3["Close"], mode="lines", name="Close"))
    fig3.add_trace(go.Scatter(x=buy_x, y=buy_y, mode="markers", name="Buy",marker=dict(symbol="triangle-up", size=10, color="green"),hovertemplate="Buy<br>Date=%{x|%Y-%m-%d}<br>Price=%{y:.2f}<extra></extra>"))
    fig3.add_trace(go.Scatter(x=sell_x, y=sell_y, mode="markers", name="Sell",marker=dict(symbol="triangle-down", size=10, color="red"),customdata=profit,hovertemplate=("Sell<br>Date=%{x|%Y-%m-%d}<br>""Price=%{y:.2f}<br>""Trade P/L=%{customdata:.2f}<extra></extra>")))
    fig3.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend_title=None)
    st.plotly_chart(fig3, use_container_width=True)

    #Total profit value and table
    st.metric("Total P/L (sum of all trades)", f"{total_profit:.2f}")
    if transactions:
        transaction_df = pd.DataFrame({
            "Trade #":range(1, len(transactions) + 1),
            "Buy Date":[dates[b].date() for (b, s, bp, sp) in transactions],
            "Sell Date":[dates[s].date() for (b, s, bp, sp) in transactions],
            "Buy Price":[bp for (_, _, bp, _) in transactions],
            "Sell Price":[sp for (_, _, _, sp) in transactions],
            "Trade P/L":[sp - bp for (_, _, bp, sp) in transactions],
        })
        st.dataframe(transaction_df, use_container_width=True)
    else:
        st.info("No profitable trades detected in the selected period.") #message to state that no trades happen
#===============================================================================================================
# WEB INTERFACE END
