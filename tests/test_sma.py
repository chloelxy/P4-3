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

    # Print once
    print("=================== SMA Validation Results: ===================")
    print(comparison)

    if comparison["Match"].all():
        print(f"\n✅ PASS: All values match (window={window}, first {n} non-NaN rows)")
    else:
        print(f"\n❌ FAIL: Some mismatches found (window={window}, first {n} non-NaN rows)")

    print("===============================================================")
    return comparison