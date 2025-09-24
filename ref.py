# streak.py
from data import dataset   # import your dataset() function
import pandas as pd

def label_directions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    delta = out["Close"].diff()
    direction = delta.where(delta.notna(), 0.0).apply(
        lambda x: "UP" if x > 0 else ("DOWN" if x < 0 else "FLAT")
    )
    out["Direction"] = direction

    mask_ud = out["Direction"].isin(["UP", "DOWN"])
    run_change = (out["Direction"] != out["Direction"].shift(1)) & mask_ud
    out["RunID"] = 0
    out.loc[mask_ud, "RunID"] = run_change[mask_ud].cumsum()

    out["RunLength"] = 0
    for _, grp in out[mask_ud].groupby("RunID"):
        out.loc[grp.index, "RunLength"] = range(1, len(grp) + 1)
    return out


def summarize_runs(df: pd.DataFrame) -> dict:
    runs = df[df["Direction"].isin(["UP", "DOWN"])]
    if runs.empty:
        return {
            "num_up_runs": 0, "num_down_runs": 0,
            "longest_up_len": 0, "longest_up_range": None,
            "longest_down_len": 0, "longest_down_range": None,
        }

    rl = runs.groupby(["RunID", "Direction"]).size().rename("Len").reset_index()
    num_up_runs = int((rl["Direction"] == "UP").sum())
    num_down_runs = int((rl["Direction"] == "DOWN").sum())

    def _longest(direction: str):
        rows = rl[rl["Direction"] == direction]
        if rows.empty: return 0, None
        max_len = int(rows["Len"].max())
        rid = rows.loc[rows["Len"].idxmax(), "RunID"]
        idx = runs[runs["RunID"] == rid].index
        return max_len, (idx.min(), idx.max())

    up_len, up_range = _longest("UP")
    down_len, down_range = _longest("DOWN")

    return {
        "num_up_runs": num_up_runs,
        "num_down_runs": num_down_runs,
        "longest_up_len": up_len,
        "longest_up_range": up_range,
        "longest_down_len": down_len,
        "longest_down_range": down_range,
    }


def main():
    tk = input("Enter stock ticker (e.g. AAPL, TSLA): ").strip().upper()
    period = input("Enter period (e.g. 6mo, 1y): ").strip() or "6mo"

    # call dataset() from data.py
    df = dataset(tk, period)
    if df.empty:
        print("No data returned.")
        return

    enriched = label_directions(df)
    summary = summarize_runs(enriched)

    print("\nLast 10 rows with streak info:")
    print(enriched[["Close", "Direction", "RunID", "RunLength"]].tail(10))

    def fmt_range(rr):
        if rr is None: return "-"
        s, e = rr
        return f"{s.date()} → {e.date()}"

    print("\n=== Run Summary ===")
    print(f"Total UP runs:   {summary['num_up_runs']}")
    print(f"Total DOWN runs: {summary['num_down_runs']}")
    print(f"Longest UP streak:   {summary['longest_up_len']} days ({fmt_range(summary['longest_up_range'])})")
    print(f"Longest DOWN streak: {summary['longest_down_len']} days ({fmt_range(summary['longest_down_range'])})")


if __name__ == "__main__":
    main()
