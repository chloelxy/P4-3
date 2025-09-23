import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime

#load the dataset
def dataset(stock, period):
    stock = yf.Ticker(stock)
    hist = stock.history(period=period)
    df = pd.DataFrame(hist)
    print("Your dataframe is:\n")
    print(df)
    return df

#function to remove rows with missing values
def calculate_sma(df, window):
    sma_values = []
    closes = df['Close'].tolist()

    for i in range(len(closes)):
        if i < window - 1:
            sma_values.append(None) #Not enough data
        else:
            window_sum = sum(closes[i - window + 1: i+1])
            sma = window_sum /window
            sma_values.append(sma)

    df['SMA'] = sma_values
    return df

def plotting_graph(sma_values):
    try:
        df_plot = sma_values.copy()
        # yfinance returns Date as index; ensure we have a 'Date' column
        if 'Date' not in df_plot.columns:
            df_plot = df_plot.reset_index().rename(columns={'index': 'Date'})
        # Coerce and sort by date
        df_plot['Date'] = pd.to_datetime(df_plot['Date'], errors='coerce')
        df_plot = df_plot.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)

        dates = df_plot['Date']
        close_price = df_plot['Close']
        sma = df_plot['SMA']

        plt.figure(figsize=(12, 6))
        plt.plot(dates, close_price, label='Close Price', color='blue')
        plt.plot(dates, sma, label = 'SMA', color='orange')

        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.title('Stock Price Vs SMA')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    except Exception as error:
        print(f"Error plotting graph: {error}")
