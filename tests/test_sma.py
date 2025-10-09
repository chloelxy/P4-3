import pandas as pd
import src.indicator as indicator
import yfinance as yf

# SMA Validation using Pandas rolling mean, Takes in dataframe and window size
def test_sma(df, window=5, n=20):
    # Custom SMA
    df_custom = indicator.calculate_sma(df.copy(), window)

    # Pandas SMA
    df_expected = df.copy()
    df_expected["SMA_Rolling"] = df_expected["Close"].rolling(window=window).mean()

    # Build comparison table
    comparison = pd.DataFrame({
        "Close": df_custom["Close"].squeeze(),
        "Custom_SMA": df_custom["SMA"].squeeze(),
        "Pandas_SMA": df_expected["SMA_Rolling"].squeeze(),
    })
    # Drop rows with NaN in either SMA column
    comparison = comparison.dropna(subset=["Custom_SMA", "Pandas_SMA"])
    # Limit to first n rows after dropping NaN
    comparison = comparison.head(n)
    # Add True/False column
    comparison["Match"] = comparison["Custom_SMA"].round(5).eq(comparison["Pandas_SMA"].round(5))

    print("=================== SMA Validation Results: ===================")
    print(comparison)
    if comparison["Match"].all():
        print(f"\n✅ PASS: All values match (window={window}, first {n} non-NaN rows)")
    else:
        print(f"\n❌ FAIL: Some mismatches found (window={window}, first {n} non-NaN rows)")
    print("===============================================================")
    return comparison

def test_daily_returns(df, n=20):
    # Custom Daily Returns
    df_custom = indicator.daily_returns(df.copy())

    # Pandas Daily Returns
    df_expected = df.copy()
    df_expected["Pandas_Daily_Returns"] = df_expected["Close"].pct_change() * 100
    df_expected["Pandas_Daily_Returns"] = df_expected["Pandas_Daily_Returns"].round(2).astype(str) + "%"

    # Build comparison table
    comparison_daily = pd.DataFrame({
        "Close": df_custom["Close"].squeeze(),
        "Custom_Daily_Returns": df_custom["Daily Returns"].squeeze(),
        "Pandas_Daily_Returns": df_expected["Pandas_Daily_Returns"].squeeze(),
    })
    # Drop rows with NaN in either Daily Returns column
    comparison_daily = comparison_daily.dropna(subset=["Custom_Daily_Returns", "Pandas_Daily_Returns"])
    # Limit to first n rows after dropping NaN
    comparison_daily = comparison_daily.head(n)
    # Add True/False column
    comparison_daily["Match"] = comparison_daily["Custom_Daily_Returns"].eq(comparison_daily["Pandas_Daily_Returns"])
    print("\n Now running tests for Daily Returns...\n")
    print("=================== Daily Returns Validation Results: ===================")
    print(comparison_daily)
    if comparison_daily["Match"].all():
        print(f"\n✅ PASS: All values match (first {n} non-NaN rows)")
    else:
        print(f"\n❌ FAIL: Some mismatches found (first {n} non-NaN rows)")
    print("==========================================================================")
    return comparison_daily

if __name__ == "__main__":
    df = yf.download("AAPL", period="1mo", interval="1d", auto_adjust=True)
    comparison_sma = test_sma(df, window =5, n=20)
    comparison_daily = test_daily_returns(df, n=20)