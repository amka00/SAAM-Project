"""
05_data_cleaning_pipeline.py
-----------------------------
Professional data cleaning pipeline for Pacific-region portfolio construction.
Extends 01_cleaning.py and replaces the ad-hoc logic in 02_analysis.py.

Pipeline steps:
  1.  load_data()                  - load all processed CSVs
  2.  remove_invalid_firms()       - drop all-NaN ISINs from every dataset
  3.  handle_low_prices()          - prices < 0.5  ->  NaN
  4.  handle_missing_values()      - beginning: keep | middle: ffill | trailing: 0 (delisting)
  5.  compute_returns()            - simple returns, safe div, delisting = -100%
  6.  detect_stale_firms()         - rolling 120-month zero-return ratio > 50%
  7.  build_investment_universe()  - history + stale + carbon filters per year
  8.  run_pipeline()               - orchestrates all steps, saves outputs
"""

import os
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
MIN_PRICE        = 0.5   # Prices below this threshold are treated as invalid
MIN_HISTORY      = 36    # Minimum months of return history to be investable
STALE_WINDOW     = 120   # Rolling window for stale detection (10 years)
STALE_THRESHOLD  = 0.50  # Max fraction of zero-return months allowed

PATHS = {
    "universe"  : "data/processed/Pacific_Universe.csv",
    "prices"    : "data/processed/Clean_Prices_Pacific.csv",
    "revenues"  : "data/processed/Clean_Revenues_Pacific.csv",
    "co2_scope1": "data/processed/Clean_CO2_Scope1_Pacific.csv",
    "co2_scope2": "data/processed/Clean_CO2_Scope2_Pacific.csv",
}


# ---------------------------------------------------------------------------
# STEP 1 - DATA LOADING
# ---------------------------------------------------------------------------
def load_data():
    """
    Load all processed datasets.

    Convention used throughout this pipeline:
      - Prices / Returns  : rows = dates (DatetimeIndex),  columns = ISINs
      - Annual data       : rows = ISINs,                  columns = integer years

    Returns
    -------
    prices    : DataFrame (dates x ISINs)
    revenues  : DataFrame (ISINs x years)
    co2_s1    : DataFrame (ISINs x years)   - Scope 1 emissions
    co2_s2    : DataFrame (ISINs x years)   - Scope 2 emissions
    """
    for key, path in PATHS.items():
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Missing file: {path}. "
                "Run 01_cleaning.py and 04_carbon_emission_check.py first."
            )

    # Monthly prices: transpose so dates are the row axis
    prices_raw = pd.read_csv(PATHS["prices"])
    prices = (
        prices_raw
        .set_index("ISIN")
        .drop(columns=["NAME"], errors="ignore")
        .T
        .rename_axis("date")
    )
    prices.index = pd.to_datetime(prices.index)
    prices = prices.sort_index()
    prices = prices.apply(pd.to_numeric, errors="coerce")

    # Annual revenues
    rev_raw  = pd.read_csv(PATHS["revenues"])
    revenues = rev_raw.set_index("ISIN").drop(columns=["NAME"], errors="ignore")
    revenues.columns = revenues.columns.astype(int)

    # Annual carbon emissions
    def _load_annual(path):
        df = pd.read_csv(path)
        df = df.set_index("ISIN").drop(columns=["NAME"], errors="ignore")
        df.columns = df.columns.astype(int)
        return df.apply(pd.to_numeric, errors="coerce")

    co2_s1 = _load_annual(PATHS["co2_scope1"])
    co2_s2 = _load_annual(PATHS["co2_scope2"])

    print(
        f"[load_data] prices: {prices.shape}  |  "
        f"revenues: {revenues.shape}  |  "
        f"CO2 S1: {co2_s1.shape}  |  CO2 S2: {co2_s2.shape}"
    )
    return prices, revenues, co2_s1, co2_s2


# ---------------------------------------------------------------------------
# STEP 2 - REMOVE INVALID FIRMS
# ---------------------------------------------------------------------------
def remove_invalid_firms(prices, revenues, co2_s1, co2_s2):
    """
    Remove ISINs that have absolutely no price data (entire column is NaN).
    The same set of ISINs is dropped from all datasets to keep them consistent.
    """
    all_nan_mask  = prices.isna().all(axis=0)
    invalid_isins = prices.columns[all_nan_mask].tolist()

    if invalid_isins:
        print(f"[remove_invalid_firms] Dropping {len(invalid_isins)} firms with zero price observations.")
        prices   = prices.drop(columns=invalid_isins)
        revenues = revenues.drop(index=invalid_isins, errors="ignore")
        co2_s1   = co2_s1.drop(index=invalid_isins,  errors="ignore")
        co2_s2   = co2_s2.drop(index=invalid_isins,  errors="ignore")
    else:
        print("[remove_invalid_firms] No fully-empty firms found.")

    return prices, revenues, co2_s1, co2_s2, invalid_isins


