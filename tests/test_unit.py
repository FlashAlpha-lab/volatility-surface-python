"""
Unit tests for volatility surface examples — all API calls are mocked with `responses`.

Tests cover:
  - adv_volatility response parsing: SVI params, total variance surface,
    arbitrage flags, greeks surfaces, variance swap fair values, forward prices
  - volatility response parsing: realized vol, skew profiles, term structure, VRP
  - surface (public) response parsing
  - IV solver response parsing
  - greeks response parsing
  - error handling: 401 auth, 403 tier restricted (Alpha+), 429 rate limit
  - empty arbitrage flags handling
  - multi-symbol IV rank scan
"""

import pytest
import responses

from flashalpha import (
    AuthenticationError,
    FlashAlpha,
    NotFoundError,
    RateLimitError,
    TierRestrictedError,
)

BASE = "https://lab.flashalpha.com"


@pytest.fixture
def fa():
    return FlashAlpha("test-key")


# ---------------------------------------------------------------------------
# Helpers: build realistic mock payloads
# ---------------------------------------------------------------------------

def make_adv_volatility_payload(symbol="SPY"):
    """Realistic adv_volatility response with SVI, surface, arb, greeks, var swap."""
    return {
        "symbol": symbol,
        "svi_parameters": [
            {
                "expiry": "2026-04-04",
                "dte": 9,
                "a": 0.0045,
                "b": 0.1823,
                "rho": -0.6214,
                "m": -0.0312,
                "sigma": 0.0891,
                "atm_total_variance": 0.0182,
                "atm_iv": 18.52,
                "forward_price": 583.21,
            },
            {
                "expiry": "2026-04-17",
                "dte": 22,
                "a": 0.0061,
                "b": 0.1540,
                "rho": -0.5890,
                "m": -0.0280,
                "sigma": 0.1021,
                "atm_total_variance": 0.0298,
                "atm_iv": 19.87,
                "forward_price": 584.10,
            },
        ],
        "total_variance_surface": {
            "moneyness": [-0.2, -0.1, 0.0, 0.1, 0.2],
            "expiries":  ["2026-04-04", "2026-04-17"],
            "rows": [
                [0.0412, 0.0225, 0.0182, 0.0198, 0.0267],
                [0.0578, 0.0341, 0.0298, 0.0312, 0.0401],
            ],
        },
        "arbitrage_flags": [],
        "greeks_surfaces": {
            "vanna": {
                "moneyness": [-0.2, -0.1, 0.0, 0.1, 0.2],
                "expiries":  ["2026-04-04", "2026-04-17"],
                "rows": [
                    [-0.0412, -0.0185, 0.0000,  0.0092,  0.0201],
                    [-0.0310, -0.0140, 0.0000,  0.0071,  0.0158],
                ],
            },
            "charm": {
                "moneyness": [-0.2, -0.1, 0.0, 0.1, 0.2],
                "expiries":  ["2026-04-04", "2026-04-17"],
                "rows": [
                    [-0.0021, -0.0154, -0.0003,  0.0148,  0.0019],
                    [-0.0012, -0.0089, -0.0002,  0.0085,  0.0011],
                ],
            },
            "volga": {
                "moneyness": [-0.2, -0.1, 0.0, 0.1, 0.2],
                "expiries":  ["2026-04-04", "2026-04-17"],
                "rows": [
                    [0.0812, 0.0341, 0.0010, 0.0298, 0.0701],
                    [0.0650, 0.0280, 0.0008, 0.0245, 0.0580],
                ],
            },
            "speed": {
                "moneyness": [-0.2, -0.1, 0.0, 0.1, 0.2],
                "expiries":  ["2026-04-04", "2026-04-17"],
                "rows": [
                    [0.0003, 0.0018, 0.0000, -0.0017, -0.0003],
                    [0.0002, 0.0012, 0.0000, -0.0011, -0.0002],
                ],
            },
        },
        "variance_swap_fair_values": [
            {
                "expiry": "2026-04-04",
                "dte": 9,
                "fair_variance": 0.0197,
                "fair_vol": 19.85,
                "convexity_adjustment": 1.33,
            },
            {
                "expiry": "2026-04-17",
                "dte": 22,
                "fair_variance": 0.0318,
                "fair_vol": 21.02,
                "convexity_adjustment": 1.15,
            },
        ],
    }


