import matplotlib.pyplot as plt
import pandas as pd

#function to calculate SMA (Sliding Window) approach
def calculate_sma(df, window):
    sma_values = [] # -> O(n) space to hold n values
    closes = df['Close'].tolist() # -> O(n) time and space to convert to list

    window_sum = 0
    for i in range(len(closes)): # -> O(n) Loop
        window_sum += closes[i] # -> O(1) time and space (scalar variables)

        if i >=window:
            #subtract the value that just moved out of window
            window_sum -= closes[i-window] # -> O(1) time and space
        if i <window -1:
            #Not enough data points to compute SMA yet, so append None
            sma_values.append(None) # -> O(1) time and space
        else:
            #Compute SMA by dividing the sum of the window by the window size
            sma = window_sum / window
            sma_values.append(sma)

    df['SMA'] = sma_values #Adds SMA values to 'SMA' column in dataframe
    return df #Total time space complexity is O(n)

def daily_returns(df):
    returns = [] #storing n values in list -> O(n) space
    closes = df['Close'].tolist()

    for i in range(1, len(closes)): #loop runs from 1 to n-1 -> (n-1) -> O(n)
        prev = closes[i-1]
        curr = closes[i]
        daily_return = (((curr - prev) / prev) * 100) #Basic arithmetic and indexing -> O(1)
        daily_return = round(daily_return, 2)
        returns.append(f"{daily_return}%")

    # adds NaN to list so the value is aligned with original dataframe
    returns = [None] + returns # returns takes O(n) time and space to construct a new list

    df['Daily Returns'] = returns #Assigning column to dataframe is O(n)
    return df #Total time and space complexity is O(n)
