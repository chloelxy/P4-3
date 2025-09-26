from datetime import datetime
import pandas as pd
from data import dataset  
from streak import movement_direction, run_summary
import indicator
from MaxProfitCalculator import fetch_prices_for_algo, max_profit_with_days

PERIOD = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "5Y": "5y", "MAX": "max"}

DATE_FORMATS = ("%d-%b-%y", "%Y-%m-%d")

def fmt_range(rr):
    if rr is None:
        return "-"
    s, e = rr
    return f"{s.date()} → {e.date()}"

# front end codes: graph 

# main to run the program, to add each persons functions together
def main():
    
    #input ticker and period
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

    while True:
        period_input = input("Enter period (1M, 3M, 6M, 1Y, 2Y, 5Y, MAX): ").strip().upper()
        if period_input in PERIOD:
            period = PERIOD[period_input]
            break
        print("Invalid period. Try again.")
    #get Sma period
    while True:
        try:
            window = int(input("Enter SMA Period (5, 10, 21...): ").strip())
            if window > 0:
                window = window
                break
            else:
                print("Invalid SMA. Try again.")
        except ValueError:
            print("Invalid input. Try again.")
        
    #get period data
    df = dataset(ticker, period)
    if df.empty or df is None:
        print("No data returned.")
        return
    
    df = df.sort_index()
    if "Close" not in df.columns:
        print("Data has no 'Close' column.")

    sma_values = indicator.calculate_sma(df, window) #Manual calculate SMA
    returns = indicator.daily_returns(df)

    print(f"{window}-Day SMA:\n {sma_values}")

    # Upward Downward movement direction and streak summary - Start
    enriched_df = movement_direction(df)
    summary = run_summary(enriched_df)
    
    #Streak summary
    print("\nLast 10 rows with streak info:")
    print(enriched_df[["Close", "Direction", "RunID", "RunLength"]].tail(10))
    print("\n=== Run Summary (for selected period) ===")
    print(f"Total UP runs:   {summary['no_up_runs']}")
    print(f"Total DOWN runs: {summary['no_down_runs']}")
    print(f"Longest UP streak:   {summary['longest_up_length']} days  ({fmt_range(summary['longest_up_range'])})")
    print(f"Longest DOWN streak: {summary['longest_down_length']} days  ({fmt_range(summary['longest_down_range'])})")
    
    # Upward Downward movement direction and streak summary - End
        

if __name__ == "__main__":
    main()