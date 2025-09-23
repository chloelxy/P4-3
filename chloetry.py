import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Get Files
DATA_DIR = Path("data")
FILES = {
    "EIGHTCO": DATA_DIR / "eightco.csv",
    "BITDEER": DATA_DIR / "bitdeer.csv",
    "RIGETTI": DATA_DIR / "rigetti.csv",
}

#Date format variable
DATE_FMT = "%d-%b-%y"

#Get data from csv and store in dataframe
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        sys.exit(f"File not found: {path}")
    df = pd.read_csv(path)
    
    #Change date format to yyyy-mm-dd 
    df["Date"] = pd.to_datetime(df["Date"], format=DATE_FMT, errors="coerce")
    
    for col in ["Open","High","Low","Close","Adj Close","Volume"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .where(lambda s: s.ne("nan"))
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    if "Close" not in df.columns:
        sys.exit("CSV must contain a 'Close' column.")
    return df
            
    #sort according to asc order 
    # df = df.sort_values("Date").drop_duplicates(subset=["Date"])
    # df = df.set_index("Date")
    
    # print(df.head(10))
    # print(df.tail(10))
    
#Get daily direction of stock price movement, upward, downward or flat    
def movement_direction(df: pd.DataFrame) -> pd.DataFrame:
    stocks = df.copy()
    closing_price_change = stocks["Close"].diff()
    direction = closing_price_change.where(closing_price_change.notna(), 0.0)
    direction = direction.apply(lambda x: "UP" if x > 0 else ("DOWN" if x < 0 else "FLAT"))
    #store direction in new column in dataframe
    stocks["Direction"] = direction
    
    # print(type(stocks["Direction"]))
    
    # if flat, not counted as streak, so we only consider up and down
    streak_type = stocks["Direction"].isin(["UP", "DOWN"])
    # if current direction is different from previous day, new run
    run_change = (stocks["Direction"] != stocks["Direction"].shift(1)) & streak_type
    # create new column to store run ids
    stocks["RunID"] = 0
    stocks.loc[streak_type, "RunID"] = run_change[streak_type].cumsum()
    
    # calculate length of each run
    stocks["RunLength"] = 0
    for runid, grp in stocks[streak_type].groupby("RunID"):
        stocks.loc[grp.index, "RunLength"] = range(1, len(grp) + 1)
    
    return stocks

#summary of runs, store in dict
def run_summary(df: pd.DataFrame) -> dict:
    #only consider up and down runs
    runs = df[df["Direction"].isin(["UP", "DOWN"])].copy()
    # if runs.empty:
    #     return {"TotalRuns": 0, "AvgRunLength": 0, "MaxRunLength": 0}
    
    # total_runs = runs["RunID"].nunique()
    # avg_run_length = runs["RunLength"].mean()
    # max_run_length = runs["RunLength"].max()
    
    # return {
    #     "TotalRuns": total_runs,
    #     "AvgRunLength": avg_run_length,
    #     "MaxRunLength": max_run_length
    # }
    
    if runs.empty:
        return{
            "no_up_runs": 0, "no_down_runs": 0, "longest_up_length": 0, "longest_up_range": None,
            "longest_down_length": 0, "longest_down_range": None
        }
        
    #run counts
    run_groups = runs.groupby(["RunID", "Direction"])
    run_lengths = run_groups.size().rename("Length").reset_index()
    no_up_runs = (run_lengths["Direction"] == "UP").sum()
    no_down_runs = (run_lengths["Direction"] == "DOWN").sum()

    
    #longest up run
    up_runs = run_lengths[run_lengths["Direction"] == "UP"]
    if not up_runs.empty:
        up_max_length = up_runs["Length"].max()
        up_rid = up_runs.loc[up_runs["Length"].idxmax(), "RunID"]
        up_idx = runs[runs["RunID"] == up_rid].index
        up_range = (up_idx.min(), up_idx.max())
    else:
        up_max_length, up_range = 0, None
        
    #longest down run
    down_runs = run_lengths[run_lengths["Direction"] == "DOWN"]
    if not down_runs.empty:
        down_max_length = down_runs["Length"].max() #longest streak length
        down_rid = down_runs.loc[down_runs["Length"].idxmax(), "RunID"]
        down_idx = runs[runs["RunID"] == down_rid].index
        down_range = (down_idx.min(), down_idx.max()) # start and end date 
    else:
        down_max_length, down_range = 0, None
        
    return{
        "no_up_runs": int(no_up_runs), "no_down_runs": int(no_down_runs), 
        "longest_up_length": int(up_max_length), "longest_up_range": up_range,
        "longest_down_length": int(down_max_length), "longest_down_range": down_range
    }
    
def main():
    stock_list = list(FILES.keys())
    print(f"Available stocks: {', '.join(stock_list)}")
    
    while True:
        stock_choice = input(f"Enter stock name to view trend summary ({'/'.join(stock_list)}): ").strip().upper()
        if stock_choice in FILES:
            break
        print("Invalid stock choice. Try again.")

    while True:
        date_input = input("Enter date (format: dd-MMM-yy, e.g., 12-Sep-25): ").strip()
        try:
            chosen_date = datetime.strptime(date_input, DATE_FMT).date()
            break
        except ValueError:
            print(f"Invalid date format. Please use dd-MMM-yy.")
    
    #load data in dataframe for chosen stock        
    df = load_csv(FILES[stock_choice])
    
    if chosen_date not in df["Date"].dt.date.values:
        available_dates = df["Date"].dt.date
        previous_dates = [d for d in available_dates if d <= chosen_date]
        if not previous_dates:
            sys.exit("Date not found, and no earlier trading day available.")
        chosen_date = max(previous_dates)
        print(f"Date not found. Using nearest previous trading day: {chosen_date}")
        
    #get data up to chosen date
    df_upto = df.loc[:pd.Timestamp(chosen_date)]
    if df_upto.empty:
        sys.exit("No data up to that date.")
        
    enriched_df = movement_direction(df_upto)
    summary = run_summary(enriched_df)
    
    target_row = enriched_df.loc[pd.Timestamp(chosen_date)]
    direction = target_row["Direction"]
    run_length = int(target_row["RunLength"]) if pd.notna(target_row["RunLength"]) else 0
    
    # summary table
    print("\n=== Daily Details ===")
    print(f"Stock: {stock_choice}")
    print(f"Date:  {chosen_date}")
    print(f"Close: {target_row['Close']:.4f}")
    print(f"Direction: {direction}")
    print(f"Run length (for this {direction if direction in ['UP','DOWN'] else 'day'}): {run_len}")

    print("\n=== Run Summary (up to selected date) ===")
    print(f"Total UP runs:   {summary['num_up_runs']}")
    print(f"Total DOWN runs: {summary['num_down_runs']}")

    lu, lur = summary["longest_up_len"], summary["longest_up_range"]
    ld, ldr = summary["longest_down_len"], summary["longest_down_range"]

    def fmt_range(rr):
        if rr is None:
            return "-"
        s, e = rr
        return f"{s.date()} → {e.date()}"

    print(f"Longest UP streak:   {lu} days  ({fmt_range(lur)})")
    print(f"Longest DOWN streak: {ld} days  ({fmt_range(ldr)})")
    
    
if __name__ == "__main__":
    main()