from __future__ import annotations
from typing import Dict, Hashable, Tuple
import numpy as np
import pandas as pd

__all__ = ["movement_direction", "run_summary"]

# ---------- Validation ----------
def require_columns(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

def ensure_numeric_series(s: pd.Series, name: str) -> pd.Series:
    if not isinstance(s, pd.Series):
        raise TypeError(f"{name} must be a pandas Series")
    # Non-numeric -> NaN (these rows become FLAT via diff)
    return pd.to_numeric(s, errors="coerce")


# ---------- Public API ----------
def movement_direction(df: pd.DataFrame, *, close_col: str = "Close") -> pd.DataFrame:
    """
    Add Direction/RunID/RunLength columns describing up/down streaks.

    Direction rules:
      - "UP"   if Close[t] > Close[t-1]
      - "DOWN" if Close[t] < Close[t-1]
      - "FLAT" otherwise (incl. NaN comparisons)

    FLAT rows are not part of a streak (RunID=0, RunLength=0).
    A new streak starts whenever Direction changes between UP/DOWN.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    require_columns(df, [close_col])

    out = df.copy()
    close = ensure_numeric_series(out[close_col], close_col)
    delta = close.diff()

    direction = pd.Series(
        np.where(delta > 0, "UP", np.where(delta < 0, "DOWN", "FLAT")),
        index=out.index,
        dtype="object",
    )
    out["Direction"] = direction

    mask = direction.isin(["UP", "DOWN"])
    run_change = (direction != direction.shift(1)) & mask

    run_id = pd.Series(0, index=out.index, dtype="int64")
    run_id.loc[mask] = run_change.loc[mask].cumsum()
    out["RunID"] = run_id

    run_len = pd.Series(0, index=out.index, dtype="int64")
    if mask.any():
        run_len.loc[mask] = run_id.loc[mask].groupby(run_id.loc[mask]).cumcount() + 1
    out["RunLength"] = run_len

    return out


def run_summary(df: pd.DataFrame) -> Dict[str, object]:
    """
    Summarize runs (counts + longest UP/DOWN).
    Expects columns: Direction, RunID. Index used to report ranges.
    """
    require_columns(df, ["Direction", "RunID"])

    runs = df[df["Direction"].isin(["UP", "DOWN"])]
    if runs.empty:
        return {
            "no_up_runs": 0,
            "no_down_runs": 0,
            "longest_up_length": 0,
            "longest_up_range": None,
            "longest_down_length": 0,
            "longest_down_range": None,
        }

    sizes = runs.groupby(["RunID", "Direction"]).size().rename("Length")
    rows = sizes.reset_index()

    no_up_runs = int((rows["Direction"] == "UP").sum())
    no_down_runs = int((rows["Direction"] == "DOWN").sum())

    def _longest(d: str) -> Tuple[int, Tuple[Hashable, Hashable] | None]:
        sub = rows[rows["Direction"] == d]
        if sub.empty:
            return 0, None
        r_id = int(sub.loc[sub["Length"].idxmax(), "RunID"])
        L = int(sub["Length"].max())
        idx = runs[runs["RunID"] == r_id].index
        return L, (idx.min(), idx.max())

    up_L, up_range = _longest("UP")
    down_L, down_range = _longest("DOWN")

    return {
        "no_up_runs": no_up_runs,
        "no_down_runs": no_down_runs,
        "longest_up_length": up_L,
        "longest_up_range": up_range,
        "longest_down_length": down_L,
        "longest_down_range": down_range,
    }
