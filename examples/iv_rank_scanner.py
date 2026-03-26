"""
IV rank scanner Python example — scan multiple symbols by IV percentile.

Search queries this file targets:
  IV rank scanner python
  implied volatility rank python
  IV percentile python
  high IV stocks python
  options IV scanner python

IV Rank (IVR) measures where current IV sits relative to its trailing range:
    IVR = (current_IV - IV_52w_low) / (IV_52w_high - IV_52w_low) * 100

An IVR of 80 means current IV is in the 80th percentile of its 52-week range.

IV Percentile (IVP) is the fraction of past days where IV was below today's level.

Both metrics help identify whether options are currently "rich" (high IVR/IVP,
good for selling premium) or "cheap" (low IVR/IVP, good for buying options).

Rule of thumb:
  IVR > 50 (or IVP > 50): IV is elevated — premium selling has a historical edge.
  IVR < 30 (or IVP < 30): IV is suppressed — consider buying premium or defined risk.
"""

import os

from flashalpha import FlashAlpha, NotFoundError, TierRestrictedError

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

fa = FlashAlpha(os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY"))

# Scan a broad set of liquid names
SYMBOLS = ["SPY", "QQQ", "AAPL", "TSLA", "NVDA", "AMZN"]

# ---------------------------------------------------------------------------
# Scan each symbol
# ---------------------------------------------------------------------------

results = []

for symbol in SYMBOLS:
    try:
        data = fa.volatility(symbol)
        realized_vol  = data.get("realized_vol", {})
        iv_rv_spreads = data.get("iv_rv_spreads", {})

        results.append({
            "symbol":      symbol,
            "atm_iv":      data.get("atm_iv"),
            "iv_rank":     data.get("iv_rank"),       # 0-100 percentile rank
            "iv_pct":      data.get("iv_percentile"), # fraction of days IV was lower
            "rv_20d":      realized_vol.get("rv_20d"),
            "vrp_20d":     iv_rv_spreads.get("spread_20d"),
            "assessment":  iv_rv_spreads.get("assessment", ""),
            "error":       None,
        })

    except TierRestrictedError as e:
        results.append({
            "symbol":  symbol,
            "error":   f"Requires {e.required_plan} plan",
        })
    except NotFoundError:
        results.append({
            "symbol":  symbol,
            "error":   "Symbol not found",
        })
    except Exception as exc:
        results.append({
            "symbol":  symbol,
            "error":   str(exc),
        })

# ---------------------------------------------------------------------------
# Sort by IV rank (highest first — most expensive options at the top)
# ---------------------------------------------------------------------------

valid   = [r for r in results if r.get("error") is None and r.get("iv_rank") is not None]
invalid = [r for r in results if r.get("error") is not None or r.get("iv_rank") is None]

valid.sort(key=lambda r: r["iv_rank"] or 0, reverse=True)

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

print(f"\n{'='*80}")
print("  IV Rank Scanner  —  Implied Volatility Comparison")
print(f"{'='*80}")
print(
    f"  {'Symbol':8s}  {'ATM IV':>8}  {'IV Rank':>8}  {'IV Pct':>8}  "
    f"{'RV 20d':>8}  {'VRP 20d':>8}  {'Signal':>22}"
)
print(
    f"  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}  "
    f"{'-'*8}  {'-'*8}  {'-'*22}"
)

for r in valid:
    symbol   = r["symbol"]
    atm_iv   = r["atm_iv"]
    iv_rank  = r["iv_rank"]
    iv_pct   = r["iv_pct"]
    rv_20d   = r["rv_20d"]
    vrp_20d  = r["vrp_20d"]

    # Generate a signal based on IV rank
    if iv_rank is not None:
        if iv_rank >= 70:
            signal = "IV RICH — consider selling"
        elif iv_rank >= 50:
            signal = "Elevated — mildly rich"
        elif iv_rank >= 30:
            signal = "Normal range"
        else:
            signal = "IV CHEAP — consider buying"
    else:
        signal = "N/A"

    def fmt(v, d=1):
        return f"{v:.{d}f}%" if v is not None else " N/A"

    def fmtv(v, d=2):
        return f"{v:+.{d}f}v" if v is not None else "N/A"

    def fmtpct(v, d=0):
        return f"{v:.{d}f}" if v is not None else "N/A"

    print(
        f"  {symbol:8s}  {fmt(atm_iv):>8}  {fmtpct(iv_rank):>8}  "
        f"{fmtpct(iv_pct):>8}  {fmt(rv_20d):>8}  {fmtv(vrp_20d):>8}  {signal:>22}"
    )

# Show errors if any
if invalid:
    print()
    for r in invalid:
        print(f"  {r['symbol']:8s}  Error: {r.get('error', 'unknown')}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print()
print(f"{'='*80}")
print("  Summary")
print(f"{'='*80}")

if valid:
    richest  = valid[0]
    cheapest = valid[-1]
    print(f"  Richest IV:   {richest['symbol']:8s}  IV Rank = {richest['iv_rank']:.0f}")
    print(f"  Cheapest IV:  {cheapest['symbol']:8s}  IV Rank = {cheapest['iv_rank']:.0f}")

print()
print("Methodology:")
print("  IV Rank = (current IV - 52w low) / (52w high - 52w low) * 100")
print("  IV Percentile = fraction of trailing days where IV was below today's level")
print()
print("Premium selling signals (sell at high IVR, buy back at low IVR):")
print("  - Short straddle / strangle at high IVR + high VRP")
print("  - Covered calls at elevated IV on stocks you already hold")
print("  - Cash-secured puts at elevated IV to accumulate shares at a discount")
print()
print("  https://flashalpha.com/articles/realized-vs-implied-volatility-risk-premium")
