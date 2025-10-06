# validation_max_profit.py
import pandas as pd
from MaxProfitCalculator import max_profit_with_days
import indicator
import yfinance as yf
# 👆 replace 'your_module_filename' with the actual filename of your code (without .py)

def run_validations():
    test_cases = [
        # (prices, expected_profit, description)
        ([7,1,5,3,6,4], 7, "Normal case with ups & downs"),
        ([1,2,3,4,5], 4, "Strictly increasing"),
        ([5,4,3,2,1], 0, "Strictly decreasing"),
        ([2,2,2,2], 0, "Flat prices"),
        ([1,3,2,8,4,9], 13, "Multiple transactions"),
        ([], 0, "Empty list"),
        ([5], 0, "Single price"),
    ]

    print("Running validation tests...\n")
    for prices, expected, desc in test_cases:
        profit, transactions = max_profit_with_days(prices)
        result = "PASS ✅" if profit == expected else f"FAIL ❌ (Got {profit})"
        print(f"{desc:25} | Prices: {prices} | Expected: {expected} | {result}")

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

if __name__ == "__main__":
    run_validations()
    df = yf.download("AAPL", period="1mo", interval="1d", auto_adjust=True)
    comparison = test_sma(df, window =5, n=20)
