# SVI Parameterization

The Stochastic Volatility Inspired (SVI) model was introduced by Jim Gatheral (2004) as a parsimonious five-parameter fit to the total implied variance smile at a fixed expiry. It was designed to reproduce the qualitative behavior of stochastic volatility models (such as Heston) while remaining analytically tractable.

## The Formula

Let k = log(K/F) denote the log-moneyness, where K is the strike and F is the forward price for the given expiry. The SVI parameterization of total variance is:

```
w(k) = a + b * ( rho * (k - m) + sqrt((k - m)^2 + sigma^2) )
```

The total variance w(k) is related to the more familiar implied volatility sigma_BS(k) by:

```
w(k) = sigma_BS(k)^2 * T
```

where T is time to expiry in years. Total variance removes the sqrt(T) scaling, making it natural to compare smiles across different expiries.

## Parameters

### a — Vertical level
The parameter a shifts the entire smile up or down along the variance axis. It controls the overall level of total variance.

- a > 0 raises the smile
- a must satisfy a + b * sigma * sqrt(1 - rho^2) >= 0 (ATM variance must be non-negative)
- In the limit where b -> 0, the smile becomes flat at height a

### b — Wing slope
The parameter b controls how quickly total variance rises as log-moneyness moves away from the center m. Larger b means steeper wings and a more pronounced smile.

- b > 0 (required for the smile to be non-flat)
- b has units of (variance / log-moneyness), but since both are dimensionless, b is just a scale factor
- Very large b produces steep wings that may violate the no-arbitrage condition: b must satisfy b * (1 + |rho|) < 4/T (the Lee moment formula bound)

### rho — Correlation / asymmetry
The parameter rho tilts the smile left or right, introducing asymmetry between the put and call wings.

- rho in (-1, 1)
- Negative rho (typical for equities): the left wing (put side) is elevated relative to the right wing, producing the observed equity skew
- Positive rho (unusual): the call side is elevated, typical in some commodity markets (natural gas) where price spikes drive call demand
- When rho = 0, the smile is symmetric around k = m

### m — Horizontal shift
The parameter m shifts the minimum of the smile along the log-moneyness axis.

- Can be negative or positive
- When m < 0, the minimum variance point is to the left of ATM (more common in equity names)
- When m = 0 and rho = 0, the minimum is exactly at k = 0 (ATM)

### sigma — ATM curvature
The parameter sigma controls the shape of the smile near its minimum. Larger sigma produces a rounder, more parabolic ATM region; sigma approaching 0 produces a V-shaped smile.

- sigma > 0 (required to keep the expression under the square root positive)
- Small sigma: the smile has a sharp vertex, like a tent function
- Large sigma: the smile is rounded and more parabolic near ATM

## ATM Properties

Setting k = 0 in the formula:

```
w(0) = a + b * ( -rho * m + sqrt(m^2 + sigma^2) )
```

In the simplified case m = 0:

```
w(0) = a + b * sigma
```

And the ATM implied volatility is:

```
ATM_IV = sqrt(w(0) / T)
```

## Arbitrage-Free Conditions

A valid SVI parameterization must satisfy two conditions:

### 1. Non-negative density (no butterfly arbitrage)

The risk-neutral density p(k) must be non-negative everywhere. This requires:

```
g(k) = (1 - k * w'(k) / (2*w(k)))^2 - w'(k)^2 / 4 * (1/w(k) + 1/4) + w''(k) / 2 >= 0
```

where w'(k) = dw/dk and w''(k) = d^2w/dk^2. A necessary (but not sufficient) condition is:

```
w''(k) >= 0   for all k
```

This means total variance must be convex in log-moneyness — i.e., the smile must be concave-up everywhere.

### 2. Non-decreasing variance (no calendar arbitrage)

For two expiries T1 < T2, we must have:

```
w(k, T1) <= w(k, T2)   for all k
```

This is satisfied automatically if the SVI parameters are fit jointly across expiries using a consistent term structure model (such as the SSVI or eSSVI framework).

## Surface SVI (SSVI)

The Surface SVI (SSVI) parameterization introduced by Gatheral and Jacquier (2014) extends raw SVI to the full surface by imposing a parametric form on how the SVI parameters evolve with T. This guarantees calendar-arbitrage freedom by construction.

The SSVI total variance is:

```
w(k, T) = (theta_T / 2) * (1 + rho * phi(theta_T) * k + sqrt((phi(theta_T)*k + rho)^2 + 1 - rho^2))
```

where theta_T = w(0, T) is the ATM total variance term structure and phi is a function that controls how the smile flattens with maturity.

## Practical Notes

- SVI fits are calibrated by minimizing a weighted sum of squared residuals between the model smile and market-quoted implied volatilities
- Liquid expiries (many strikes, tight bid-ask) produce better fits
- Very short expiries (DTE < 3) can produce degenerate fits because the smile is nearly linear
- The FlashAlpha API calibrates SVI parameters in real time using live market option prices

## References

- Gatheral, J. (2004). *A Parsimonious Arbitrage-Free Implied Volatility Parameterization with Application to the Valuation of Volatility Derivatives.*
- Gatheral, J. and Jacquier, A. (2014). *Arbitrage-Free SVI Volatility Surfaces.* Quantitative Finance.
- Lee, R. (2004). *The Moment Formula for Implied Volatility at Extreme Strikes.*

## Related Resources

- [Advanced Volatility API: SVI, Variance Surface, Arbitrage Detection](https://flashalpha.com/articles/advanced-volatility-api-svi-variance-surface-arbitrage-detection)
- [FlashAlpha Python SDK](https://github.com/FlashAlpha-lab/flashalpha-python)
- [flashalpha.com](https://flashalpha.com)
