"""
Realized vs implied volatility Python example — VRP across multiple windows.

Search queries this file targets:
  realized vs implied volatility python
  volatility risk premium python
  VRP options python
  implied volatility vs historical volatility python
  vol risk premium calculation python

Realized volatility (RV) is computed from historical price returns:
  RV = sqrt(252) * std(log(P_t / P_{t-1})) over a trailing window

Implied volatility (IV) is the market's forward-looking expectation
of future realized volatility, embedded in option prices. IV also
includes a risk premium — the additional compensation sellers demand.

Volatility Risk Premium (VRP) = IV - RV (measured in vol points).

A persistently positive VRP means options are overpriced on average,
which is the theoretical basis for systematic premium-selling strategies.
"""

import os

from flashalpha import FlashAlpha, TierRestrictedError

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

fa = FlashAlpha(os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY"))

SYMBOL = "SPY"

# ---------------------------------------------------------------------------
# Fetch volatility data (Growth+ plan required)
# ---------------------------------------------------------------------------

try:
    data = fa.volatility(SYMBOL)
except TierRestrictedError as e:
    print(f"volatility requires {e.required_plan} plan (you have {e.current_plan}).")
    print("Upgrade at https://flashalpha.com")
    raise SystemExit(1)

realized_vol = data.get("realized_vol", {})
iv_rv_spreads = data.get("iv_rv_spreads", {})
atm_iv = data.get("atm_iv")

# ---------------------------------------------------------------------------
# Realized volatility across all windows
# ---------------------------------------------------------------------------

print(f"\n{'='*70}")
print(f"  Realized vs Implied Volatility  —  {SYMBOL}")
print(f"{'='*70}")

# ATM IV is a single number representing the front-month at-the-money IV
print(f"\n  ATM Implied Volatility (front-month):  {atm_iv:.2f}%")
print()

# Realized vol is available for multiple lookback windows.
# Comparing IV to each window shows which lookback is most representative.
rv_windows = [
    ("rv_5d",  "5-day RV",  iv_rv_spreads.get("spread_5d")),
    ("rv_10d", "10-day RV", iv_rv_spreads.get("spread_10d")),
    ("rv_20d", "20-day RV", iv_rv_spreads.get("spread_20d")),
    ("rv_30d", "30-day RV", iv_rv_spreads.get("spread_30d")),
    ("rv_60d", "60-day RV", iv_rv_spreads.get("spread_60d")),
]

print(f"  {'Window':12s}  {'RV (%)':>9}  {'IV (%)':>9}  {'VRP (vol pts)':>14}  {'Signal':>20}")
print(f"  {'-'*12}  {'-'*9}  {'-'*9}  {'-'*14}  {'-'*20}")

for key, label, spread in rv_windows:
    rv_val = realized_vol.get(key)
    if rv_val is None:
        continue

    # VRP = IV - RV (positive = options are rich)
    vrp = spread if spread is not None else (atm_iv - rv_val if atm_iv else None)

    # Qualitative signal
    if vrp is None:
        signal = "N/A"
    elif vrp > 4:
        signal = "Options expensive (sell)"
    elif vrp > 1:
        signal = "Mildly rich"
    elif vrp > -1:
        signal = "Fairly priced"
    else:
        signal = "Options cheap (buy)"

    vrp_str = f"{vrp:+.2f}" if vrp is not None else "N/A"
    iv_str  = f"{atm_iv:.2f}" if atm_iv else "N/A"

    print(f"  {label:12s}  {rv_val:>9.2f}  {iv_str:>9}  {vrp_str:>14}  {signal:>20}")

# ---------------------------------------------------------------------------
# Overall assessment from the API
# ---------------------------------------------------------------------------

print()
assessment = iv_rv_spreads.get("assessment", "")
if assessment:
    print(f"  API Assessment: {assessment}")

# ---------------------------------------------------------------------------
# Interpretation guide
# ---------------------------------------------------------------------------

print()
print(f"{'='*70}")
print("  Interpretation Guide")
print(f"{'='*70}")
print()
print("  Choosing the right RV window to compare against IV:")
print("    - 30-day IV => compare with 30-day RV (matching horizons)")
print("    - Short-dated options (5-10 DTE) => compare with 5d or 10d RV")
print("    - For VIX (30-day ATM IV) => canonical comparison is 30d RV")
print()
print("  What the VRP signal means for traders:")
print("    High VRP (IV >> RV):  Sell premium: covered calls, cash-secured puts,")
print("                          short straddles, short iron condors.")
print("    Near zero VRP:        Market is efficiently pricing realized vol.")
print("                          Use defined-risk spreads if selling.")
print("    Negative VRP (RV > IV): Realized vol is outpacing expectations.")
print("                          Buying protection or long gamma may be favored.")
print()
print("  Important caveats:")
print("    - VRP is measured ex-post; future RV is unknown at trade entry.")
print("    - IV incorporates a forward-looking skew; RV is symmetric.")
print("    - The VRP varies by expiry, moneyness, and market regime.")
print()
print("Learn more:")
print("  https://flashalpha.com/articles/realized-vs-implied-volatility-risk-premium")
