"""
Variance swap pricing Python example — fair variance, fair vol, convexity adjustment.

Search queries this file targets:
  variance swap python
  variance swap fair value python
  variance swap pricing options python
  variance swap convexity adjustment python
  VIX replication python

A variance swap is a forward contract on realized variance. At inception the
two sides agree on a "fair variance strike" K_var such that the contract has
zero value. At expiry, the payoff is:

    Payoff = (sigma_R^2 - K_var) * Notional

where sigma_R^2 is the annualized realized variance over the life of the contract.

The fair variance can be replicated by a portfolio of OTM options across all
strikes. This is exactly the logic behind the VIX index:

    K_var = (2/T) * [ SUM_puts P(K_i) / K_i^2 * dK  +  SUM_calls C(K_i) / K_i^2 * dK ]

Because fair variance is a convex combination of squared IVs, it always exceeds
the square of ATM IV when the smile has non-zero curvature. The difference is:

    Convexity adjustment = fair_vol - ATM_IV

The larger the wings (curvature), the bigger the convexity adjustment.
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

var_swaps = data.get("variance_swap_fair_values", [])
svi_lookup = {r["expiry"]: r for r in data.get("svi_parameters", [])}

# ---------------------------------------------------------------------------
# Display variance swap fair values
# ---------------------------------------------------------------------------

print(f"\n{'='*80}")
print(f"  Variance Swap Fair Values  —  {SYMBOL}")
print(f"{'='*80}")
print(
    f"  {'Expiry':12s}  {'DTE':>5}  {'Fair Var':>10}  {'Fair Vol':>10}  "
    f"{'ATM IV':>8}  {'Conv Adj':>10}  {'Conv Adj %':>12}"
)
print(
    f"  {'-'*12}  {'-'*5}  {'-'*10}  {'-'*10}  "
    f"{'-'*8}  {'-'*10}  {'-'*12}"
)

for row in var_swaps:
    expiry      = row.get("expiry", "")
    dte         = row.get("dte", "")
    fair_var    = row.get("fair_variance")
    fair_vol    = row.get("fair_vol")
    conv_adj    = row.get("convexity_adjustment")

    # ATM IV from SVI params for cross-reference
    svi = svi_lookup.get(expiry, {})
    atm_iv = svi.get("atm_iv") or row.get("atm_iv")

    def fmt(v, decimals=2):
        return f"{v:.{decimals}f}" if v is not None else "N/A"

    # Convexity adjustment as a percentage of ATM IV
    conv_pct = ""
    if conv_adj is not None and atm_iv and atm_iv > 0:
        conv_pct = f"{(conv_adj / atm_iv * 100):.2f}%"

    print(
        f"  {expiry:12s}  {str(dte):>5}  {fmt(fair_var, 4):>10}  "
        f"{fmt(fair_vol):>9}%  {fmt(atm_iv):>7}%  "
        f"{fmt(conv_adj):>9}v  {conv_pct:>12}"
    )

# ---------------------------------------------------------------------------
# Summary: what variance swaps tell you
# ---------------------------------------------------------------------------

print()
print(f"{'='*80}")
print("  Summary")
print(f"{'='*80}")

if var_swaps:
    first = var_swaps[0]
    near_expiry    = first.get("expiry", "")
    near_fair_vol  = first.get("fair_vol")
    near_atm_iv    = (svi_lookup.get(near_expiry, {}).get("atm_iv")
                      or first.get("atm_iv"))
    near_conv      = first.get("convexity_adjustment")

    print(f"  Nearest expiry: {near_expiry}")
    if near_fair_vol is not None:
        print(f"  Fair vol (variance swap strike): {near_fair_vol:.2f}%")
    if near_atm_iv is not None:
        print(f"  ATM IV (Black-Scholes at-the-money):  {near_atm_iv:.2f}%")
    if near_conv is not None:
        print(f"  Convexity adjustment: {near_conv:.2f} vol points")
    print()

print("Key points:")
print("  1. Fair vol > ATM IV whenever the smile has non-zero curvature (wings).")
print("  2. The convexity adjustment measures how much you pay for the wings")
print("     relative to the ATM vol when entering a variance swap.")
print("  3. Realized variance is mark-to-market each day using squared log returns.")
print("  4. Variance swaps (unlike vol swaps) have exact static replication via a")
print("     log-contract — no model assumptions beyond no-arbitrage.")
print("  5. A short variance swap is equivalent to selling a replicating portfolio")
print("     of OTM options — it profits when realized vol < fair vol.")
print()
print("Learn more:")
print("  https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection")
