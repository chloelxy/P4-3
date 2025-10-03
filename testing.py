# validation_max_profit.py
from MaxProfitCalculator import max_profit_with_days
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

    print("🔍 Running validation tests...\n")
    for prices, expected, desc in test_cases:
        profit, transactions = max_profit_with_days(prices)
        result = "PASS ✅" if profit == expected else f"FAIL ❌ (Got {profit})"
        print(f"{desc:25} | Prices: {prices} | Expected: {expected} | {result}")

if __name__ == "__main__":
    run_validations()
