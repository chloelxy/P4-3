import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- max profit function ---
def max_profit_with_days(prices):
    """
    Calculates maximum profit with multiple transactions allowed
    and records actual buy/sell days.
    """
    # If prices list is empty or has only one day, no transactions possible
    if not prices or len(prices) < 2: #check if there is prices in a list & ensure the number of days is = 2 or > 2 in order to do comparison
        return 0, []

    profit = 0
    transactions = []
    i = 0
    n = len(prices)

    # Loop through the prices list
    while i < n - 1: #The loop never reaches i = 5, so you won’t accidentally do prices[6] (which doesn’t exist).index is till 5


        # Find local minima (buy day)
        while i < n - 1 and prices[i + 1] <= prices[i]: #As long as the next day’s price is lower or equal to today’s price, keep moving forward we are skipping days where the stock is flat or going down
            i += 1 #Move the index forward by 1 day.
        if i == n - 1: # reached the end “Did we land on the very last day of data?” If yes, there’s no point in buying (because there’s no future day to sell).
            break
        buy_day = i
        buy_price = prices[i]

        i += 1 #Move to the next day After deciding the buy day, we look ahead to search for a good sell day

        # Find local maxima (sell day)
        while i < n and (i == n - 1 or prices[i] >= prices[i - 1]):#don’t go past the last day. AND If we’re at the last day → stop here (must sell) Otherwise, keep looping as long as today’s price is higher than yesterday’s (still rising).
            if i == n - 1 or (i < n - 1 and prices[i + 1] < prices[i]):#"“Am I on the very last day?”If yes → we can’t go further, so we must sell here." OR check if tomorrow’s price is lower than today’s price.If yes → it means the price is about to drop.So we should selltoday to lock in profit before it falls.
                break
            i += 1 #iis day
        sell_day = i
        sell_price = prices[i]

        # Record the transaction and add profit
        transactions.append((buy_day, sell_day, buy_price, sell_price))
        profit += sell_price - buy_price

        i += 1 # Move to next day after selling

    return profit, transactions

# --- fetch prices from yfinance ---
def fetch_prices_for_algo(ticker, start, end_inclusive, interval='1d'):#Creates a function that takes a stock symbol, start date, end date, and time interval
    end_dt = datetime.strptime(end_inclusive, "%Y-%m-%d") + timedelta(days=1) #Adds 1 day to the end date because Yahoo Finance's end parameter is exclusive
    end = end_dt.strftime("%Y-%m-%d")#Converts back to string format (YYYY-MM-DD)

    df = yf.download( #Downloads stock data from Yahoo Finance
        ticker,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=True,  # Simplified: always use auto_adjust #auto_adjust=True automatically adjusts for stock splits/dividends
        progress=False #progress=False hides the download progress bar
    )

    if df.empty: #Checks if data is empty - if no data found, shows an error message
        raise ValueError("No data returned. Check ticker/date range/interval.")

    # SIMPLIFIED column selection
    numeric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist() #Finds all number columns (prices, volumes, etc.) in the data
    if len(numeric_cols) == 0: #Makes sure there are actual price numbers in the data
        raise ValueError(f"No numeric columns found in df: {df.columns.tolist()}")
    price_col = numeric_cols[0] #Picks the first number column (usually the main price column)
    print("Using numeric column for prices:", price_col) #Prints which column is being used

    df = df.dropna(subset=[price_col]) #Removes rows where the price is missing/empty
    prices = df[price_col].tolist() #Converts prices to a simple list of numbers
    dates = list(df.index) #Gets the dates for each price point

    print("Number of prices extracted:", len(prices)) #Shows how many prices were found
    return prices, dates, df #Returns three things: price list, date list, and the full data table

# --- Main runner ---
if __name__ == "__main__":
    while True:
        try:
            ticker = input("Enter stock ticker (e.g., AAPL): ").upper().strip() #Asks for stock symbol (like AAPL for Apple) Converts to uppercase (AAPL instead of aapl) strip is spacing
            if ticker.lower() in ['quit', 'exit']: #Checks if user wants to quit at any point
                print("Goodbye!")
                break

            start = input("Enter start date (YYYY-MM-DD): ").strip() #Gets the date range for analysis
            if start.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break

            end = input("Enter end date (YYYY-MM-DD): ").strip() #Gets the date range for analysis
            if end.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break

            # Basic validation
            if not ticker or not start or not end:
                print("❌ All fields are required. Please try again.\n") #Makes sure user entered something for all three fields
                continue

            # Fetch prices and run analysis
            prices, dates, df = fetch_prices_for_algo(ticker, start, end) #Calls the previous function to get stock prices
            profit, transactions = max_profit_with_days(prices) #Runs trading algorithm to find best buy/sell opportunities

            # Display results
            print(f"\nTotal profit: ${profit:.2f}") #Shows total profit possible
            if transactions:
                print("Transactions:")
                for b, s, bp, sp in transactions:
                    print(f"Buy {dates[b].date()} @ ${bp:.2f}, Sell {dates[s].date()} @ ${sp:.2f}, Profit ${sp - bp:.2f}") #Lists each trade: Buy date/price, Sell date/price, Profit made
            else:
                print("No profitable transactions found.")

            # Ask if user wants to analyze another stock
            another = input("\nAnalyze another stock? (y/n): ").lower().strip()
            if another not in ['y', 'yes']:
                print("Goodbye!")
                break
            print()

        except Exception as e: #Catches any errors (wrong dates, invalid stock symbol, etc.) # Shows friendly error message instead of crashing
            print(f"❌ Error: {e}") #Program continues running so user can try again
            print("Please try again or type 'quit' to exit.\n")