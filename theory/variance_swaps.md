# Variance Swaps

A variance swap is a forward contract on realized variance. It is one of the cleanest instruments for taking a pure view on future realized volatility, without any delta exposure from the underlying.

## Payoff Structure

At inception (time 0), the two counterparties agree on a variance strike K_var such that the contract has zero value. At expiry (time T), the payoff to the long is:

```
Payoff = (sigma_R^2 - K_var) * N_var
```

where:
- sigma_R^2 = annualized realized variance over [0, T], computed from daily log returns
- K_var = the fair variance strike agreed at inception
- N_var = notional in variance units (e.g., USD per unit of annualized variance)

In vega terms, traders often express the notional as:
```
N_vega = N_var * (2 * sqrt(K_var))
```

This converts to a notional that approximates a vega position at the strike vol.

## Realized Variance

Realized variance is computed from the daily log return series:

```
sigma_R^2 = (252 / n) * sum_{i=1}^{n} ln(S_i / S_{i-1})^2
```

where n is the number of trading days in the period and 252 is the annualization factor. Note that the mean return is typically omitted (set to zero) to match the conventions used in variance swap term sheets.

## Fair Variance: The Replication Argument

The key insight (Carr and Madan, 1998; Britten-Jones and Neuberger, 2000) is that the fair variance K_var can be exactly replicated by a static portfolio of European options — no dynamic trading required.

The replication formula is:

```
K_var = (2/T) * [ integral from 0 to F of P(K)/K^2 dK  +  integral from F to infinity of C(K)/K^2 dK ]
```

where:
- F = S * exp(r*T) is the forward price
- P(K) = price of a put with strike K
- C(K) = price of a call with strike K
- The 1/K^2 weighting gives equal variance contribution per log-moneyness interval

In discrete form using a grid of strikes K_1 < K_2 < ... < K_n:

```
K_var = (2/T) * sum_i [ Q(K_i) / K_i^2 * delta_K_i ]
```

where Q(K_i) is the OTM option price (put for K_i < F, call for K_i > F) and delta_K_i is the width of the strike interval.

This is exactly the formula used by CBOE to compute the VIX index, making VIX a 30-day fair variance estimate (quoted as volatility, i.e., sqrt(K_var) * 100).

## The Convexity Adjustment

Because fair variance is a sum of squared IVs, and the smile is not flat, the fair vol (sqrt of fair variance) is always strictly greater than the ATM IV when there is any curvature in the smile:

```
Fair vol = sqrt(K_var) > ATM_IV   whenever the smile is not flat
```

The difference is the convexity adjustment:

```
Convexity adjustment = fair_vol - ATM_IV
```

This adjustment is driven by:
- The curvature (butterfly) of the smile — more curvature means a larger adjustment
- The magnitude of the skew — steeper skew increases the left-wing contribution

Typical convexity adjustments:
- SPY: 0.5 to 1.5 vol points (relatively shallow smile)
- TSLA: 1 to 4 vol points (steep smile with strong wings)
- VIX-linked instruments: much larger adjustments during stress

## Why Traders Use Variance Swaps

**1. Pure vol exposure without delta hedging**
A vanilla option position has delta that must be managed dynamically. A variance swap provides realized variance exposure with no delta — the payoff depends only on the path of returns, not the level of the stock.

**2. Gamma P&L capture**
A delta-hedged option position earns (1/2) * Gamma * (dS)^2 - Theta*dt each day. Summing over all days gives approximately realized variance. A variance swap is the explicit forward contract on this quantity.

**3. Volatility relative value**
Traders use variance swaps to express views on IV vs RV (the variance risk premium). Selling a variance swap at current fair variance levels profits if subsequent realized vol is lower than the strike.

**4. Term structure trading**
Calendar spreads of variance swaps allow expression of views on the term structure of realized variance — for example, selling near-dated variance and buying far-dated variance.

## Practical Limitations

- Variance swaps are OTC instruments, not exchange-traded
- The replication requires a continuum of strikes; in practice, only a finite grid is available, introducing discretization error
- Realized variance is path-dependent and sensitive to dividends, jumps, and market closures
- The payoff can be convex in a crisis (sigma_R^2 can spike dramatically), making short variance swaps dangerous without proper risk management

## VIX as a Variance Swap Rate

The VIX index is defined as:

```
VIX = 100 * sqrt(K_var)
```

where K_var is the 30-day fair variance computed using the SPX option chain. VIX futures and options provide exchange-traded access to the variance swap market, though with some differences from OTC variance swaps (most notably, VIX is an expectation, not a realized quantity).

## Related Resources

- [Advanced Volatility API: SVI, Variance Surface, Arbitrage Detection](https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection)
- [Volatility Term Structure: Contango, Backwardation, and Events](https://flashalpha.com/articles/volatility-term-structure-contango-backwardation-events)
- [FlashAlpha Python SDK](https://github.com/FlashAlpha-lab/flashalpha-python)
- [flashalpha.com](https://flashalpha.com)
