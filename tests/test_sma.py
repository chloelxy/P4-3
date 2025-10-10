import pandas as pd
from src.indicator import calculate_sma, daily_returns
import numpy as np
import time

# ----------------- Helper Functions -----------------

def time_function(func, *args, **kwargs):
    """Measures and returns the result and duration of a function call."""
    start = time.time()
    result = func(*args, **kwargs)
    duration = time.time() - start
    return result, duration


def print_comparison(df, col_manual, col_pandas, label):
    df[col_manual] = df[col_manual].round(2)
    df[col_pandas] = df[col_pandas].round(2)
    df['Match'] = np.isclose(df[col_manual], df[col_pandas], equal_nan=True)
    print(f"\n {label}")
    print(df[[col_manual, col_pandas, 'Match']])
    print(f"✅ All Match: {df['Match'].all()}\n")


# ----------------- Test Datasets -----------------

def get_test_cases():
    return {
        "Increasing": [100, 105, 110, 115, 120],
        "Fluctuating": [100, 102, 99, 105, 103],
        "Constant": [50, 50, 50, 50, 50],
        "Decreasing": [120, 115, 110, 105, 100],
        "With missing": [100, np.nan, 120, np.nan, 130]
    }


# ----------------- SMA Validation -----------------

def validate_sma(window=3):
    print("\n================= SMA Validation =================\n")
    test_cases = get_test_cases()

    for name, prices in test_cases.items():
        df = pd.DataFrame({'Close': prices})

        # Manual SMA
        df_manual = df.copy()
        df_manual, t_manual = time_function(calculate_sma, df_manual, window)
        df['Manual_SMA'] = df_manual['SMA']

        # Pandas SMA
        df['Pandas_SMA'], t_pandas = time_function(
            lambda x: x['Close'].rolling(window).mean(), df
        )

        print(f" Test Case: {name}")
        print_comparison(df, 'Manual_SMA', 'Pandas_SMA', "SMA Comparison")
        print(f"⏱ Manual Time: {t_manual:.6f}s | Pandas Time: {t_pandas:.6f}s")
        print("-" * 50)


# ----------------- Daily Returns Validation -----------------

def validate_daily_returns():
    print("\n============== Daily Returns Validation ==============\n")
    test_cases = get_test_cases()

    for name, prices in test_cases.items():
        df = pd.DataFrame({'Close': prices})

        # Manual Returns
        df_manual = df.copy()
        df_manual, t_manual = time_function(daily_returns, df_manual)
        df['Manual_Returns'] = df_manual['Daily Returns']

        # Pandas Returns
        df['Pandas_Returns'], t_pandas = time_function(
            lambda x: x['Close'].pct_change(fill_method=None) * 100, df
        )

        print(f" Test Case: {name}")
        print_comparison(df, 'Manual_Returns', 'Pandas_Returns', "Daily Returns Comparison")
        print(f"⏱ Manual Time: {t_manual:.6f}s | Pandas Time: {t_pandas:.6f}s")
        print("-" * 50)


# ----------------- Run Both -----------------

if __name__ == "__main__":
    validate_sma(window=3)
    validate_daily_returns()


