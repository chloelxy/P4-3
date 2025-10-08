# tests/test_streaks.py
import numpy as np
import pandas as pd
import pytest
from src.streaks import movement_direction, run_summary



# ---------- helpers ----------
def df_ohlc_from_close(vals, start="2025-01-01", freq="D"):
    idx = pd.date_range(start, periods=len(vals), freq=freq)
    s = pd.Series(vals, index=idx, name="Close")
    # simple OHLC scaffold so Candlestick has columns
    return pd.DataFrame({"Open": s, "High": s, "Low": s, "Close": s})


# ---------- validation / shape ----------
def test_missing_close_raises_keyerror():
    df = pd.DataFrame({"Open": [1, 2], "High": [1, 2], "Low": [1, 2]})
    with pytest.raises(KeyError):
        movement_direction(df)

def test_non_numeric_close_coerces_to_flat():
    df = df_ohlc_from_close([1, "x", 2])  # "x" -> NaN => FLAT at both boundaries
    out = movement_direction(df)
    assert "FLAT" in out["Direction"].values

def test_flat_rows_have_zero_ids_and_lengths():
    df = df_ohlc_from_close([1, 1, 2, 2, 2])
    out = movement_direction(df)
    flat = out["Direction"] == "FLAT"
    assert (out.loc[flat, ["RunID", "RunLength"]] == 0).all().all()

def test_streak_rows_have_positive_ids_and_lengths():
    df = df_ohlc_from_close([1, 2, 3])
    out = movement_direction(df)
    mask = out["Direction"].isin(["UP", "DOWN"])
    assert (out.loc[mask, "RunID"] > 0).all()
    assert (out.loc[mask, "RunLength"] >= 1).all()


# ---------- core behaviour ----------
def test_simple_up_then_down_produces_two_runs():
    df = df_ohlc_from_close([1, 2, 3, 2, 1])
    out = movement_direction(df)
    runs = out[out["Direction"].isin(["UP", "DOWN"])]
    sizes = runs.groupby(["RunID", "Direction"]).size().to_list()
    assert sorted(sizes) == [3, 3]  # UP len 3, DOWN len 3

def test_flats_break_runs():
    df = df_ohlc_from_close([1, 2, 3, 3, 3, 2, 1])
    out = movement_direction(df)
    runs = out[out["Direction"].isin(["UP", "DOWN"])]
    sizes = runs.groupby(["RunID", "Direction"]).size().to_list()
    assert sorted(sizes) == [3, 3]

def test_leading_and_trailing_flats_ignored_in_runs():
    df = df_ohlc_from_close([7, 7, 7, 6, 5, 5])
    out = movement_direction(df)
    runs = out[out["Direction"].isin(["UP", "DOWN"])]
    sizes = runs.groupby(["RunID", "Direction"]).size().to_list()
    assert sizes == [3]  # one DOWN run (6->5->5 counts as DOWN, then FLAT)

def test_single_point_has_no_runs():
    df = df_ohlc_from_close([42])
    out = movement_direction(df)
    assert (out["RunID"] == 0).all()
    assert (out["RunLength"] == 0).all()


# ---------- invariants ----------
def test_runlength_is_1_to_n_inside_each_run():
    df = df_ohlc_from_close([1, 2, 3, 2, 1, 2, 3, 4])
    out = movement_direction(df)
    mask = out["Direction"].isin(["UP", "DOWN"])
    for rid, grp in out.loc[mask].groupby("RunID"):
        expected = np.arange(1, len(grp) + 1)
        assert np.array_equal(grp["RunLength"].to_numpy(), expected), f"RunID {rid} bad sequence"

def test_runlength_max_equals_group_size():
    df = df_ohlc_from_close([1, 2, 3, 2, 1, 2, 3, 4])
    out = movement_direction(df)
    mask = out["Direction"].isin(["UP", "DOWN"])
    sizes = out.loc[mask].groupby("RunID").size()
    maxlen = out.loc[mask, "RunLength"].groupby(out.loc[mask, "RunID"]).max()
    assert sizes.equals(maxlen)

def test_runs_count_equals_number_of_run_starts():
    df = df_ohlc_from_close([1, 2, 1, 2, 1, 1, 2])
    out = movement_direction(df)
    mask = out["Direction"].isin(["UP", "DOWN"])
    run_starts = mask & (out["Direction"] != out["Direction"].shift(1))
    assert run_starts.sum() == out.loc[mask, "RunID"].nunique()


# ---------- summary ----------
def test_run_summary_counts_and_lengths_match_dataframe_groups():
    df = df_ohlc_from_close([1, 2, 3, 2, 1, 2, 3, 4])
    out = movement_direction(df)
    s = run_summary(out)

    runs = out[out["Direction"].isin(["UP", "DOWN"])].groupby(["RunID", "Direction"]).size()
    no_up = (runs.reset_index()["Direction"] == "UP").sum()
    no_dn = (runs.reset_index()["Direction"] == "DOWN").sum()
    assert s["no_up_runs"] == int(no_up)
    assert s["no_down_runs"] == int(no_dn)

    up_len = runs[runs.index.get_level_values("Direction") == "UP"].max() if no_up else 0
    dn_len = runs[runs.index.get_level_values("Direction") == "DOWN"].max() if no_dn else 0
    assert s["longest_up_length"] == int(up_len or 0)
    assert s["longest_down_length"] == int(dn_len or 0)

def test_run_summary_ranges_align_with_index_bounds():
    df = df_ohlc_from_close([1, 2, 3, 2, 1])
    out = movement_direction(df)
    s = run_summary(out)

    # If we have an UP run of length 3, its range should match the first 3-date window
    if s["longest_up_length"] > 0 and s["longest_up_range"] is not None:
        a, b = s["longest_up_range"]
        idx = out[(out["RunID"] > 0) & (out["Direction"] == "UP")].index
        assert a == idx.min() and b == idx.max()
