"""
SVI calibration Python example — raw SVI parameters per expiry.

Search queries this file targets:
  SVI calibration python
  stochastic volatility inspired python
  SVI model parameters options python
  fit implied volatility smile python
  Gatheral SVI python

The SVI (Stochastic Volatility Inspired) model parameterizes the total
implied variance smile at a single expiry with five parameters:

    w(k) = a + b * ( rho*(k - m) + sqrt((k - m)^2 + sigma^2) )

where k = log(K/F) is the log-moneyness (log of strike over forward price).

Parameters:
  a     — overall variance level (shifts the entire smile up or down)
  b     — slope / "wing" magnitude (how steeply variance rises away from ATM)
  rho   — correlation / skew tilt (negative = left-skewed, i.e. put skew)
  m     — horizontal shift (moves the smile left or right along the k axis)
  sigma — minimum variance smoothness (rounds the ATM vertex; larger = rounder)

The FlashAlpha adv_volatility endpoint returns calibrated SVI parameters
for each available expiry, fitted to live market option prices.
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

# ---------------------------------------------------------------------------
# Display raw SVI parameters
# ---------------------------------------------------------------------------

print(f"\n{'='*80}")
print(f"  SVI Calibration Results  —  {SYMBOL}")
print(f"{'='*80}")
print(
    f"  {'Expiry':12s}  {'DTE':>5}  {'a':>8}  {'b':>8}  "
    f"{'rho':>8}  {'m':>8}  {'sigma':>8}  {'ATM Var':>9}  {'ATM IV':>8}"
)
print(f"  {'-'*12}  {'-'*5}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*9}  {'-'*8}")

for row in svi_params:
    expiry  = row.get("expiry", "")
    dte     = row.get("dte", "")
    a       = row.get("a")
    b       = row.get("b")
    rho     = row.get("rho")
    m       = row.get("m")
    sigma   = row.get("sigma")
    atm_var = row.get("atm_total_variance")
    atm_iv  = row.get("atm_iv")

    def fmt(v, decimals=4):
        return f"{v:.{decimals}f}" if v is not None else "N/A"

    print(
        f"  {expiry:12s}  {str(dte):>5}  {fmt(a):>8}  {fmt(b):>8}  "
        f"{fmt(rho):>8}  {fmt(m):>8}  {fmt(sigma):>8}  "
        f"{fmt(atm_var):>9}  {fmt(atm_iv, 2):>8}"
    )

# ---------------------------------------------------------------------------
# Evaluate the SVI smile analytically for one expiry
# ---------------------------------------------------------------------------
# Given SVI parameters we can compute IV at any log-moneyness k without
# calling the API — useful for plotting or interpolation.

print()
print(f"{'='*80}")
print("  SVI Smile Evaluation — First Expiry")
print(f"{'='*80}")

if svi_params:
    row   = svi_params[0]
    expiry = row.get("expiry", "")
    a, b, rho, m, sigma = row.get("a"), row.get("b"), row.get("rho"), row.get("m"), row.get("sigma")
    dte   = row.get("dte")
    fwd   = row.get("forward_price")

    if all(v is not None for v in [a, b, rho, m, sigma, dte]) and dte > 0:
        T = dte / 365.0  # time to expiry in years

        print(f"  Expiry: {expiry}  (DTE={dte}, T={T:.4f}y)")
        print(f"  Parameters: a={a:.4f}, b={b:.4f}, rho={rho:.4f}, m={m:.4f}, sigma={sigma:.4f}")
        if fwd:
            print(f"  Forward price: {fwd:.2f}")
        print()
        print(f"  {'Log-moneyness k':>18}  {'Total Var w(k)':>15}  {'IV (%)':>10}  {'Strike':>10}")
        print(f"  {'-'*18}  {'-'*15}  {'-'*10}  {'-'*10}")

        k_values = [-0.20, -0.15, -0.10, -0.05, 0.00, 0.05, 0.10, 0.15, 0.20]
        for k in k_values:
            # SVI formula: w(k) = a + b*(rho*(k-m) + sqrt((k-m)^2 + sigma^2))
            diff = k - m
            w_k  = a + b * (rho * diff + math.sqrt(diff ** 2 + sigma ** 2))
            w_k  = max(w_k, 0.0)  # total variance must be non-negative
            iv_k = math.sqrt(w_k / T) * 100  # annualized IV in percent

            # Approximate strike from log-moneyness and forward
            strike_str = f"{fwd * math.exp(k):.2f}" if fwd else "N/A"

            print(f"  {k:>18.2f}  {w_k:>15.6f}  {iv_k:>10.2f}  {strike_str:>10}")

print()
print("Interpretation:")
print("  - Negative rho: put side (k < 0) has higher IV than call side — typical equity skew.")
print("  - Large b: wings are steep — the market prices tail events heavily.")
print("  - Small sigma: sharp ATM vertex — IV rises quickly as you move off ATM.")
print("  - m < 0: the minimum variance point is in the put wing.")
print()
print("Learn more:")
print("  https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection")
