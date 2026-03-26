"""
Implied volatility surface Python example — displaying the total variance surface.

Search queries this file targets:
  implied volatility surface python
  how to get implied volatility surface python
  total variance surface options python
  vol surface moneyness grid python

The implied volatility surface is a 2D grid of IV values indexed by:
  - Moneyness (log-strike / forward): the x-axis, where 0 = ATM
  - Expiry (DTE or calendar date): the y-axis / depth axis

Total variance w(k) = IV(k)^2 * T is the more fundamental quantity because
it removes the sqrt(T) scaling, making comparisons across expiries natural.
"""

import os

from flashalpha import FlashAlpha, TierRestrictedError

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

fa = FlashAlpha(os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY"))

SYMBOL = "SPY"

# ---------------------------------------------------------------------------
# Fetch advanced volatility data
# ---------------------------------------------------------------------------
# adv_volatility requires the Alpha+ plan.
# It returns the calibrated SVI surface, total variance grids, arbitrage flags,
# higher-order greeks surfaces, and variance swap fair values.

try:
    data = fa.adv_volatility(SYMBOL)
except TierRestrictedError as e:
    print(f"adv_volatility requires {e.required_plan} plan (you have {e.current_plan}).")
    print("Upgrade at https://flashalpha.com")
    raise SystemExit(1)

# ---------------------------------------------------------------------------
# Total variance surface
# ---------------------------------------------------------------------------
# The total_variance_surface field contains a grid of w(k, T) values.
# Each row corresponds to one expiry; columns are log-moneyness buckets.

surface = data.get("total_variance_surface", {})

moneyness_grid = surface.get("moneyness", [])   # e.g. [-0.3, -0.2, ..., 0.3]
expiries       = surface.get("expiries", [])     # e.g. ["2026-04-04", "2026-04-18", ...]
rows           = surface.get("rows", [])         # list of lists — one per expiry

print(f"\n{'='*70}")
print(f"  Implied Volatility Surface  —  {SYMBOL}")
print(f"{'='*70}")
print(f"  Expiries:            {len(expiries)}")
print(f"  Moneyness points:    {len(moneyness_grid)}")
print()

# Print the moneyness axis header
if moneyness_grid:
    header = f"{'Expiry':12s}" + "".join(f"{k:7.2f}" for k in moneyness_grid)
    print(header)
    print("-" * len(header))

# Each row in `rows` is a list of total variance values w(k) for that expiry.
# Converting w(k) to IV: IV = sqrt(w(k) / T), where T is DTE/365.
for expiry, row in zip(expiries, rows):
    if not row:
        continue
    # Display as implied vol (%) for readability
    # We approximate T from the surface metadata if available,
    # otherwise display raw total variance.
    row_str = f"{expiry:12s}" + "".join(
        f"{(v * 100):7.2f}" if v is not None else f"{'---':>7}"
        for v in row
    )
    print(row_str)

print()
print("Values shown are total variance w(k) * 100. To convert to IV:")
print("  IV(k, T) = sqrt(w(k, T) / T_years)")
print()

# ---------------------------------------------------------------------------
# SVI-derived IV at ATM (k=0) for each expiry
# ---------------------------------------------------------------------------
# The SVI parameters let us evaluate the smile analytically at any moneyness.
# ATM IV = sqrt(a + b * sigma * sqrt(1 - rho^2)) / sqrt(T)

svi_params = data.get("svi_parameters", [])

print(f"{'='*70}")
print("  ATM Implied Volatility by Expiry (from SVI fit)")
print(f"{'='*70}")
print(f"  {'Expiry':12s}  {'DTE':>5}  {'ATM IV':>9}  {'ATM Var':>10}  {'Forward':>10}")
print(f"  {'-'*12}  {'-'*5}  {'-'*9}  {'-'*10}  {'-'*10}")

for row in svi_params:
    expiry    = row.get("expiry", "")
    dte       = row.get("dte", "")
    atm_iv    = row.get("atm_iv")
    atm_var   = row.get("atm_total_variance")
    forward   = row.get("forward_price")

    iv_str  = f"{atm_iv:.2f}%"  if atm_iv  is not None else "N/A"
    var_str = f"{atm_var:.4f}"  if atm_var is not None else "N/A"
    fwd_str = f"{forward:.2f}"  if forward is not None else "N/A"

    print(f"  {expiry:12s}  {str(dte):>5}  {iv_str:>9}  {var_str:>10}  {fwd_str:>10}")

print()
print("Interpretation:")
print("  - ATM IV rises with DTE in contango (normal term structure).")
print("  - ATM IV falls with DTE in backwardation (stress / event-driven).")
print("  - Forward price > spot implies positive cost of carry (rates - dividends > 0).")
print()
print("Learn more:")
print("  https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection")
