"""
Integration tests for volatility surface examples — hit the live FlashAlpha API.

Run with:
    pytest tests/test_integration.py -m integration

Requires FLASHALPHA_API_KEY environment variable:
    export FLASHALPHA_API_KEY=your_key_here

Tests that require Alpha+ plan are skipped automatically if the key is on a
lower-tier plan (TierRestrictedError is caught and the test is skipped).

Tests that require Growth+ plan are similarly skipped on Free/Basic plans.
"""

import os

import pytest

from flashalpha import FlashAlpha, NotFoundError, TierRestrictedError

API_KEY = os.environ.get("FLASHALPHA_API_KEY", "")

pytestmark = pytest.mark.integration


@pytest.fixture
def fa():
    if not API_KEY:
        pytest.skip("FLASHALPHA_API_KEY environment variable not set")
    return FlashAlpha(API_KEY)


# ---------------------------------------------------------------------------
# 1. Health check (public — no auth required)
# ---------------------------------------------------------------------------

def test_health(fa):
    """API health check returns status field."""
    result = fa.health()
    assert "status" in result


# ---------------------------------------------------------------------------
# 2. Surface (public — no auth required)
# ---------------------------------------------------------------------------

def test_surface_returns_data(fa):
    """Public volatility surface returns data for SPY."""
    result = fa.surface("SPY")
    assert result is not None
    # Surface should have some structure
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# 3. volatility — returns valid data structure (Growth+ plan)
# ---------------------------------------------------------------------------

def test_volatility_spy(fa):
    """volatility('SPY') returns all expected top-level fields."""
    try:
        result = fa.volatility("SPY")
    except TierRestrictedError:
        pytest.skip("volatility requires Growth+ plan")

    assert result["symbol"] == "SPY"
    assert "atm_iv" in result
    assert "realized_vol" in result
    assert "iv_rv_spreads" in result
    assert isinstance(result["atm_iv"], (int, float))
    assert result["atm_iv"] > 0


# ---------------------------------------------------------------------------
# 4. volatility — realized vol windows are present
# ---------------------------------------------------------------------------

def test_volatility_realized_vol_windows(fa):
    """All expected realized vol windows (5d through 60d) are present."""
    try:
        result = fa.volatility("SPY")
    except TierRestrictedError:
        pytest.skip("volatility requires Growth+ plan")

    rv = result.get("realized_vol", {})
    for window in ["rv_5d", "rv_10d", "rv_20d", "rv_30d", "rv_60d"]:
        assert window in rv, f"Missing realized vol window: {window}"
        assert isinstance(rv[window], (int, float))
        assert rv[window] > 0


# ---------------------------------------------------------------------------
# 5. adv_volatility — SVI parameters (Alpha+ plan, skip if lower)
# ---------------------------------------------------------------------------

def test_adv_volatility_svi_parameters(fa):
    """adv_volatility returns SVI parameters per expiry (Alpha+ required)."""
    try:
        result = fa.adv_volatility("SPY")
    except TierRestrictedError:
        pytest.skip("adv_volatility requires Alpha+ plan")

    assert result["symbol"] == "SPY"
    assert "svi_parameters" in result
    svi = result["svi_parameters"]
    assert isinstance(svi, list)
    assert len(svi) > 0

    # Validate parameter ranges for first expiry
    row = svi[0]
    assert "a" in row and "b" in row and "rho" in row and "m" in row and "sigma" in row
    assert row["b"] > 0
    assert -1 < row["rho"] < 1
    assert row["sigma"] > 0
    assert row["atm_iv"] > 0
    assert row["forward_price"] > 0


# ---------------------------------------------------------------------------
# 6. adv_volatility — arbitrage flags present (Alpha+ plan)
# ---------------------------------------------------------------------------

def test_adv_volatility_arbitrage_flags(fa):
    """adv_volatility returns arbitrage_flags list (may be empty for clean surface)."""
    try:
        result = fa.adv_volatility("SPY")
    except TierRestrictedError:
        pytest.skip("adv_volatility requires Alpha+ plan")

    assert "arbitrage_flags" in result
    assert isinstance(result["arbitrage_flags"], list)
    # Flags may be empty (clean surface) or contain violations
    for flag in result["arbitrage_flags"]:
        assert "type" in flag
        assert flag["type"] in ("butterfly", "calendar")


# ---------------------------------------------------------------------------
# 7. greeks calculation — BSM greeks endpoint
# ---------------------------------------------------------------------------

