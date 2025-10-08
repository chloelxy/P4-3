import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import streamlit as st
import plotly.express as px
import os
import time
from src.data import dataset
from src.streaks import movement_direction, run_summary
from src.indicator import calculate_sma, daily_returns
from src.max_profit import max_profit_with_days

#maps user-friendly period labels to yfinance format
#Specifies periods in dropdown input
PERIOD = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "3Y":"3y"}
DATE_FORMATS = ("%d-%b-%y", "%Y-%m-%d") #defines date formats for display

# WEB INTERFACE START
#=========================================================================
st.set_page_config(page_title="Stock Market Analysis", layout="wide") #Set page title and layout
st.title("Stock Market Visualisation Dashboard") #Displays main dashboard title

TICKER_OPTIONS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "JPM", "V"]
# Apple, Microsoft, Google, Amazon, Tesla, Nvidia, Meta, Netflix, JPMorgan, Visa
# Top 10 popular stocks

endserver = 0
# Inputs for period on web interface (dropdown)
col1, col2, col3 = st.columns([0.5,1.5,0.5]) # defines the columns and splits them to size
with col1:
    period_key = st.selectbox("Period", list(PERIOD.keys()), index=3)  # default 1Y when starting web interface
with col3:
    if st.button("Shutdown Server"):
        st.warning("Shutting down Streamlit server...")
        endserver = 1

if endserver == 1:
    st.empty()
    st.markdown("<h1 style='text-align: center;'>Server has been shutdown</h1>", unsafe_allow_html=True)
    time.sleep(2)  # Pause for 2 seconds so user sees the message
    os._exit(0)  # Forcefully exit the app

# Inputs for ticker on web interface (side menu) 
st.sidebar.header("Options")
ticker = st.sidebar.selectbox("Select Ticker", TICKER_OPTIONS, index=0)
st.sidebar.subheader("Stocks Today")

live_data = {} # initializing dictionary
for symbol in TICKER_OPTIONS: #iterates over the top 10 popular stocks
    try:
        stock = yf.Ticker(symbol) # using yfinance fetches stock prices for top 10 popular stocks
        hist = stock.history(period="2d") #fetches last 2 days of data for each ticker
        if len(hist) >= 2: #ensure there are at least 2 data points to calculate change
            today_close = hist["Close"].iloc[-1] #get most recent closing price
            yesterday_close = hist["Close"].iloc[-2] #get previous closing price
            change = today_close - yesterday_close #calculate change
            pct_change = (change / yesterday_close) * 100 #calculate percentage change
            live_data[symbol] = f"{today_close:.2f} ({pct_change:+.2f}%)" #formats result to 2dp for most recent close and percentage change and adds it to live_data dictionary
    except Exception: #if anything fails, fallback to "N/A"
        live_data[symbol] = "N/A"

for symbol, info in live_data.items(): #loops through dictionary and prints each stock's info in sidemenu
    st.sidebar.write(f"{symbol}: {info}")

period = PERIOD[period_key] #converts selected period key into yfinance format

if not ticker: #check if ticker is selected
    st.warning("Enter a ticker to begin.") #if not show warning and halts the app
    st.stop()

st.subheader(f"Displaying data for: {ticker}") #adds subheader to web interface indicating current stock being analyzed

def _get_df(_ticker: str, _period: str) -> pd.DataFrame: #gets base df from dataset function for graph visualisations
    return dataset(_ticker, _period) # calls dataset() function

try: #attempts to load data
    base_df = _get_df(ticker, period) #if successful, shows date range
    st.caption(f"Date range: {base_df.index.min().date()} to {base_df.index.max().date()}") # caption to show date range of data 
except Exception as e: #if fail
    st.error(f"Failed to retrieve data: {e}") #show error message
    st.stop()                                 #stops execution

# Tabs for web interface
tab1, tab2, tab3= st.tabs(["Close vs SMA", "Upward/Downward Runs", "Max profit(Buy/Sell)"]) #Creates 3 tabs