# ---------------------------------------------------------------------------
# STEP 3 - HANDLE LOW / INVALID PRICES
# ---------------------------------------------------------------------------
def handle_low_prices(prices):
    """
    Replace prices strictly below MIN_PRICE (0.5) with NaN.
    Near-zero prices create artificially extreme returns.
    Fully vectorized (single boolean mask).
    """
    low_mask   = prices < MIN_PRICE
    n_replaced = int(low_mask.sum().sum())
    prices     = prices.where(~low_mask, other=np.nan)
    print(f"[handle_low_prices] {n_replaced} observations (< {MIN_PRICE}) replaced with NaN.")
    return prices


# ---------------------------------------------------------------------------
# STEP 4 - HANDLE MISSING VALUES
# ---------------------------------------------------------------------------
def handle_missing_values(prices):
    """
    Three strategies depending on where NaN sits in each column:

    A) Leading NaN   -> keep as NaN  (firm not yet listed)
    B) Middle NaN    -> forward-fill (temporary data gap)
    C) Trailing NaN  -> set to 0.0  (delisted; next return = -100%)

    Algorithm (fully vectorized):
      1. Identify trailing NaN via reverse cumsum:
         trailing[t] = isna[t] AND cumsum_from_bottom[t] == 0
      2. Forward-fill (handles middle NaN, leaves leading NaN intact).
      3. Override trailing positions with 0.0.
    """
    # Step 1 - identify trailing NaN
    non_nan_int    = prices.notna().astype(np.int8)
    cum_from_below = non_nan_int.iloc[::-1].cumsum(axis=0).iloc[::-1]
    trailing_mask  = prices.isna() & (cum_from_below == 0)

    n_trailing = int(trailing_mask.sum().sum())
    n_total_na = int(prices.isna().sum().sum())

    # Step 2 - forward-fill (middle NaN only; leading NaN stay NaN)
    filled = prices.ffill(axis=0)

    # Step 3 - mark delisting
    filled[trailing_mask] = 0.0

    print(
        f"[handle_missing_values] Total NaN before: {n_total_na} | "
        f"Trailing -> 0 (delisting): {n_trailing} | Middle -> ffill | Leading -> kept"
    )
    return filled


# ---------------------------------------------------------------------------
# STEP 5 - COMPUTE RETURNS
# ---------------------------------------------------------------------------
def compute_returns(prices):
    """
    Simple monthly returns: R_t = (P_t / P_{t-1}) - 1

    - P_{t-1} == 0           -> NaN  (division-by-zero guard)
    - P_t == 0, P_{t-1} > 0 -> exactly -1.0  (-100% delisting)
    - Inf / -Inf             -> NaN  (safety net)
    """
    prev_prices = prices.shift(1)
    safe_prev   = prev_prices.replace(0.0, np.nan)
    returns     = (prices / safe_prev) - 1.0

    delisting_mask          = (prices == 0.0) & (prev_prices > 0.0)
    returns[delisting_mask] = -1.0

    returns = returns.replace([np.inf, -np.inf], np.nan)

    print(
        f"[compute_returns] Shape: {returns.shape} | "
        f"NaN ratio: {returns.isna().mean().mean():.2%} | "
        f"Delisting events: {int(delisting_mask.sum().sum())}"
    )
    return returns


# ---------------------------------------------------------------------------
# STEP 6 - DETECT STALE PRICES
# ---------------------------------------------------------------------------
def detect_stale_firms(returns):
    """
    Flag firms with >50% zero returns in any rolling 120-month window.
    Zero returns = price unchanged = stale / illiquid data.
    Fully vectorized via pandas rolling().

    Returns
    -------
    stale_flags : Series[bool] indexed by ISIN
    stale_ratio : DataFrame (dates x ISINs) - rolling ratio for inspection
    """
    is_zero = (returns == 0.0).astype(np.float32)

    rolling_zeros = is_zero.rolling(window=STALE_WINDOW, min_periods=1).sum()
    rolling_obs   = (
        returns.notna().astype(np.float32)
               .rolling(window=STALE_WINDOW, min_periods=1).sum()
    )

    stale_ratio = rolling_zeros / rolling_obs.replace(0.0, np.nan)
    stale_flags = (stale_ratio > STALE_THRESHOLD).any()

    print(
        f"[detect_stale_firms] {int(stale_flags.sum())} / {len(stale_flags)} firms "
        f"flagged as stale (zero-return ratio > {STALE_THRESHOLD:.0%})."
    )
    return stale_flags, stale_ratio


