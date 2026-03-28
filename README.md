# Volatility Surface Python

[![CI](https://github.com/FlashAlpha-lab/volatility-surface-python/actions/workflows/ci.yml/badge.svg)](https://github.com/FlashAlpha-lab/volatility-surface-python/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/flashalpha)](https://pypi.org/project/flashalpha/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Practical Python examples for implied volatility surface construction, SVI calibration, variance swap pricing, arbitrage detection, volatility skew analysis, realized vs implied volatility, and vol risk premium — all powered by the [FlashAlpha API](https://flashalpha.com).

```bash
pip install flashalpha
```

---

## What Is an Implied Volatility Surface?

The implied volatility surface is a three-dimensional representation of the implied volatility (IV) extracted from options prices across all strikes and expiries for a given underlying asset. Because the Black-Scholes model assumes a single constant volatility, the surface captures the market's departures from that assumption.

The two axes of the surface are:

- **Moneyness (or log-moneyness)**: the relationship between the strike price and the current forward price. At-the-money (ATM) options sit at the center; out-of-the-money puts are to the left and OTM calls to the right.
- **Time to expiry (DTE)**: measured in calendar days or years. Short-dated options form the front of the surface; long-dated options form the back.

The height of the surface at any point is the implied volatility — the value of sigma that makes the Black-Scholes price match the observed market price for that strike and expiry.

**Why does the surface matter?**

- Options are consistently more expensive on the downside than the upside (put skew), reflecting demand for crash protection.
- Implied volatility varies with expiry (the term structure), often rising ahead of known events and falling afterward.
- The shape of the surface contains information about the risk-neutral density — the market's probabilistic view of future prices.
- Arbitrage-free conditions must hold across the surface: butterfly constraints within each expiry and calendar constraints across expiries.

---

## SVI Parameterization

The Stochastic Volatility Inspired (SVI) model, introduced by Jim Gatheral, provides a parsimonious five-parameter fit to the total implied variance smile at a single expiry.

The SVI formula for total variance as a function of log-moneyness k = log(K/F) is:

```
w(k) = a + b * ( rho * (k - m) + sqrt((k - m)^2 + sigma^2) )
```

Where:
- **a** — vertical translation; controls the overall level of total variance (ATM variance when rho=0, m=0)
- **b** — the "wings" parameter; controls how quickly variance rises away from ATM. Higher b means more pronounced wings.
- **rho** — correlation between spot and volatility; negative rho tilts the smile left (put skew). Range: (-1, 1).
- **m** — horizontal translation; shifts the minimum of the smile along the log-moneyness axis.
- **sigma** — curvature at the center; controls how sharp the ATM vertex is. As sigma approaches 0 the smile becomes a V-shape; larger sigma rounds the bottom.

**ATM total variance** is w(0) = a + b * sigma * sqrt(1 - rho^2).

**ATM implied volatility** is sqrt(w(0) / T), where T is time to expiry in years.

A fit is arbitrage-free if:
1. w(k) >= 0 for all k (no negative variance)
2. d^2w/dk^2 >= 0 for all k (butterfly arbitrage condition — the density must be non-negative)
3. w(k, T1) <= w(k, T2) for T1 < T2 (calendar arbitrage condition — total variance must be monotonically increasing in time)

See [theory/svi_parameterization.md](theory/svi_parameterization.md) for the full derivation and parameter interpretation.

---

## Variance Swap Pricing

A variance swap is a forward contract on realized variance. The buyer receives (realized variance - fair variance strike) * notional at expiry, with no upfront premium. They are used by volatility traders to take a pure view on realized vol without delta exposure.

**Fair variance** (the strike that makes the swap worth zero at inception) can be approximated from the implied volatility surface by a weighted integral over the cross-section of OTM option prices:

```
K_var = (2/T) * [ integral of (P(K)/K^2 dK) for K < F  +  integral of (C(K)/K^2 dK) for K > F ]
```

Because the fair variance is a linear combination of squared IVs (by the replication argument), it is always slightly higher than the square of the ATM IV when there is a non-flat smile. This difference is the **convexity adjustment** — a direct measure of the smile's curvature or "wings".

Practical implications:
- Shorting a variance swap is equivalent to selling a log-contract and delta-hedging continuously.
- The VIX index is constructed using exactly this replication, making it a 30-day fair-variance estimate.
- Fair vol (sqrt of fair variance) typically exceeds ATM IV by 0.5-2 vol points depending on the skew.

See [theory/variance_swaps.md](theory/variance_swaps.md) for the full pricing derivation.

---

## Arbitrage Detection: Butterfly and Calendar

**Butterfly arbitrage** within a single expiry occurs when the implied density function is negative for some range of strikes. The condition for absence is that the second derivative of total variance with respect to log-moneyness is non-negative:

```
d^2 w(k) / dk^2 >= 0  for all k
```

A violation means you can construct a portfolio of three options at strikes K1 < K2 < K3 that has a non-positive cost and a non-negative payoff — a free lunch.

**Calendar arbitrage** across expiries occurs when total variance decreases as expiry increases for some strike. The condition is:

```
w(k, T1) <= w(k, T2)  for all k, whenever T1 < T2
```

A violation means that the longer-dated option is cheaper (in total variance terms) than the shorter-dated one for the same moneyness, again creating an arbitrage.

See [theory/volatility_surface_arbitrage.md](theory/volatility_surface_arbitrage.md) for the mathematical details.

---

## Volatility Skew and Term Structure

**Volatility skew** refers to the asymmetry in implied volatility across strikes at a single expiry. In equity markets, put IVs are systematically higher than call IVs (negative skew) because:

1. Investors buy puts as portfolio insurance, driving up put premiums.
2. Market crashes are correlated with volatility spikes — the risk-neutral distribution has a fat left tail.

Key skew metrics:
- **Risk reversal (25d)**: IV of 25-delta put minus IV of 25-delta call. More negative = steeper put skew.
- **Butterfly (25d)**: Average of 25d put and call IV minus ATM IV. Measures smile curvature / wings.
- **Tail convexity**: The rate at which IV rises as you move to extreme OTM puts.

**Term structure** refers to how ATM IV varies across expiries. Common shapes:
- **Contango (normal)**: Short-dated IV < long-dated IV. The market expects low near-term vol.
- **Backwardation (inverted)**: Short-dated IV > long-dated IV. Typically observed during stress events or before major catalysts.
- **Flat**: IV is approximately constant across expiries.

---

## Realized vs Implied Volatility and the Vol Risk Premium

**Realized volatility (RV)** is the standard deviation of log returns over a historical lookback window, scaled to annual terms. Common estimators include close-to-close, Parkinson (high-low), Garman-Klass, and Yang-Zhang. See [theory/realized_volatility_estimators.md](theory/realized_volatility_estimators.md) for a comparison.

**Implied volatility (IV)** is forward-looking — it reflects the market's expectation of future realized volatility embedded in option prices, plus any risk premium.

**Volatility risk premium (VRP)** = IV - RV. Historically, implied volatility has exceeded subsequent realized volatility on average — the VRP is usually positive. This means options are systematically overpriced relative to subsequent realized moves, which is the basis of systematic premium-selling strategies (covered calls, short straddles, cash-secured puts).

Key points:
- VRP is not constant — it compresses during stress and expands in quiet markets.
- A high VRP (IV >> RV) suggests options are expensive; premium sellers have an edge.
- A negative VRP (IV < RV) suggests realized vol is outpacing expectations; premium buyers and long vol positions may be favored.
- The appropriate RV window to compare against a given IV depends on the option's DTE.

Learn more: [Realized vs Implied Volatility and the Risk Premium](https://flashalpha.com/articles/realized-vs-implied-volatility-risk-premium)

---

## Quick Start

```python
pip install flashalpha
```

```python
import os
from flashalpha import FlashAlpha, TierRestrictedError

fa = FlashAlpha(os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY"))

# Implied volatility surface and SVI parameters (Alpha+ plan)
try:
    adv = fa.adv_volatility("SPY")
    for row in adv["svi_parameters"][:3]:
        print(f"{row['expiry']:12s}  a={row['a']:.4f}  b={row['b']:.4f}  "
              f"rho={row['rho']:.3f}  m={row['m']:.4f}  sigma={row['sigma']:.4f}")
except TierRestrictedError as e:
    print(f"adv_volatility requires {e.required_plan} plan (you have {e.current_plan})")

# Realized vs implied vol and VRP (Growth+ plan)
vol = fa.volatility("SPY")
rv = vol["realized_vol"]
print(f"ATM IV:    {vol['atm_iv']:.1f}%")
print(f"RV 20d:    {rv['rv_20d']:.1f}%")
print(f"VRP 20d:   {vol['iv_rv_spreads']['spread_20d']:.1f} vol points")
print(f"Assessment: {vol['iv_rv_spreads']['assessment']}")
```

---

## Examples

| File | Description | API Method | Plan |
|------|-------------|------------|------|
| [implied_volatility_surface.py](examples/implied_volatility_surface.py) | Display total variance surface grid | `adv_volatility` | Alpha+ |
| [svi_calibration_example.py](examples/svi_calibration_example.py) | Raw SVI parameters per expiry | `adv_volatility` | Alpha+ |
| [variance_swap_pricing.py](examples/variance_swap_pricing.py) | Variance swap fair values and convexity | `adv_volatility` | Alpha+ |
| [volatility_skew_analysis.py](examples/volatility_skew_analysis.py) | Skew: risk reversal, smile ratio, tail convexity | `volatility` | Growth+ |
| [realized_vs_implied_volatility.py](examples/realized_vs_implied_volatility.py) | RV vs IV across all windows, VRP | `volatility` | Growth+ |
| [volatility_term_structure.py](examples/volatility_term_structure.py) | Term structure slope, contango/backwardation | `volatility` | Growth+ |
| [arbitrage_detection_butterfly_calendar.py](examples/arbitrage_detection_butterfly_calendar.py) | Butterfly and calendar arb flags | `adv_volatility` | Alpha+ |
| [greeks_surface_vanna_charm.py](examples/greeks_surface_vanna_charm.py) | Vanna, charm, volga, speed across surface | `adv_volatility` | Alpha+ |
| [iv_rank_scanner.py](examples/iv_rank_scanner.py) | Scan multiple symbols by IV percentile | `volatility` | Growth+ |
| [vol_risk_premium_analysis.py](examples/vol_risk_premium_analysis.py) | Deep-dive VRP across all RV windows | `volatility` | Growth+ |
| [forward_implied_volatility.py](examples/forward_implied_volatility.py) | Forward prices, basis, cost of carry | `adv_volatility` | Alpha+ |

---

## API Plans

| Plan | Requests/Day | Key Features |
|------|-------------|--------------|
| Free | 5 | Stock quotes, GEX/DEX/VEX/CHEX, BSM greeks, IV solver, vol surface |
| Basic | 100 | Free + index symbols (SPX, VIX, RUT) |
| Growth | 2,500 | + Volatility analytics, exposure summary, 0DTE, Kelly sizing |
| Alpha | Unlimited | + Advanced volatility: SVI, variance surface, arbitrage detection, greeks surfaces, variance swaps |

Get your API key at [flashalpha.com](https://flashalpha.com).

---

## Theory

- [SVI Parameterization](theory/svi_parameterization.md) — formula, parameters, arbitrage-free conditions
- [Variance Swaps](theory/variance_swaps.md) — fair value, replication, convexity adjustment
- [Surface Arbitrage](theory/volatility_surface_arbitrage.md) — butterfly and calendar conditions
- [Realized Volatility Estimators](theory/realized_volatility_estimators.md) — close-to-close, Parkinson, Garman-Klass, Yang-Zhang

---

## Related Articles

- [Advanced Volatility API: SVI, Variance Surface, Arbitrage Detection](https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection)
- [Realized vs Implied Volatility and the Risk Premium](https://flashalpha.com/articles/realized-vs-implied-volatility-risk-premium)
- [Volatility Term Structure: Contango, Backwardation, and Events](https://flashalpha.com/articles/volatility-term-structure-contango-backwardation-events)

---

## Links

- [FlashAlpha](https://flashalpha.com) — API keys, docs, pricing
- [FlashAlpha Python SDK](https://github.com/FlashAlpha-lab/flashalpha-python)
- [API Documentation](https://flashalpha.com/docs)

## Related Repositories

- [FlashAlpha Python SDK](https://github.com/FlashAlpha-lab/flashalpha-python) — `pip install flashalpha`
- [GEX Explained](https://github.com/FlashAlpha-lab/gex-explained) — gamma exposure theory and code
- [0DTE Options Analytics](https://github.com/FlashAlpha-lab/0dte-options-analytics) — 0DTE pin risk, expected move, dealer hedging
- [Examples](https://github.com/FlashAlpha-lab/flashalpha-examples) — more tutorials
- [Awesome Options Analytics](https://github.com/FlashAlpha-lab/awesome-options-analytics) — curated resource list

## License

MIT