# Tab 1: Close vs SMA 
with tab1:
    sma_window = st.slider("SMA period", min_value=5, max_value=60, value=30, step=1) #user can change value of SMA slider
    df1 = calculate_sma(base_df.copy(), window=sma_window) # creating temp dataframe to store sma values
    if "Daily Returns" not in df1.columns: #ensure daily returns exist in dataframe
        df1 = daily_returns(df1)

    hover_ret = df1["Daily Returns"].fillna("—").to_numpy() #replaces missing returns with "-" and converts to NumPy for Plotly hover tooltips                                          

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter
                   (x=df1.index, #X = Date
                    y=df1["Close"], #Y = Close value
                    mode="lines", # Line Graph
                    name="Close", # Graph Name
                    customdata=hover_ret, # Daily Returns Value
                    hovertemplate="Date:%{x|%Y-%m-%d}<br>""Close:%{y:.2f}<br>""Daily Return:%{customdata}<extra></extra>")) #Formatting of data in display container
    fig1.add_trace(go.Scatter(x=df1.index, # X = Date
                              y=df1["SMA"], # Y = SMA value
                              mode="lines", # Line Graph
                              name=f"SMA{sma_window}", # SMA Values
                              hovertemplate="Date=%{x|%Y-%m-%d}<br>"f"SMA{sma_window}=%{{y:.2f}}<extra></extra>")) #Formatting of data in display container
    fig1.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend_title=None) #Graph layout
    st.plotly_chart(fig1, use_container_width=True)

    #Daily Returns graph (volatility)
    df1['Daily_Returns'] = df1['Close'].pct_change()
    st.header("Daily Returns Analysis")
    fig2 = px.line(df1, x=df1.index, y='Daily_Returns', title='Daily Volatility')
    fig2.update_traces(line_color='orange')
    st.plotly_chart(fig2, use_container_width=True)

# Tab 2: Shaded candlestick graph with up/down runs
with tab2:
    df2 = calculate_sma(base_df.copy(), window=sma_window) #Create copy of base dataframe
    df2 = daily_returns(df2)             #Stores daily return values into dataframe "df2"
    enriched = movement_direction(df2)   #Storing Direction & RunLength into dataframe "enriched"

    def _fmt_range(rr):
        if rr is None: return "—"
        a, b = pd.to_datetime(rr[0]).strftime("%Y-%m-%d"), pd.to_datetime(rr[1]).strftime("%Y-%m-%d")
        return f"{a} → {b}"
    
    summary = run_summary(enriched)

    # KPI tiles
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("UP runs",   summary["no_up_runs"])
    c2.metric("DOWN runs", summary["no_down_runs"])
    c3.metric("Longest UP",   f'{summary["longest_up_length"]}',   _fmt_range(summary["longest_up_range"]))
    c4.metric("Longest DOWN", f'{summary["longest_down_length"]}', _fmt_range(summary["longest_down_range"]))
   
    fig2 = go.Figure([ #candlestick chart showing OHLC data
        go.Candlestick(
            x=enriched.index, #Date
            open=enriched["Open"], #Gets open value from enriched dataframe
            high=enriched["High"], #Gets high value from enriched dataframe
            low=enriched["Low"], #Gets low value from enriched dataframe
            close=enriched["Close"], #Gets close value from enriched dataframe
            increasing_line_color="green", #Green for upward runs
            decreasing_line_color="red", #Red for downward runs
            name="OHLC")]) #Name of chart
    runs = enriched[enriched["Direction"].isin(["UP","DOWN"])].copy() #filter rows where movement direction is either up or down
    # identify run boundaries
    is_new = (runs["Direction"] != runs["Direction"].shift(1)).fillna(True) #marks start of new run when direction changes
    run_ids = is_new.cumsum() #assigns unique ID to each run using cumulative sum
    for _, grp in runs.groupby(run_ids): #loops of each run group
        d = grp["Direction"].iloc[0] #direction determines the color of the shading
        x0, x1 = grp.index.min(), grp.index.max() + pd.Timedelta(days=1) #start and end of run + add 1 day to x1 to make candlestick more visible
        fig2.add_vrect(x0=x0, x1=x1,fillcolor=("green" if d == "UP" else "red"),opacity=0.08, line_width=0) # add verticle rectangle (up = green, down = red)
    
    # concise KPI annotations on the chart
    fig2.add_annotation(
        xref="paper", yref="paper", x=0.01, y=1.07, showarrow=False, align="left",
        text=f"Longest UP: {summary['longest_up_length']} ({_fmt_range(summary['longest_up_range'])})"
    )
    fig2.add_annotation(
        xref="paper", yref="paper", x=0.40, y=1.07, showarrow=False, align="left",
        text=f"Longest DOWN: {summary['longest_down_length']} ({_fmt_range(summary['longest_down_range'])})"
    )

    fig2.update_layout(margin=dict(l=10, r=10, t=60, b=10), legend_title=None)
    st.plotly_chart(fig2, use_container_width=True)

    # Table displaying Close, SMA, Direction, RunLength
    show_cols = ["Close", "SMA", "Direction", "RunLength"]
    missing = [c for c in show_cols if c not in enriched.columns]
    if missing:
        st.error(f"Missing columns for table: {missing}") #checks if any columns are missing and displays error message if true
    else:
        st.dataframe(enriched[show_cols].tail(20)) #shows 20 table rows

