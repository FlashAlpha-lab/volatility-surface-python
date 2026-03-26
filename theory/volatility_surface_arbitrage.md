# Volatility Surface Arbitrage

A volatility surface is arbitrage-free if and only if it satisfies two sets of conditions: butterfly conditions within each expiry (static arbitrage along the strike dimension) and calendar conditions across expiries (static arbitrage along the time dimension).

Violating either condition means a market participant could construct a portfolio with a non-positive cost and a non-negative payoff — a free lunch that should not persist in efficient markets.

## Butterfly Arbitrage

Butterfly arbitrage occurs when the risk-neutral density implied by the volatility surface is negative for some range of strikes at a given expiry.

### The Butterfly Portfolio

A butterfly spread at strikes K1 < K2 < K3 (with K2 = (K1 + K3) / 2 for simplicity) has the payoff profile of a tent function: positive for stock prices between K1 and K3, zero otherwise. If the risk-neutral density were negative in this region, the butterfly would have a negative expected value but non-negative payoff — an arbitrage.

### The Mathematical Condition

The risk-neutral density p(K) is related to the call price by Breeden-Litzenberger:

```
p(K) = exp(r*T) * d^2C(K) / dK^2
```

Non-negativity of p(K) requires:

```
d^2C(K) / dK^2 >= 0   for all K
```

In terms of total variance w(k) as a function of log-moneyness k = log(K/F), the condition becomes (Roper, 2010):

```
g(k) = (1 - k * w'(k) / (2*w(k)))^2 - w'(k)^2 / 4 * (1/w(k) + 1/4) + w''(k) / 2 >= 0
```

A simpler sufficient (but not necessary) condition is:

```
w''(k) >= 0   for all k
```

i.e., total variance is convex in log-moneyness. This means the smile must be "concave up" — curving upward as you move away from ATM.

### When Does Butterfly Arbitrage Occur?

In practice, butterfly violations arise from:

1. **Noisy market data**: Individual option quotes may be stale, crossed, or at wide bid-ask spreads, causing the interpolated IV surface to dip locally.

2. **Rigid parameterization**: A five-parameter SVI model may not be flexible enough to fit a complex, multi-modal smile without introducing a local concavity.

3. **Jumps and discrete distributions**: If the market prices a binary event (earnings, FDA approval), the risk-neutral density has a spike — a smooth parametric model may create negative density in adjacent regions.

4. **Very short expiries**: Near-expiry smiles can be V-shaped and difficult to fit with smooth parametric forms.

### Fixing Butterfly Violations

- Arbitrage-free SVI (aSSVI) imposes additional parameter constraints that guarantee g(k) >= 0 everywhere by construction.
- Regularized local volatility fitting with positivity constraints.
- Using a mixture model or jump-diffusion that naturally produces non-negative densities.

## Calendar Arbitrage

Calendar arbitrage occurs when total variance decreases as expiry increases for some moneyness level.

### The Calendar Spread Portfolio

Consider a calendar spread: buy the longer-dated option, sell the shorter-dated option at the same strike. If the longer-dated option is cheaper (in total variance terms), this spread costs nothing and has a non-negative payoff (due to the European option's time value being at least as large for longer expiries) — a static arbitrage.

### The Mathematical Condition

For two expiries T1 < T2, the no-calendar-arbitrage condition is:

```
w(k, T1) <= w(k, T2)   for all k
```

i.e., total variance must be non-decreasing in T for every log-moneyness k.

Equivalently, the forward variance between T1 and T2:

```
w_fwd(k, T1, T2) = w(k, T2) - w(k, T1)
```

must be non-negative.

### When Does Calendar Arbitrage Occur?

1. **Fitting each expiry independently**: If SVI is calibrated separately per expiry without joint constraints, the resulting surfaces may violate the monotonicity condition between adjacent expiries.

2. **Event clustering**: If two earnings announcements or macro events are closely spaced, the term structure may invert between them.

3. **Data errors**: A misquoted long-dated option (cheaper than it should be) can create an apparent calendar violation.

4. **Dividend jumps**: Discrete dividends cause the forward price to jump downward on ex-dividend dates, which can cause apparent inversions in naive surface constructions.

### Fixing Calendar Violations

- Fit the surface globally across all expiries simultaneously, imposing d(w)/dT >= 0 as an explicit constraint.
- Use a term-structure-consistent parameterization (SSVI, Hendriks-Martini) where calendar freedom is guaranteed by construction.
- Interpolate in the forward variance dimension (rather than total variance) to ensure non-negativity by construction.

## Why Arbitrage-Free Surfaces Matter

**For pricing**: A model that admits arbitrage will produce inconsistent derivative prices. Exotic products (barrier options, cliquets, variance swaps) are extremely sensitive to the full surface shape, and even small violations can produce large pricing errors.

**For hedging**: Greeks derived from an arbitrage-violated surface may be negative when they should be positive (e.g., negative vega for a long call), leading to incorrect hedges.

**For risk management**: Risk models that use implied distributions must ensure the distribution integrates to 1 and is everywhere non-negative.

**For regulatory reporting**: Capital models that use implied surfaces must demonstrate internal consistency and arbitrage freedom to regulators.

## Related Resources

- [Advanced Volatility API: SVI, Variance Surface, Arbitrage Detection](https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection)
- [SVI Parameterization](svi_parameterization.md)
- [Variance Swaps](variance_swaps.md)
- [FlashAlpha Python SDK](https://github.com/FlashAlpha-lab/flashalpha-python)
- [flashalpha.com](https://flashalpha.com)
