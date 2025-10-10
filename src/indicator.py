import pandas as pd
import numpy as np

#function to calculate SMA (Sliding Window) approach
def calculate_sma(df: pd.DataFrame, window: int) -> pd.DataFrame:
    sma_values = [] # -> O(n) space to hold n values
    closes = df ['Close']
    if isinstance(closes, pd.DataFrame):
        closes = closes.squeeze() # Convert DataFrame to Series if necessary
    closes = closes.tolist() # -> O(n) time and space to convert to list

    window_sum = 0
    for i in range(len(closes)): # -> O(n) Loop
        window_sum += closes[i] # -> O(1) time and space (scalar variables)

        if i >=window:
            #subtract the value that just moved out of window
            window_sum -= closes[i - window] # -> O(1) time and space
        if i <window -1:
            #Not enough data points to compute SMA yet, so append None
            sma_values.append(None) # -> O(1) time and space
        else:
            #Compute SMA by dividing the sum of the window by the window size
            sma = window_sum / window
            sma_values.append(sma)

    df['SMA'] = sma_values #Adds SMA values to 'SMA' column in dataframe
    return df #Total time space complexity is O(n)

def daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    closes = df["Close"].reset_index(drop=True)  # O(n) time to copy/clean column; O(n) space for closes list
    returns = [np.nan]  # O(1) time & space for initialization

    last_valid_idx = 0  # O(1) time & space

    # Loop runs (n - 1) times → overall O(n) time
    for i in range(1, len(closes)):
        curr = closes[i]                # O(1) access
        prev = closes[last_valid_idx]   # O(1) access

        # Checking NaN and zero → O(1) time
        if pd.isna(curr) or pd.isna(prev) or prev == 0:
            returns.append(np.nan)      # O(1) amortized time, O(n) space overall for list
        else:
            change = ((curr - prev) / prev) * 100  # O(1) arithmetic operations
            returns.append(round(change, 2))       # O(1) rounding + append
            last_valid_idx = i                     # O(1) assignment

    df["Daily Returns"] = returns  # O(n) time to assign new column; O(n) space
    return df  # Total time: O(n), Total space: O(n)