# Tab 3: Max profit (Buy/Sell)
with tab3:
    
    df3 = calculate_sma(base_df.copy(), window=sma_window) #Creates copy of base dataframe
    #extract close prices and dates
    prices = df3["Close"].tolist()
    dates = list(df3.index)

    total_profit, transactions = max_profit_with_days(prices) #calls function to calculate buy/sell trades for max profit

    # Creating arrays for plotting of graph and table
    # b = buy date, s = sell date, bp = buy price, sp = sell price
    buy_x   = [dates[b]   for (b, _, _, _) in transactions]
    buy_y   = [prices[b]  for (b, _, _, _) in transactions]
    sell_x  = [dates[s]   for (_, s, _, _) in transactions]
    sell_y  = [prices[s]  for (_, s, _, _) in transactions]
    profit = [sp - bp    for (_, _, bp, sp) in transactions] # per trade profit or loss (sell price - buy price)

    # Chart
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df3.index, 
        y=df3["Close"], 
        mode="lines", 
        name="Close")) #add line chart of closing prices
    fig3.add_trace(go.Scatter(
        x=buy_x, 
        y=buy_y, 
        mode="markers", 
        name="Buy",
        marker=dict(symbol="triangle-up", size=10, color="green"),
        hovertemplate="Buy<br>Date=%{x|%Y-%m-%d}<br>Price=%{y:.2f}<extra></extra>")) #adds green triangle markers for buy signals with hover info showing date and price
    fig3.add_trace(go.Scatter(
        x=sell_x, 
        y=sell_y, 
        mode="markers", 
        name="Sell",
        marker=dict(symbol="triangle-down", size=10, color="red"),
        customdata=profit,hovertemplate=("Sell<br>Date=%{x|%Y-%m-%d}<br>""Price=%{y:.2f}<br>""Trade P/L=%{customdata:.2f}<extra></extra>"))) #adds red triangle for sell signals with hover info showing data, price and profit/loss
    fig3.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend_title=None)
    st.plotly_chart(fig3, use_container_width=True)

    #Total profit value and table
    st.metric("Total P/L (sum of all trades)", f"{total_profit:.2f}") #displays total profit/loss as a metric above the table
    if transactions: #checks if any trades were made
        transaction_df = pd.DataFrame({ #creates dataframe summarizing each trade
            "Trade Number":range(1, len(transactions) + 1), #range from 1 to max number of transactions + 1
            "Buy Date":[dates[b].date() for (b, _, _, _) in transactions], #get buy date from transaction dataframe
            "Sell Date":[dates[s].date() for (_, s, _, _) in transactions], #get sell date from transaction dataframe
            "Buy Price":[bp for (_, _, bp, _) in transactions], #get buy price from transaction dataframe
            "Sell Price":[sp for (_, _, _, sp) in transactions], #get sell price from transaction dataframe
            "Trade P/L":[sp - bp for (_, _, bp, sp) in transactions], #calculates profit/loss
        })
        st.dataframe(transaction_df, use_container_width=True)
    else:
        st.info("No profitable trades detected in the selected period.") #if no trades were made, shows info message
#===============================================================================================================
# WEB INTERFACE END
