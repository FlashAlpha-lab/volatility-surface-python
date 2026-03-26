"""
Volatility skew analysis Python example — risk reversal, smile ratio, tail convexity.

Search queries this file targets:
  volatility skew python
  implied volatility skew python
  risk reversal volatility python
  put skew options python
  volatility smile python

Volatility skew refers to the asymmetry in implied volatility across strikes
at a single expiry. In equity markets, puts (negative moneyness) carry higher IV
than equivalent calls, producing a negatively skewed smile.

Key skew metrics:
  Risk reversal (25d): IV(25d put) - IV(25d call)
    More negative = steeper downside skew (puts more expensive relative to calls)

  Butterfly (25d): (IV(25d put) + IV(25d call)) / 2 - IV(ATM)
    Measures the curvature of the smile. Large positive butterfly = fat tails.

  Smile ratio: IV(10d put) / IV(ATM)
    How much more expensive deep OTM puts are relative to ATM.

  Tail convexity: how IV accelerates toward deep OTM puts (10d vs 25d slope).
"""

import os

from flashalpha import FlashAlpha, TierRestrictedError

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

fa = FlashAlpha(os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY"))

# TSLA is a high-skew name — the skew is more pronounced than on index ETFs
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

skew_profiles = data.get("skew_profiles", [])
atm_iv        = data.get("atm_iv")

# ---------------------------------------------------------------------------
# Display skew metrics by expiry
# ---------------------------------------------------------------------------

print(f"\n{'='*85}")
print(f"  Volatility Skew Analysis  —  {SYMBOL}  (ATM IV: {atm_iv:.1f}%)")
print(f"{'='*85}")
print(
    f"  {'Expiry':12s}  {'DTE':>5}  "
    f"{'10d Put':>9}  {'25d Put':>9}  {'ATM':>7}  {'25d Call':>9}  {'10d Call':>9}  "
    f"{'RR 25d':>8}  {'BF 25d':>8}  {'Smile Ratio':>12}"
)
print(
    f"  {'-'*12}  {'-'*5}  "
    f"{'-'*9}  {'-'*9}  {'-'*7}  {'-'*9}  {'-'*9}  "
    f"{'-'*8}  {'-'*8}  {'-'*12}"
)

for row in skew_profiles:
    expiry    = row.get("expiry", "")
    dte       = row.get("dte", "")
    put_10d   = row.get("put_10d_iv")
    put_25d   = row.get("put_25d_iv")
    atm       = row.get("atm_iv")
    call_25d  = row.get("call_25d_iv")
    call_10d  = row.get("call_10d_iv")
    rr_25d    = row.get("risk_reversal_25d")  # 25d RR = put - call
    bf_25d    = row.get("butterfly_25d")       # 25d BF = (put + call)/2 - ATM
    smile_ratio = row.get("smile_ratio")        # typically put_10d / atm

    def fmt(v, d=2):
        return f"{v:.{d}f}%" if v is not None else "  N/A  "

    def fmtv(v, d=2):
        return f"{v:.{d}f}" if v is not None else "  N/A"

    print(
        f"  {expiry:12s}  {str(dte):>5}  "
        f"{fmt(put_10d):>9}  {fmt(put_25d):>9}  {fmt(atm):>7}  "
        f"{fmt(call_25d):>9}  {fmt(call_10d):>9}  "
        f"{fmtv(rr_25d):>8}  {fmtv(bf_25d):>8}  {fmtv(smile_ratio, 3):>12}"
    )

# ---------------------------------------------------------------------------
# Tail convexity: how fast IV rises from 25d to 10d put
# ---------------------------------------------------------------------------

print()
print(f"{'='*85}")
print("  Tail Convexity (slope of IV from 25d put to 10d put)")
print(f"{'='*85}")
print(f"  {'Expiry':12s}  {'DTE':>5}  {'25d Put':>9}  {'10d Put':>9}  {'Tail Slope':>12}")
print(f"  {'-'*12}  {'-'*5}  {'-'*9}  {'-'*9}  {'-'*12}")

for row in skew_profiles:
    expiry  = row.get("expiry", "")
    dte     = row.get("dte", "")
    put_10d = row.get("put_10d_iv")
    put_25d = row.get("put_25d_iv")
    # tail convexity already provided by the API
    tail_conv = row.get("tail_convexity")

    # fallback: compute from put_10d - put_25d if tail_convexity not present
    if tail_conv is None and put_10d is not None and put_25d is not None:
        tail_conv = put_10d - put_25d

    tc_str = f"{tail_conv:.2f}v" if tail_conv is not None else "N/A"

    print(
        f"  {expiry:12s}  {str(dte):>5}  "
        f"{fmt(put_25d):>9}  {fmt(put_10d):>9}  {tc_str:>12}"
    )

print()
print("Interpretation:")
print("  - Risk reversal < 0: puts are more expensive than equivalent calls (normal for equities).")
print("  - Risk reversal closer to 0: market is less concerned about downside tail risk.")
print("  - Large butterfly: fat tails on both sides — market expects large moves in either direction.")
print("  - High smile ratio (put_10d / ATM >> 1): deep OTM crash protection is expensive.")
print("  - Steep tail convexity: IV accelerates sharply into the left tail — high crash premium.")
print()
print("Learn more:")
print("  https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection")
