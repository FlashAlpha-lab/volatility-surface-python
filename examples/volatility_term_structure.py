"""
Volatility term structure Python example — contango, backwardation, slope, dispersion.

Search queries this file targets:
  volatility term structure python
  implied volatility term structure python
  vol term structure contango backwardation python
  VIX term structure python
  volatility curve python

The volatility term structure describes how ATM implied volatility varies
with time to expiry. It is analogous to the yield curve for interest rates.

Common term structure shapes:
  Contango (upward-sloping): Short-dated IV < long-dated IV.
    Normal in calm markets: uncertainty grows with time horizon.

  Backwardation (inverted): Short-dated IV > long-dated IV.
    Observed during stress events, before earnings, or during macro uncertainty.
    Short-dated options are expensive because near-term tail risk is elevated.

  Flat: IV is approximately constant across expiries.
    Transition state — often short-lived.

The slope between near and far expiries is the primary metric. A rapidly
inverting term structure is often a leading indicator of elevated near-term risk.
"""

import os

from flashalpha import FlashAlpha, TierRestrictedError

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

fa = FlashAlpha(os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY"))

# Single-stock names like TSLA often show dramatic term structure events
# around earnings announcements or macro catalysts.
SYMBOL = "TSLA"

# ---------------------------------------------------------------------------
# Fetch volatility data (Growth+ plan required)
# ---------------------------------------------------------------------------

try:
    data = fa.volatility(SYMBOL)
except TierRestrictedError as e:
    print(f"volatility requires {e.required_plan} plan (you have {e.current_plan}).")
    print("Upgrade at https://flashalpha.com")
    raise SystemExit(1)

term_structure = data.get("term_structure", {})
skew_profiles  = data.get("skew_profiles", [])
atm_iv         = data.get("atm_iv")

# ---------------------------------------------------------------------------
# Display term structure
# ---------------------------------------------------------------------------

print(f"\n{'='*70}")
print(f"  Volatility Term Structure  —  {SYMBOL}  (ATM IV: {atm_iv:.1f}%)")
print(f"{'='*70}")

# Term structure summary fields from the API
near_slope  = term_structure.get("near_slope")   # slope between near-term expiries
far_slope   = term_structure.get("far_slope")    # slope between far-term expiries
shape       = term_structure.get("shape")        # "contango", "backwardation", "flat"
iv_dispersion = term_structure.get("iv_dispersion")  # std dev of ATM IVs across expiries

print(f"\n  Shape:          {shape or 'N/A'}")
print(f"  Near slope:     {f'{near_slope:+.2f} vol pts/month' if near_slope is not None else 'N/A'}")
print(f"  Far slope:      {f'{far_slope:+.2f} vol pts/month' if far_slope is not None else 'N/A'}")
print(f"  IV dispersion:  {f'{iv_dispersion:.2f} vol pts' if iv_dispersion is not None else 'N/A'}")
print()

# ---------------------------------------------------------------------------
# Per-expiry ATM IV table (extracted from skew profiles)
# ---------------------------------------------------------------------------

print(f"  {'Expiry':12s}  {'DTE':>5}  {'ATM IV':>9}  {'vs Front':>10}  {'Shape Contribution':>20}")
print(f"  {'-'*12}  {'-'*5}  {'-'*9}  {'-'*10}  {'-'*20}")

front_iv = None
for row in skew_profiles:
    expiry  = row.get("expiry", "")
    dte     = row.get("dte", "")
    iv      = row.get("atm_iv")

    if iv is None:
        continue

    if front_iv is None:
        front_iv = iv

    vs_front = iv - front_iv if front_iv is not None else None

    # Qualitative contribution to the shape
    if vs_front is None:
        contrib = "—  (reference expiry)"
    elif vs_front > 2:
        contrib = "Adds to contango"
    elif vs_front > 0:
        contrib = "Mild upward slope"
    elif vs_front > -2:
        contrib = "Near-flat"
    else:
        contrib = "Inverted / backwardation"

    vs_str = f"{vs_front:+.2f}v" if vs_front is not None else "—"

    print(f"  {expiry:12s}  {str(dte):>5}  {f'{iv:.2f}%':>9}  {vs_str:>10}  {contrib:>20}")

# ---------------------------------------------------------------------------
# Interpretation
# ---------------------------------------------------------------------------

print()
print(f"{'='*70}")
print("  Interpretation")
print(f"{'='*70}")

if shape:
    shape_lower = shape.lower()
    if "backwardation" in shape_lower or "inverted" in shape_lower:
        print(f"\n  Term structure is INVERTED ({shape}).")
        print("  Near-term IV is elevated relative to far-term IV.")
        print("  This is common when:")
        print("    - Earnings or a macro event is imminent")
        print("    - Realized vol has recently spiked and front options are bid")
        print("    - The market is pricing a specific near-term event, not a secular trend")
        print()
        print("  Trading implications:")
        print("    - Calendar spreads (sell near, buy far) may have positive theta while")
        print("      benefiting if the front IV mean-reverts post-event.")
        print("    - Short near-dated straddles may capture the elevated front IV premium.")
    elif "contango" in shape_lower:
        print(f"\n  Term structure is in CONTANGO ({shape}).")
        print("  Far-term IV exceeds near-term IV — the normal state for equity vol.")
        print("  This suggests:")
        print("    - No immediate event is driving short-dated premium higher")
        print("    - The market is pricing growing uncertainty with time horizon")
        print()
        print("  Trading implications:")
        print("    - Front-dated premium selling is attractive on a relative basis.")
        print("    - Reverse calendar spreads (sell far, buy near) may be considered.")

print()
print("Learn more:")
print("  https://flashalpha.com/articles/volatility-term-structure-contango-backwardation-events")