def make_volatility_payload(symbol="SPY"):
    """Realistic volatility response with RV, skew, term structure, VRP."""
    return {
        "symbol": symbol,
        "atm_iv": 19.2,
        "iv_rank": 42.0,
        "iv_percentile": 38.0,
        "realized_vol": {
            "rv_5d":  14.8,
            "rv_10d": 16.3,
            "rv_20d": 15.9,
            "rv_30d": 17.1,
            "rv_60d": 18.5,
        },
        "iv_rv_spreads": {
            "spread_5d":  4.4,
            "spread_10d": 2.9,
            "spread_20d": 3.3,
            "spread_30d": 2.1,
            "spread_60d": 0.7,
            "assessment": "Options are moderately rich; mild seller edge on 5d-20d windows.",
        },
        "skew_profiles": [
            {
                "expiry": "2026-04-04",
                "dte": 9,
                "atm_iv": 19.2,
                "put_10d_iv": 28.1,
                "put_25d_iv": 22.4,
                "call_25d_iv": 16.9,
                "call_10d_iv": 14.2,
                "risk_reversal_25d": -5.5,
                "butterfly_25d": 1.3,
                "smile_ratio": 1.46,
                "tail_convexity": 5.7,
            },
            {
                "expiry": "2026-04-17",
                "dte": 22,
                "atm_iv": 20.1,
                "put_10d_iv": 27.3,
                "put_25d_iv": 23.2,
                "call_25d_iv": 17.8,
                "call_10d_iv": 15.1,
                "risk_reversal_25d": -5.4,
                "butterfly_25d": 1.5,
                "smile_ratio": 1.36,
                "tail_convexity": 4.1,
            },
        ],
        "term_structure": {
            "shape": "contango",
            "near_slope": 0.82,
            "far_slope": 0.31,
            "iv_dispersion": 1.8,
        },
    }


# ---------------------------------------------------------------------------
# 1. adv_volatility response parsing — SVI parameters
# ---------------------------------------------------------------------------

@responses.activate
def test_adv_volatility_svi_parameters(fa):
    """SVI parameter fields are correctly parsed from adv_volatility."""
    payload = make_adv_volatility_payload()
    responses.get(f"{BASE}/v1/adv_volatility/SPY", json=payload)

    result = fa.adv_volatility("SPY")

    assert result["symbol"] == "SPY"
    svi = result["svi_parameters"]
    assert isinstance(svi, list)
    assert len(svi) == 2

    row = svi[0]
    assert row["expiry"] == "2026-04-04"
    assert row["a"] == 0.0045
    assert row["b"] == 0.1823
    assert row["rho"] == -0.6214
    assert row["m"] == -0.0312
    assert row["sigma"] == 0.0891
    assert row["atm_iv"] == 18.52
    assert row["forward_price"] == 583.21


# ---------------------------------------------------------------------------
# 2. adv_volatility — total variance surface
# ---------------------------------------------------------------------------

@responses.activate
def test_adv_volatility_total_variance_surface(fa):
    """Total variance surface grid is correctly parsed."""
    payload = make_adv_volatility_payload()
    responses.get(f"{BASE}/v1/adv_volatility/SPY", json=payload)

    result = fa.adv_volatility("SPY")
    surface = result["total_variance_surface"]

    assert "moneyness" in surface
    assert "expiries" in surface
    assert "rows" in surface
    assert len(surface["moneyness"]) == 5
    assert len(surface["expiries"]) == 2
    assert len(surface["rows"]) == 2
    # ATM (k=0) total variance for first expiry
    atm_idx = surface["moneyness"].index(0.0)
    assert surface["rows"][0][atm_idx] == 0.0182


# ---------------------------------------------------------------------------
# 3. adv_volatility — arbitrage flags (clean surface)
# ---------------------------------------------------------------------------

@responses.activate
def test_adv_volatility_arbitrage_flags_empty(fa):
    """Empty arbitrage_flags list is handled gracefully (surface is clean)."""
    payload = make_adv_volatility_payload()
    payload["arbitrage_flags"] = []
    responses.get(f"{BASE}/v1/adv_volatility/SPY", json=payload)

    result = fa.adv_volatility("SPY")
    assert result["arbitrage_flags"] == []
    assert len(result["arbitrage_flags"]) == 0


# ---------------------------------------------------------------------------
# 4. adv_volatility — arbitrage flags (violations present)
# ---------------------------------------------------------------------------