# ---------------------------------------------------------------------------
# STEP 7 - BUILD INVESTMENT UNIVERSE
# ---------------------------------------------------------------------------
def build_investment_universe(
    returns, co2_s1, co2_s2, stale_flags,
    start_year=2004, end_year=2013
):
    """
    Per year Y, keep firms that satisfy ALL three criteria:
      1. >= 36 months of return history up to end of year Y
      2. Not flagged as stale
      3. Non-NaN Scope-1 or Scope-2 carbon data for year Y

    Rules 1-3 are vectorized. Exclusion log loops only over excluded firms.

    Returns
    -------
    universe_per_year : dict { year: [ISIN, ...] }
    excluded_log      : DataFrame [ISIN, year, reason]
    """
    universe_per_year = {}
    exclusion_records = []

    stale = stale_flags.reindex(returns.columns, fill_value=False)

    for year in range(start_year, end_year + 1):
        year_end   = pd.Timestamp(f"{year}-12-31")
        ret_window = returns.loc[:year_end]

        # Rule 1: sufficient history
        obs_count      = ret_window.count()
        enough_history = obs_count >= MIN_HISTORY

        # Rule 2: not stale
        not_stale = ~stale

        # Rule 3: carbon data available
        has_co2 = pd.Series(False, index=returns.columns)
        for co2_df in (co2_s1, co2_s2):
            if year in co2_df.columns:
                has_co2 = has_co2 | co2_df[year].reindex(returns.columns).notna()

        valid_mask              = enough_history & not_stale & has_co2
        universe_per_year[year] = returns.columns[valid_mask].tolist()

        # Build exclusion log
        for isin in returns.columns[~valid_mask]:
            reasons = []
            if not enough_history[isin]:
                reasons.append(f"insufficient_history({int(obs_count[isin])}mo)")
            if stale[isin]:
                reasons.append("stale_prices")
            if not has_co2[isin]:
                reasons.append("no_carbon_data")
            exclusion_records.append({"ISIN": isin, "year": year, "reason": " | ".join(reasons)})

        print(
            f"  {year}: {int(valid_mask.sum()):>3} valid  |  "
            f"{int((~valid_mask).sum()):>3} excluded  "
            f"[history: {int((~enough_history).sum())}  "
            f"stale: {int((~not_stale).sum())}  "
            f"no_CO2: {int((~has_co2).sum())}]"
        )

    return universe_per_year, pd.DataFrame(exclusion_records, columns=["ISIN", "year", "reason"])


# ---------------------------------------------------------------------------
# STEP 8 - MAIN PIPELINE ORCHESTRATOR
# ---------------------------------------------------------------------------
def run_pipeline(start_year=2004, end_year=2013):
    """
    Run the full cleaning pipeline end-to-end and save outputs.

    Returns
    -------
    clean_prices      : DataFrame (dates x ISINs)
    clean_returns     : DataFrame (dates x ISINs)
    universe_per_year : dict { year: [ISIN, ...] }
    excluded_log      : DataFrame [ISIN, year, reason]
    """
    sep = "=" * 64

    print(f"\n{sep}\nSTEP 1 - Load data\n{sep}")
    prices, revenues, co2_s1, co2_s2 = load_data()

    print(f"\n{sep}\nSTEP 2 - Remove invalid firms\n{sep}")
    prices, revenues, co2_s1, co2_s2, invalid_isins = remove_invalid_firms(
        prices, revenues, co2_s1, co2_s2
    )

    print(f"\n{sep}\nSTEP 3 - Handle low / invalid prices\n{sep}")
    prices = handle_low_prices(prices)

    print(f"\n{sep}\nSTEP 4 - Handle missing values\n{sep}")
    prices = handle_missing_values(prices)

    print(f"\n{sep}\nSTEP 5 - Compute returns\n{sep}")
    returns = compute_returns(prices)

    print(f"\n{sep}\nSTEP 6 - Detect stale firms\n{sep}")
    stale_flags, _ = detect_stale_firms(returns)

    print(f"\n{sep}\nSTEP 7 - Build investment universe ({start_year}-{end_year})\n{sep}")
    universe_per_year, excluded_log = build_investment_universe(
        returns, co2_s1, co2_s2, stale_flags,
        start_year=start_year, end_year=end_year,
    )

    os.makedirs("data/processed", exist_ok=True)
    excluded_log.to_csv("data/processed/excluded_firms_log.csv", index=False)
    print(f"\nExclusion log  -> data/processed/excluded_firms_log.csv")

    for year, isins in universe_per_year.items():
        if isins:
            year_end = pd.Timestamp(f"{year}-12-31")
            returns.loc[:year_end, isins].to_csv(f"data/processed/returns_{year}.csv")
    print(f"Returns files  -> data/processed/returns_<year>.csv")

    print(f"\n{sep}\nPIPELINE COMPLETE - Summary\n{sep}")
    print(f"  Firms loaded            : {prices.shape[1] + len(invalid_isins)}")
    print(f"  Firms removed (no data) : {len(invalid_isins)}")
    print(f"  Firms stale             : {int(stale_flags.sum())}")
    print()
    for year, isins in universe_per_year.items():
        print(f"  {year}  ->  {len(isins):>3} investable firms")

    return prices, returns, universe_per_year, excluded_log


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    clean_prices, clean_returns, universe_per_year, excluded_log = run_pipeline()
