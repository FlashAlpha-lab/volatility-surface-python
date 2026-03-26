"""
Arbitrage detection Python example — butterfly and calendar arbitrage flags.

Search queries this file targets:
  volatility surface arbitrage detection python
  butterfly arbitrage implied volatility python
  calendar arbitrage options python
  arbitrage-free volatility surface python
  SVI arbitrage python

An arbitrage-free volatility surface must satisfy two conditions:

1. BUTTERFLY ARBITRAGE (within each expiry):
   The second derivative of total variance with respect to log-moneyness
   must be non-negative everywhere:
       d^2 w(k) / dk^2 >= 0   for all k

   A violation implies a negative risk-neutral density, meaning the model
   assigns negative probability to some range of stock prices — a free lunch.

2. CALENDAR ARBITRAGE (across expiries):
   Total variance must be non-decreasing in time for all moneyness levels:
       w(k, T1) <= w(k, T2)   for all k, whenever T1 < T2

   A violation means a longer-dated option is cheaper (in variance terms)
   than a shorter-dated one at the same moneyness, creating a static arbitrage.

The FlashAlpha adv_volatility endpoint detects and reports both types.
"""

import os

from flashalpha import FlashAlpha, TierRestrictedError

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

fa = FlashAlpha(os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY"))

SYMBOL = "SPY"

# ---------------------------------------------------------------------------
# Fetch advanced volatility data (Alpha+ plan required)
# ---------------------------------------------------------------------------

try:
    data = fa.adv_volatility(SYMBOL)
except TierRestrictedError as e:
    print(f"adv_volatility requires {e.required_plan} plan (you have {e.current_plan}).")
    print("Upgrade at https://flashalpha.com")
    raise SystemExit(1)

arb_flags = data.get("arbitrage_flags", [])

# ---------------------------------------------------------------------------
# Separate butterfly and calendar violations
# ---------------------------------------------------------------------------

butterfly_violations = [f for f in arb_flags if f.get("type") == "butterfly"]
calendar_violations  = [f for f in arb_flags if f.get("type") == "calendar"]
all_clean = len(arb_flags) == 0

print(f"\n{'='*70}")
print(f"  Arbitrage Detection  —  {SYMBOL}")
print(f"{'='*70}")
print(f"  Total flags:              {len(arb_flags)}")
print(f"  Butterfly violations:     {len(butterfly_violations)}")
print(f"  Calendar violations:      {len(calendar_violations)}")

if all_clean:
    print()
    print("  Surface is ARBITRAGE-FREE across all checked expiries.")
    print("  Both butterfly and calendar conditions are satisfied.")

# ---------------------------------------------------------------------------
# Butterfly violations
# ---------------------------------------------------------------------------

if butterfly_violations:
    print()
    print(f"{'='*70}")
    print("  Butterfly Arbitrage Violations (within-expiry density violations)")
    print(f"{'='*70}")
    print(f"  {'Expiry':12s}  {'Moneyness k':>13}  {'d^2w/dk^2':>12}  {'Severity':>10}")
    print(f"  {'-'*12}  {'-'*13}  {'-'*12}  {'-'*10}")

    for flag in butterfly_violations:
        expiry    = flag.get("expiry", "")
        moneyness = flag.get("moneyness")
        d2wdk2    = flag.get("d2w_dk2")
        severity  = flag.get("severity", "")

        mk_str  = f"{moneyness:.4f}"  if moneyness  is not None else "N/A"
        d2_str  = f"{d2wdk2:.6f}"    if d2wdk2      is not None else "N/A"

        print(f"  {expiry:12s}  {mk_str:>13}  {d2_str:>12}  {severity:>10}")

    print()
    print("  What this means:")
    print("    A negative d^2w/dk^2 at moneyness k implies the risk-neutral density")
    print("    is negative in that region. This can happen when:")
    print("      - Market data is noisy and the SVI fit is under-constrained")
    print("      - The five-parameter SVI is not expressive enough for that expiry")
    print("      - A quoted option price is stale or crossed (bad data)")
    print("    Arbitrage-free SVI (aSSVI) or a global surface regularizer would fix this.")

# ---------------------------------------------------------------------------
# Calendar violations
# ---------------------------------------------------------------------------

if calendar_violations:
    print()
    print(f"{'='*70}")
    print("  Calendar Arbitrage Violations (across-expiry total variance)")
    print(f"{'='*70}")
    print(
        f"  {'Near Expiry':12s}  {'Far Expiry':12s}  "
        f"{'Moneyness k':>13}  {'Near Var':>10}  {'Far Var':>10}  {'Diff':>10}"
    )
    print(
        f"  {'-'*12}  {'-'*12}  "
        f"{'-'*13}  {'-'*10}  {'-'*10}  {'-'*10}"
    )

    for flag in calendar_violations:
        near_exp  = flag.get("near_expiry", "")
        far_exp   = flag.get("far_expiry", "")
        moneyness = flag.get("moneyness")
        near_var  = flag.get("near_variance")
        far_var   = flag.get("far_variance")

        diff = (far_var - near_var) if (near_var is not None and far_var is not None) else None

        mk_str   = f"{moneyness:.4f}" if moneyness is not None else "N/A"
        nv_str   = f"{near_var:.6f}" if near_var  is not None else "N/A"
        fv_str   = f"{far_var:.6f}"  if far_var   is not None else "N/A"
        diff_str = f"{diff:.6f}"     if diff       is not None else "N/A"

        print(
            f"  {near_exp:12s}  {far_exp:12s}  "
            f"{mk_str:>13}  {nv_str:>10}  {fv_str:>10}  {diff_str:>10}"
        )

    print()
    print("  What this means:")
    print("    Total variance must be non-decreasing in expiry at every moneyness.")
    print("    A violation means: w(k, T_near) > w(k, T_far) — a static arb exists.")
    print("    In practice: sell the expensive near-dated option, buy the cheap far-dated")
    print("    option at the same strike, collect the difference, and it costs nothing.")
    print("    This is extremely rare with live data; it usually signals data errors.")

print()
print("Learn more:")
print("  https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection")
