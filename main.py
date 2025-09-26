from datetime import datetime
import pandas as pd
from data import dataset  
from streak import movement_direction, run_summary  

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
        ticker = input("Enter stock ticker (e.g. AAPL, TSLA): ").strip().upper()
        if ticker:
            break
        print("Invalid Ticker. Try again.")
        
    while True:
        period_input = input("Enter period (1M, 3M, 6M, 1Y, 2Y, 5Y, MAX): ").strip().upper()
        if period_input in PERIOD:
            period = PERIOD[period_input]
            break
        print("Invalid period. Try again.")
        
    #get period data
    df = dataset(ticker, period)
    if df.empty or df is None:
        print("No data returned.")
        return
    
    df = df.sort_index()
    if "Close" not in df.columns:
        print("Data has no 'Close' column.")
        
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