@responses.activate
def test_adv_volatility_arbitrage_flags_violations(fa):
    """Butterfly and calendar arbitrage flags are parsed correctly."""
    payload = make_adv_volatility_payload()
    payload["arbitrage_flags"] = [
        {
            "type": "butterfly",
            "expiry": "2026-04-04",
            "moneyness": -0.15,
            "d2w_dk2": -0.0012,
            "severity": "minor",
        },
        {
            "type": "calendar",
            "near_expiry": "2026-04-04",
            "far_expiry": "2026-04-17",
            "moneyness": 0.10,
            "near_variance": 0.0210,
            "far_variance": 0.0205,
        },
    ]
    responses.get(f"{BASE}/v1/adv_volatility/SPY", json=payload)

    result = fa.adv_volatility("SPY")
    flags = result["arbitrage_flags"]

    assert len(flags) == 2
    butterfly = [f for f in flags if f["type"] == "butterfly"]
    calendar  = [f for f in flags if f["type"] == "calendar"]

    assert len(butterfly) == 1
    assert butterfly[0]["expiry"] == "2026-04-04"
    assert butterfly[0]["d2w_dk2"] == -0.0012

    assert len(calendar) == 1
    assert calendar[0]["near_expiry"] == "2026-04-04"
    assert calendar[0]["far_expiry"]  == "2026-04-17"


# ---------------------------------------------------------------------------
# 5. adv_volatility — greeks surfaces
# ---------------------------------------------------------------------------

@responses.activate
def test_adv_volatility_greeks_surfaces(fa):
    """Higher-order greeks surfaces (vanna, charm, volga, speed) are parsed."""
    payload = make_adv_volatility_payload()
    responses.get(f"{BASE}/v1/adv_volatility/SPY", json=payload)

    result = fa.adv_volatility("SPY")
    gs = result["greeks_surfaces"]

    for greek in ["vanna", "charm", "volga", "speed"]:
        assert greek in gs
        assert "moneyness" in gs[greek]
        assert "expiries" in gs[greek]
        assert "rows" in gs[greek]

    # Vanna at ATM (k=0.0) should be zero by symmetry
    vanna = gs["vanna"]
    atm_idx = vanna["moneyness"].index(0.0)
    assert vanna["rows"][0][atm_idx] == 0.0


# ---------------------------------------------------------------------------
# 6. adv_volatility — variance swap fair values
# ---------------------------------------------------------------------------

@responses.activate
def test_adv_volatility_variance_swap_fair_values(fa):
    """Variance swap fair values are correctly parsed."""
    payload = make_adv_volatility_payload()
    responses.get(f"{BASE}/v1/adv_volatility/SPY", json=payload)

    result = fa.adv_volatility("SPY")
    var_swaps = result["variance_swap_fair_values"]

    assert isinstance(var_swaps, list)
    assert len(var_swaps) == 2

    vs = var_swaps[0]
    assert vs["expiry"] == "2026-04-04"
    assert vs["fair_variance"] == 0.0197
    assert vs["fair_vol"] == 19.85
    assert vs["convexity_adjustment"] == 1.33

    # Fair vol must exceed ATM IV (convexity adjustment is positive)
    svi_atm_iv = payload["svi_parameters"][0]["atm_iv"]
    assert vs["fair_vol"] > svi_atm_iv


# ---------------------------------------------------------------------------
# 7. volatility — realized vol parsing
# ---------------------------------------------------------------------------

@responses.activate
def test_volatility_realized_vol(fa):
    """All realized vol windows are correctly parsed."""
    payload = make_volatility_payload()
    responses.get(f"{BASE}/v1/volatility/SPY", json=payload)

    result = fa.volatility("SPY")
    rv = result["realized_vol"]

    assert rv["rv_5d"]  == 14.8
    assert rv["rv_10d"] == 16.3
    assert rv["rv_20d"] == 15.9
    assert rv["rv_30d"] == 17.1
    assert rv["rv_60d"] == 18.5


# ---------------------------------------------------------------------------
# 8. volatility — skew profiles
# ---------------------------------------------------------------------------

@responses.activate
def test_volatility_skew_profiles(fa):
    """Skew profile fields (RR, BF, smile ratio, tail convexity) are parsed."""
    payload = make_volatility_payload()
    responses.get(f"{BASE}/v1/volatility/SPY", json=payload)

    result = fa.volatility("SPY")
    skew = result["skew_profiles"]

    assert isinstance(skew, list)
    assert len(skew) == 2

    s = skew[0]
    assert s["expiry"] == "2026-04-04"
    assert s["risk_reversal_25d"] == -5.5
    assert s["butterfly_25d"] == 1.3
    assert s["smile_ratio"] == 1.46
    # Put 10d IV should exceed ATM IV
    assert s["put_10d_iv"] > s["atm_iv"]


