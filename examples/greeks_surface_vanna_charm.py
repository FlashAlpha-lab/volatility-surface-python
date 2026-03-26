"""
Higher-order greeks surface Python example — vanna, charm, volga, speed.

Search queries this file targets:
  vanna charm volga python
  second order greeks options python
  vanna surface options python
  volga vomma options python
  higher order greeks implied volatility python

Higher-order (second and third) greeks measure how the primary greeks
change as market conditions evolve. They are critical for volatility
traders and structured products desks.

Key second-order greeks:
  Vanna  = d(delta)/d(sigma) = d(vega)/d(S)
    Measures how delta changes as IV changes, and how vega changes with spot.
    Important for managing delta-hedged books when the skew moves.

  Charm  = d(delta)/d(T) = d(theta)/d(S)
    Measures how delta changes as time passes. Critical for delta hedgers
    who need to know how much to re-hedge each day purely from time decay.

  Volga (Vomma) = d(vega)/d(sigma)
    Measures how vega changes as IV changes — the convexity of the option
    with respect to volatility. Long options have positive volga.

  Speed  = d(gamma)/d(S)
    Measures how gamma changes as spot moves. Relevant for large spot moves.

The greeks_surfaces field from adv_volatility provides these quantities
evaluated across a moneyness-expiry grid.
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

greeks_surfaces = data.get("greeks_surfaces", {})
svi_params = data.get("svi_parameters", [])

# ---------------------------------------------------------------------------
# Display greeks surfaces
# ---------------------------------------------------------------------------

print(f"\n{'='*70}")
print(f"  Higher-Order Greeks Surfaces  —  {SYMBOL}")
print(f"{'='*70}")

# The greeks_surfaces object contains sub-keys for each greek,
# each holding a grid similar in shape to the total_variance_surface.

greek_names = ["vanna", "charm", "volga", "speed"]

for greek_name in greek_names:
    surface = greeks_surfaces.get(greek_name, {})
    if not surface:
        continue

    moneyness_grid = surface.get("moneyness", [])
    expiries       = surface.get("expiries", [])
    rows           = surface.get("rows", [])

    print(f"\n  --- {greek_name.upper()} ---")

    # Brief description of what this greek means in context
    descriptions = {
        "vanna":  "d(delta)/d(sigma). Negative on the left wing for calls: "
                  "as spot falls and IV rises, delta moves faster than Black-Scholes predicts.",
        "charm":  "d(delta)/d(T). Delta decays toward 0 or 1 as expiry approaches. "
                  "Large near expiry, especially for options near ATM.",
        "volga":  "d(vega)/d(sigma). Positive for OTM options (they benefit from IV rising). "
                  "Long wings = long volga.",
        "speed":  "d(gamma)/d(S). Positive for OTM options: gamma increases as you approach ATM.",
    }
    print(f"  {descriptions.get(greek_name, '')}")
    print()

    if not moneyness_grid or not expiries:
        print("  (No data available)")
        continue

    # Header
    header = f"  {'Expiry':12s}" + "".join(f"{k:8.2f}" for k in moneyness_grid)
    print(header)
    print("  " + "-" * (len(header) - 2))

    for expiry, row in zip(expiries, rows):
        if not row:
            continue
        row_str = f"  {expiry:12s}" + "".join(
            f"{v:8.4f}" if v is not None else f"{'---':>8}"
            for v in row
        )
        print(row_str)

# ---------------------------------------------------------------------------
# If greeks_surfaces is empty, fall back to showing the structure
# ---------------------------------------------------------------------------

if not greeks_surfaces:
    print()
    print("  greeks_surfaces not yet populated for this symbol.")
    print("  The field structure when populated:")
    print()
    print("  data['greeks_surfaces'] = {")
    print("    'vanna': {")
    print("      'moneyness': [-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3],")
    print("      'expiries':  ['2026-04-04', '2026-04-18', ...],")
    print("      'rows':      [[v11, v12, ...], [v21, v22, ...], ...]")
    print("    },")
    print("    'charm': { ... },")
    print("    'volga': { ... },")
    print("    'speed': { ... },")
    print("  }")

# ---------------------------------------------------------------------------
# Practical use cases
# ---------------------------------------------------------------------------

print()
print(f"{'='*70}")
print("  Practical Use Cases for Surface Greeks")
print(f"{'='*70}")
print()
print("  Vanna:")
print("    - Dealers short puts are long vanna: when spot drops, IV rises,")
print("      creating additional delta that forces buying in a falling market.")
print("    - Vanna-weighted strikes are important for GEX flow analysis.")
print()
print("  Charm:")
print("    - Charm tells you how much delta changes overnight from time decay alone.")
print("    - Used by market makers to estimate re-hedging demand at open.")
print()
print("  Volga:")
print("    - Long volga positions (long OTM strangles) profit when IV is volatile.")
print("    - Volga is the 'vega of vega' — important in vol-of-vol models.")
print()
print("  Speed:")
print("    - Large speed near expiry signals rapid gamma changes as spot moves.")
print("    - Relevant for 0DTE hedging where gamma can flip sign quickly.")
print()
print("Learn more:")
print("  https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection")
