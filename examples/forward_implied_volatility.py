"""
Forward implied volatility Python example — forward prices, basis, cost of carry.

Search queries this file targets:
  forward implied volatility python
  implied forward price options python
  cost of carry options python
  forward price basis python
  options forward price calculation python

The forward price F(T) is the fair price today for delivery of the underlying
at time T in the future. Under no-arbitrage:

    F(T) = S * exp((r - q) * T)

where:
  S = current spot price
  r = risk-free interest rate
  q = continuous dividend yield
  T = time to expiry in years

In practice, the implied forward is backed out from the options market
using put-call parity:
    C(K) - P(K) = (F - K) * exp(-r*T)

At a given strike K, solving for F gives the market-implied forward price.

Why it matters:
  - The forward is the reference for log-moneyness k = log(K/F)
  - If we use spot instead of forward, we mismeasure moneyness (especially for
    high-dividend stocks or in high-rate environments)
  - The basis (F/S - 1) reflects the net cost of carry: rates minus dividends
"""

import math
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

svi_params = data.get("svi_parameters", [])

# Also get spot price for basis calculation
spot = None
try:
    quote = fa.stock_quote(SYMBOL)
    spot  = quote.get("mid") or quote.get("lastPrice")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Display forward prices and basis
# ---------------------------------------------------------------------------

print(f"\n{'='*75}")
print(f"  Implied Forward Prices  —  {SYMBOL}")
if spot:
    print(f"  Spot price: {spot:.2f}")
print(f"{'='*75}")
print(
    f"  {'Expiry':12s}  {'DTE':>5}  {'T (yrs)':>8}  "
    f"{'Forward':>10}  {'Basis %':>9}  {'Implied r-q':>12}"
)
print(
    f"  {'-'*12}  {'-'*5}  {'-'*8}  "
    f"{'-'*10}  {'-'*9}  {'-'*12}"
)

for row in svi_params:
    expiry  = row.get("expiry", "")
    dte     = row.get("dte")
    forward = row.get("forward_price")

    if dte is None or forward is None:
        continue

    T = dte / 365.0

    # Basis = (F/S - 1) * 100%
    basis_pct = None
    implied_carry = None
    if spot and spot > 0 and T > 0:
        basis_pct     = (forward / spot - 1) * 100
        # F = S * exp((r-q)*T)  =>  r-q = ln(F/S) / T
        implied_carry = math.log(forward / spot) / T * 100  # in percent

    basis_str = f"{basis_pct:+.3f}%" if basis_pct is not None else "N/A"
    carry_str = f"{implied_carry:+.3f}%" if implied_carry is not None else "N/A"

    print(
        f"  {expiry:12s}  {str(dte):>5}  {T:>8.4f}  "
        f"  {forward:>8.2f}  {basis_str:>9}  {carry_str:>12}"
    )

# ---------------------------------------------------------------------------
# Explanation of forward-spot relationship
# ---------------------------------------------------------------------------

print()
print(f"{'='*75}")
print("  Understanding Forward Prices")
print(f"{'='*75}")
print()
print("  Forward price = Spot * exp((r - q) * T)")
print()
print("  Where r = risk-free rate, q = dividend yield, T = time in years.")
print()
print("  Positive basis (F > S):  r > q  — rates exceed dividend yield (normal today)")
print("    The forward is above spot because you earn interest but forgo dividends.")
print("    Cost of carry is positive.")
print()
print("  Negative basis (F < S):  q > r  — dividend yield exceeds risk-free rate")
print("    More common in high-yield stocks or low-rate environments.")
print("    Cost of carry is negative.")
print()
print("  Why the forward price matters for implied volatility:")
print("    - Log-moneyness k = log(K/F) is defined relative to the FORWARD, not spot")
print("    - If you use spot instead of forward, ATM is shifted, biasing skew estimates")
print("    - SVI parameters from the FlashAlpha API are calibrated using the")
print("      market-implied forward for each expiry, ensuring correct moneyness alignment")
print()
print("  Cost of carry and dividends:")
print("    - SPY pays a quarterly dividend — this reduces the forward below a no-dividend")
print("      equivalent, creating a negative basis near dividend dates.")
print("    - High-rate environments (r >> q) push the forward above spot, making")
print("      call options relatively more expensive than puts on a delta-adjusted basis.")
print()
print("Learn more:")
print("  https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection")