def test_greeks_atm_call(fa):
    """BSM greeks for ATM call are within expected ranges."""
    result = fa.greeks(spot=580, strike=580, dte=30, sigma=0.18, type="call")

    assert "theoretical_price" in result
    assert result["theoretical_price"] > 0

    fo = result["first_order"]
    assert 0.45 < fo["delta"] < 0.55   # ATM call delta ~ 0.5
    assert fo["gamma"] > 0
    assert fo["theta"] < 0
    assert fo["vega"] > 0

    assert "second_order" in result
    assert "third_order" in result


# ---------------------------------------------------------------------------
# 8. IV solver — implied volatility from price
# ---------------------------------------------------------------------------

def test_iv_solver(fa):
    """IV solver returns a plausible implied volatility for a known input."""
    result = fa.iv(spot=580, strike=580, dte=30, price=12.69, type="call")

    assert "implied_volatility" in result
    assert "implied_volatility_pct" in result
    assert 0.05 < result["implied_volatility"] < 1.0
    # IV% should equal IV * 100
    assert abs(result["implied_volatility_pct"] - result["implied_volatility"] * 100) < 0.01


# ---------------------------------------------------------------------------
# 9. stock_quote — live quote for SPY
# ---------------------------------------------------------------------------

def test_stock_quote(fa):
    """Live stock quote returns bid, ask, mid with bid <= ask."""
    result = fa.stock_quote("SPY")

    assert result["ticker"] == "SPY"
    assert "bid" in result
    assert "ask" in result
    assert isinstance(result["bid"], (int, float))
    assert isinstance(result["ask"], (int, float))
    assert result["ask"] >= result["bid"]


# ---------------------------------------------------------------------------
# 10. health — basic API reachability
# ---------------------------------------------------------------------------

def test_health_status_string(fa):
    """Health endpoint returns a non-empty status string."""
    result = fa.health()
    assert "status" in result
    assert len(str(result["status"])) > 0


# ---------------------------------------------------------------------------
# 11. stock_summary — comprehensive summary
# ---------------------------------------------------------------------------

def test_stock_summary(fa):
    """stock_summary returns symbol and price fields."""
    result = fa.stock_summary("SPY")
    assert "symbol" in result
    assert result["symbol"] == "SPY"
    assert "price" in result


# ---------------------------------------------------------------------------
# 12. symbols — list of active symbols
# ---------------------------------------------------------------------------

def test_symbols(fa):
    """symbols() returns a non-empty list of active symbols."""
    result = fa.symbols()
    assert "symbols" in result
    assert isinstance(result["symbols"], list)
    assert len(result["symbols"]) > 0


# ---------------------------------------------------------------------------
# 13. invalid symbol returns 404
# ---------------------------------------------------------------------------

def test_invalid_symbol_raises_not_found(fa):
    """Requesting an invalid symbol raises NotFoundError (404)."""
    with pytest.raises(NotFoundError):
        fa.stock_quote("ZZZZZZZZZ")


# ---------------------------------------------------------------------------
# 14. volatility for high-vol single stock (TSLA)
# ---------------------------------------------------------------------------

def test_volatility_tsla(fa):
    """volatility('TSLA') returns valid data with higher ATM IV than SPY."""
    try:
        spy_data  = fa.volatility("SPY")
        tsla_data = fa.volatility("TSLA")
    except TierRestrictedError:
        pytest.skip("volatility requires Growth+ plan")

    assert tsla_data["symbol"] == "TSLA"
    # TSLA should have higher IV than SPY in normal market conditions
    assert tsla_data["atm_iv"] > spy_data["atm_iv"]


# ---------------------------------------------------------------------------
# 15. adv_volatility — total variance surface grid (Alpha+ plan)
# ---------------------------------------------------------------------------

def test_adv_volatility_total_variance_surface(fa):
    """adv_volatility returns a total_variance_surface with rows and moneyness."""
    try:
        result = fa.adv_volatility("SPY")
    except TierRestrictedError:
        pytest.skip("adv_volatility requires Alpha+ plan")

    assert "total_variance_surface" in result
    surface = result["total_variance_surface"]

    assert "moneyness" in surface
    assert "expiries" in surface
    assert "rows" in surface
    assert len(surface["moneyness"]) > 0
    assert len(surface["expiries"]) > 0
    assert len(surface["rows"]) == len(surface["expiries"])

    # All total variance values should be non-negative
    for row in surface["rows"]:
        for val in row:
            if val is not None:
                assert val >= 0, f"Negative total variance found: {val}"
