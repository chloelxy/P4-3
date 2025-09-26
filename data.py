import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime

# load the dataset
def dataset(stock, period):
    stock = yf.Ticker(stock)
    hist = stock.history(period=period)
    df = pd.DataFrame(hist)
    print("Your dataframe is:\n")
    print(df)
    return df