# ---------------------------------------------------------------------------
# 9. volatility — term structure
# ---------------------------------------------------------------------------

@responses.activate
def test_volatility_term_structure(fa):
    """Term structure shape, slopes, and dispersion are parsed."""
    payload = make_volatility_payload()
    responses.get(f"{BASE}/v1/volatility/SPY", json=payload)

    result = fa.volatility("SPY")
    ts = result["term_structure"]

    assert ts["shape"] == "contango"
    assert ts["near_slope"] == 0.82
    assert ts["far_slope"] == 0.31
    assert ts["iv_dispersion"] == 1.8


# ---------------------------------------------------------------------------
# 10. volatility — VRP / IV-RV spreads
# ---------------------------------------------------------------------------

@responses.activate
def test_volatility_iv_rv_spreads(fa):
    """IV-RV spread values and assessment are correctly parsed."""
    payload = make_volatility_payload()
    responses.get(f"{BASE}/v1/volatility/SPY", json=payload)

    result = fa.volatility("SPY")
    spreads = result["iv_rv_spreads"]

    assert spreads["spread_5d"]  == 4.4
    assert spreads["spread_20d"] == 3.3
    assert spreads["spread_60d"] == 0.7
    assert "assessment" in spreads
    assert len(spreads["assessment"]) > 0


# ---------------------------------------------------------------------------
# 11. volatility — IV rank and percentile
# ---------------------------------------------------------------------------

@responses.activate
def test_volatility_iv_rank_and_percentile(fa):
    """IV rank (0-100) and IV percentile fields are parsed."""
    payload = make_volatility_payload()
    responses.get(f"{BASE}/v1/volatility/SPY", json=payload)

    result = fa.volatility("SPY")
    assert result["iv_rank"] == 42.0
    assert result["iv_percentile"] == 38.0
    assert 0 <= result["iv_rank"] <= 100


# ---------------------------------------------------------------------------
# 12. surface (public) response parsing
# ---------------------------------------------------------------------------

@responses.activate
def test_surface_parsing(fa):
    """Public vol surface response is parsed correctly."""
    payload = {
        "symbol": "SPY",
        "data": [
            {"expiry": "2026-04-04", "strike": 580, "call_iv": 0.185, "put_iv": 0.187},
            {"expiry": "2026-04-04", "strike": 590, "call_iv": 0.172, "put_iv": 0.175},
        ],
    }
    responses.get(f"{BASE}/v1/surface/SPY", json=payload)

    result = fa.surface("SPY")
    assert result["symbol"] == "SPY"
    assert isinstance(result["data"], list)
    assert result["data"][0]["strike"] == 580


# ---------------------------------------------------------------------------
# 13. IV solver response parsing
# ---------------------------------------------------------------------------

@responses.activate
def test_iv_solver_parsing(fa):
    """IV solver returns implied_volatility and implied_volatility_pct."""
    payload = {
        "implied_volatility": 0.1952,
        "implied_volatility_pct": 19.52,
    }
    responses.get(f"{BASE}/v1/pricing/iv", json=payload)

    result = fa.iv(spot=583, strike=583, dte=9, price=8.45)
    assert result["implied_volatility"] == 0.1952
    assert result["implied_volatility_pct"] == 19.52
    assert 0 < result["implied_volatility"] < 2.0


# ---------------------------------------------------------------------------
# 14. greeks response parsing
# ---------------------------------------------------------------------------

@responses.activate
def test_greeks_parsing(fa):
    """BSM greeks response includes first, second, and third order."""
    payload = {
        "theoretical_price": 8.45,
        "first_order": {
            "delta": 0.512,
            "gamma": 0.028,
            "theta": -0.042,
            "vega": 0.183,
            "rho": 0.091,
        },
        "second_order": {
            "vanna": -0.0312,
            "charm": -0.0081,
            "vomma": 0.0215,
        },
        "third_order": {
            "speed": 0.00014,
            "zomma": -0.00082,
            "color": 0.00031,
        },
    }
    responses.get(f"{BASE}/v1/pricing/greeks", json=payload)

    result = fa.greeks(spot=583, strike=583, dte=9, sigma=0.1952)
    assert result["theoretical_price"] == 8.45
    assert result["first_order"]["delta"] == 0.512
    assert result["second_order"]["vanna"] == -0.0312
    assert result["third_order"]["speed"] == 0.00014


