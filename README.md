# Stock Market Trend Analysis 
Interactive Streamlit dashboard for exploring stock prices, up/down streaks, and max-profit (buy/sell) scenarios. Core logic is packaged under src/ with unit tests in tests/.

Team List:
* Ang Wei Long (2500447@sit.singaporetech.edu.sg)
* Anandan Madhu Mowli (2501922@sit.singaporetech.edu.sg)
* Lim Jun Hong (2501666@sit.singaporetech.edu.sg)
* Chloe Lim (2503580@sit.singaporetech.edu.sg)
* Chan Si Ying, Nasya (2502538@sit.singaporetech.edu.sg)

## **Project Structure**
```
P4-3-sandbox/
├─ src/
│  ├─ data.py            # dataset() -> fetches yfinance OHLC data
│  ├─ indicator.py       # calculate_sma(), daily_returns()
│  ├─ max_profit.py      # max_profit_with_days()
│  └─ streaks.py         # movement_direction(), run_summary()
├─ tests/
│  ├─ conftest.py        # adds project root to sys.path for imports
│  ├─ test_sma.py        # SMA & returns tests
│  └─ test_streak.py     # streak detection tests
├─ main.py               # Streamlit app entry point
├─ pyproject.toml        # deps + pytest config
└─ README.md
```

## **Requirements**
- Before running the code, make sure you have **Python 3.x** installed.
- Internet access (for yfinance ticker data)
- Install the dependencies below:
```bash
pip install yfinance

```
```bash
pip install plotly
```
```bash
pip install streamlit
```
## **Run The App**
```bash
streamlit run main.py
```

## **Testing**

Run all tests:
```bash
pytest -q
```
Run a specific test (e.g. streak test):
```bash
pytest tests/test_streak.py -q
```
Run a single test (e.g test_flats_break_runs):
```bash
pytest tests/test_streak.py::test_flats_break_runs -q
```