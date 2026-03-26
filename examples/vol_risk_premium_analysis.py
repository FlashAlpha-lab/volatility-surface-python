"""
Volatility risk premium analysis Python example — deep-dive VRP across all windows.

Search queries this file targets:
  vol risk premium python
  volatility risk premium analysis python
  VRP options trading python
  sell premium options python
  IV minus RV python

The Volatility Risk Premium (VRP) is the average excess of implied volatility
over subsequent realized volatility. It compensates options sellers for bearing
the risk of large unexpected moves.

    VRP = IV - RV (ex-post, after the fact)
    Expected VRP = IV - E[RV] (ex-ante, forward-looking)

Historically the VRP has been positive on average (~2-4 vol points for SPY),
meaning options sellers have been systematically compensated. This is the
statistical basis for premium-selling strategies.

However, VRP is not constant:
  - It expands during quiet markets (IV stays elevated, RV is low)
  - It compresses or inverts during stress (RV spikes beyond IV)
  - It varies by moneyness (the skew encodes a larger crash premium)
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

realized_vol  = data.get("realized_vol", {})
iv_rv_spreads = data.get("iv_rv_spreads", {})
atm_iv        = data.get("atm_iv")
iv_rank       = data.get("iv_rank")

# ---------------------------------------------------------------------------
# VRP across all windows
# ---------------------------------------------------------------------------

print(f"\n{'='*75}")
print(f"  Volatility Risk Premium Analysis  —  {SYMBOL}")
print(f"{'='*75}")
print(f"\n  ATM Implied Volatility: {atm_iv:.2f}%")
if iv_rank is not None:
    print(f"  IV Rank (0-100):        {iv_rank:.0f}")
print()

windows = [
    ("rv_5d",   "spread_5d",   " 5-day"),
    ("rv_10d",  "spread_10d",  "10-day"),
    ("rv_20d",  "spread_20d",  "20-day"),
    ("rv_30d",  "spread_30d",  "30-day"),
    ("rv_60d",  "spread_60d",  "60-day"),
]

print(f"  {'Window':8s}  {'RV (%)':>9}  {'ATM IV (%)':>11}  {'VRP (v pts)':>12}  {'Edge':>30}")
print(f"  {'-'*8}  {'-'*9}  {'-'*11}  {'-'*12}  {'-'*30}")

vrp_values = []
for rv_key, spread_key, label in windows:
    rv_val  = realized_vol.get(rv_key)
    spread  = iv_rv_spreads.get(spread_key)

    if rv_val is None:
        continue

    vrp = spread if spread is not None else (atm_iv - rv_val if atm_iv else None)

    if vrp is not None:
        vrp_values.append(vrp)

    # Characterize the edge based on VRP magnitude
    if vrp is None:
        edge = "N/A"
    elif vrp > 5:
        edge = "Strong seller edge (options very rich)"
    elif vrp > 2:
        edge = "Moderate seller edge"
    elif vrp > 0:
        edge = "Mild seller edge"
    elif vrp > -2:
        edge = "Neutral / options fairly priced"
    else:
        edge = "Buyer edge (realized > implied)"

    iv_str  = f"{atm_iv:.2f}" if atm_iv else "N/A"
    rv_str  = f"{rv_val:.2f}"
    vrp_str = f"{vrp:+.2f}" if vrp is not None else "N/A"

    print(f"  {label:8s}  {rv_str:>9}  {iv_str:>11}  {vrp_str:>12}  {edge:>30}")

# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

print()
print(f"{'='*75}")
print("  VRP Summary Statistics")
print(f"{'='*75}")

if vrp_values:
    avg_vrp = sum(vrp_values) / len(vrp_values)
    min_vrp = min(vrp_values)
    max_vrp = max(vrp_values)

    print(f"\n  Average VRP across all windows:  {avg_vrp:+.2f} vol points")
    print(f"  Min VRP (shortest window):       {min_vrp:+.2f} vol points")
    print(f"  Max VRP (longest window):        {max_vrp:+.2f} vol points")

overall_assessment = iv_rv_spreads.get("assessment", "")
if overall_assessment:
    print(f"\n  API Assessment: {overall_assessment}")

# ---------------------------------------------------------------------------
# Strategy implications
# ---------------------------------------------------------------------------

print()
print(f"{'='*75}")
print("  Strategy Implications")
print(f"{'='*75}")
print()

avg_vrp_val = sum(vrp_values) / len(vrp_values) if vrp_values else None

if avg_vrp_val is None:
    print("  Insufficient data.")
elif avg_vrp_val > 3:
    print("  HIGH VRP REGIME — Premium sellers have a historical statistical edge.")
    print()
    print("  Candidate strategies (all defined risk preferred for retail):")
    print("    - Short iron condor (defined-risk short strangle)")
    print("    - Cash-secured put (sell put at desired entry price)")
    print("    - Covered call (sell call against existing long position)")
    print("    - Short calendar spread (sell far IV, buy near IV)")
    print()
    print("  Risk management:")
    print("    - Size for maximum 1-2% portfolio loss per position")
    print("    - Set exit rules at 2x or 3x premium received")
    print("    - Monitor IV rank — if VRP compresses, close early")
elif avg_vrp_val > 0:
    print("  MILD VRP REGIME — Some edge to selling premium, but conditions are average.")
    print()
    print("  Candidate strategies:")
    print("    - Defined-risk spreads (vertical, iron condor) rather than naked premium")
    print("    - Wheel strategy (CSP -> covered call) at support/resistance levels")
elif avg_vrp_val > -2:
    print("  NEUTRAL — IV and RV are roughly matched. Options are fairly priced.")
    print()
    print("  Candidate strategies:")
    print("    - Avoid heavy premium selling; favor defined-risk spreads")
    print("    - Consider butterfly or calendar spreads with limited vega exposure")
else:
    print("  NEGATIVE VRP — Realized vol is exceeding implied vol.")
    print()
    print("  Candidate strategies:")
    print("    - Long premium: long straddles, long strangles, long calls/puts")
    print("    - Tail protection: buy OTM puts as portfolio hedge")
    print("    - Reduce or close existing short premium positions")

print()
print("Learn more:")
print("  https://flashalpha.com/articles/realized-vs-implied-volatility-risk-premium")
