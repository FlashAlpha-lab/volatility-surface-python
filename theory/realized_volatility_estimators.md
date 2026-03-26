# Realized Volatility Estimators

Realized volatility (RV) is a backward-looking measure of how much an asset's price actually moved over a historical period, expressed as an annualized standard deviation. Comparing RV to implied volatility (IV) reveals the volatility risk premium (VRP).

Several estimators exist, each with different efficiency and data requirements. "Efficiency" here means how quickly the estimator converges to the true volatility as the observation window grows — a more efficient estimator requires fewer data points to achieve the same accuracy.

## 1. Close-to-Close (Standard Historical Volatility)

The simplest and most commonly reported estimator. Uses only daily closing prices.

```
r_i = ln(C_i / C_{i-1})

RV_CC = sqrt(252 / n * sum_{i=1}^{n} r_i^2)
```

where C_i is the closing price on day i and n is the number of observations. (The mean return is typically omitted — set to zero — to match variance swap convention and reduce estimation noise over short windows.)

**Advantages**: Simple, universally available, easy to understand.

**Disadvantages**: Uses only one price per day (close), ignoring intraday information. Highly sensitive to outlier days. Requires ~30 observations for reasonable precision.

**When to use**: As the standard benchmark, for comparison with IV, or when only EOD data is available.

## 2. Parkinson Estimator

Uses the daily high and low prices to extract more information per day than close-to-close.

```
RV_P = sqrt( 252 / (4 * n * ln(2)) * sum_{i=1}^{n} ln(H_i / L_i)^2 )
```

where H_i and L_i are the daily high and low prices.

**Advantages**: Approximately 5x more efficient than close-to-close (requires ~6 days instead of ~30 for the same precision). Simple to compute.

**Disadvantages**: Biased downward in the presence of jumps (the high-low range understates volatility when a large move opens a gap). Assumes a continuous diffusion with no drift.

**When to use**: When intraday high/low data is available and you want a quick efficiency boost over close-to-close. Good for liquid equities without frequent gaps.

## 3. Garman-Klass Estimator

Combines open, high, low, and close prices for even greater efficiency.

```
RV_GK = sqrt( 252 / n * sum_{i=1}^{n} [
    0.5 * ln(H_i / L_i)^2  -  (2*ln(2) - 1) * ln(C_i / O_i)^2
] )
```

where O_i is the open price on day i.

**Advantages**: Approximately 7-8x more efficient than close-to-close under continuous diffusion assumptions. Uses four price points per day.

**Disadvantages**: Biased downward in the presence of large overnight gaps (open vs previous close). Assumes no drift (mean return = 0). Still sensitive to jumps.

**When to use**: When OHLC data is available, no large overnight gaps are expected, and drift is negligible (short window or low-drift asset).

## 4. Yang-Zhang Estimator

The most sophisticated of the standard OHLC estimators. Combines overnight returns (close-to-open), open-to-close returns, and an intraday Parkinson estimator, correcting for overnight jumps and drift.

```
RV_YZ = sqrt( 252 / n * (sigma_o^2 + k * sigma_c^2 + (1-k) * sigma_rs^2) )
```

where:
- sigma_o^2 = variance of overnight (close-to-open) log returns
- sigma_c^2 = variance of open-to-close (intraday) log returns
- sigma_rs^2 = Rogers-Satchell estimator (handles drift, combines all four prices)
- k = 0.34 / (1.34 + (n+1)/(n-1)) — a constant that minimizes variance of the combined estimator

The Rogers-Satchell component:

```
sigma_rs^2 = (1/n) * sum [ln(H/C) * ln(H/O) + ln(L/C) * ln(L/O)]
```

**Advantages**:
- Handles overnight gaps (open vs prior close), making it robust to dividends, earnings gaps, and index rebalancings
- Handles non-zero drift (more important over longer windows)
- Most efficient of the standard estimators: approximately 14x more efficient than close-to-close

**Disadvantages**:
- Requires OHLC plus previous close, so four price points and a lag
- More complex to implement correctly
- Still does not fully capture jump dynamics (though it is more robust than Parkinson/GK)

**When to use**: This is the recommended general-purpose estimator. Use it whenever OHLC data is available. Particularly important for single stocks where overnight gaps (earnings, news) are common.

## Comparison Table

| Estimator | Data Required | Relative Efficiency | Drift Bias | Gap Bias |
|-----------|--------------|---------------------|------------|----------|
| Close-to-Close | Close | 1x (baseline) | Low | None |
| Parkinson | High, Low | ~5x | Low (assumes no drift) | High |
| Garman-Klass | OHLC | ~7-8x | Low (assumes no drift) | Moderate |
| Yang-Zhang | OHLC + prev Close | ~14x | Handles drift | Low |

## Choosing the Right Window

The RV window should be matched to the IV you are comparing against:

| IV Tenor | Recommended RV Window |
|----------|-----------------------|
| 5 DTE (weekly) | 5-day RV |
| 10 DTE | 10-day RV |
| 30 DTE (monthly) | 20-30 day RV |
| VIX (30-day) | 30-day RV |
| 60+ DTE | 60-day RV |

The VRP comparison is most meaningful when the RV window approximately matches the DTE of the options you are analyzing.

## VRP and the FlashAlpha API

The FlashAlpha `volatility` endpoint computes realized vol using multiple windows (5d, 10d, 20d, 30d, 60d) and returns IV-RV spreads for each window, along with an overall assessment of whether options are currently rich or cheap.

```python
from flashalpha import FlashAlpha
fa = FlashAlpha("YOUR_API_KEY")
vol = fa.volatility("SPY")
print(vol["realized_vol"])        # all RV windows
print(vol["iv_rv_spreads"])       # VRP per window + assessment
```

## Related Resources

- [Realized vs Implied Volatility and the Risk Premium](https://flashalpha.com/articles/realized-vs-implied-volatility-risk-premium)
- [Volatility Term Structure: Contango, Backwardation, and Events](https://flashalpha.com/articles/volatility-term-structure-contango-backwardation-events)
- [FlashAlpha Python SDK](https://github.com/FlashAlpha-lab/flashalpha-python)
- [flashalpha.com](https://flashalpha.com)