# ---------------------------------------------------------------------------
# 15. error handling — 401 authentication error
# ---------------------------------------------------------------------------

@responses.activate
def test_401_authentication_error(fa):
    """401 response raises AuthenticationError."""
    responses.get(
        f"{BASE}/v1/adv_volatility/SPY",
        json={"detail": "Invalid API key."},
        status=401,
    )

    with pytest.raises(AuthenticationError) as exc_info:
        fa.adv_volatility("SPY")
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# 16. error handling — 403 tier restricted (Alpha+ required)
# ---------------------------------------------------------------------------

@responses.activate
def test_403_tier_restricted_adv_volatility(fa):
    """403 on adv_volatility raises TierRestrictedError with plan info."""
    responses.get(
        f"{BASE}/v1/adv_volatility/SPY",
        json={
            "status": "ERROR",
            "error": "tier_restricted",
            "message": "adv_volatility requires Alpha plan.",
            "current_plan": "Growth",
            "required_plan": "Alpha",
        },
        status=403,
    )

    with pytest.raises(TierRestrictedError) as exc_info:
        fa.adv_volatility("SPY")

    err = exc_info.value
    assert err.status_code == 403
    assert err.current_plan == "Growth"
    assert err.required_plan == "Alpha"


# ---------------------------------------------------------------------------
# 17. error handling — 429 rate limit
# ---------------------------------------------------------------------------

@responses.activate
def test_429_rate_limit(fa):
    """429 response raises RateLimitError with retry_after."""
    responses.get(
        f"{BASE}/v1/volatility/TSLA",
        json={"message": "Quota exceeded."},
        status=429,
        headers={"Retry-After": "30"},
    )

    with pytest.raises(RateLimitError) as exc_info:
        fa.volatility("TSLA")

    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == 30


# ---------------------------------------------------------------------------
# 18. multiple symbols scanning (IV rank scanner pattern)
# ---------------------------------------------------------------------------

@responses.activate
def test_multi_symbol_volatility_scan(fa):
    """Multiple volatility calls for different symbols return independent results."""
    symbols = ["SPY", "QQQ", "TSLA"]
    atm_ivs = [19.2, 21.5, 48.7]

    for symbol, atm_iv in zip(symbols, atm_ivs):
        responses.get(
            f"{BASE}/v1/volatility/{symbol}",
            json=make_volatility_payload(symbol) | {"atm_iv": atm_iv, "symbol": symbol},
        )

    results = []
    for symbol in symbols:
        data = fa.volatility(symbol)
        results.append({"symbol": symbol, "atm_iv": data["atm_iv"]})

    assert len(results) == 3
    assert results[0]["symbol"] == "SPY"
    assert results[0]["atm_iv"] == 19.2
    assert results[1]["atm_iv"] == 21.5
    assert results[2]["symbol"] == "TSLA"
    assert results[2]["atm_iv"] == 48.7


# ---------------------------------------------------------------------------
# 19. multi-symbol scan with mixed errors
# ---------------------------------------------------------------------------

@responses.activate
def test_multi_symbol_scan_with_tier_error(fa):
    """Tier error on one symbol does not prevent other symbols from returning data."""
    responses.get(
        f"{BASE}/v1/volatility/SPY",
        json=make_volatility_payload("SPY"),
    )
    responses.get(
        f"{BASE}/v1/adv_volatility/SPY",
        json={
            "message": "Requires Alpha.",
            "current_plan": "Free",
            "required_plan": "Alpha",
        },
        status=403,
    )

    vol_data = fa.volatility("SPY")
    assert vol_data["symbol"] == "SPY"

    with pytest.raises(TierRestrictedError):
        fa.adv_volatility("SPY")


# ---------------------------------------------------------------------------
# 20. adv_volatility — forward price basis check
# ---------------------------------------------------------------------------

@responses.activate
def test_adv_volatility_forward_prices(fa):
    """Forward prices are present and plausible (> 0) for each expiry."""
    payload = make_adv_volatility_payload()
    responses.get(f"{BASE}/v1/adv_volatility/SPY", json=payload)

    result = fa.adv_volatility("SPY")
    for row in result["svi_parameters"]:
        assert row["forward_price"] > 0
        # Forward should be close to spot (within 5%)
        assert 500 < row["forward_price"] < 700
