import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from vix_engine.vix_analytics import (
    pearson_correlation,
    calculate_vix_analytics,
    get_vix_fallback_data,
    get_vix_analytics
)

client = TestClient(app)

def test_pearson_correlation():
    # Perfect positive correlation
    x1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    y1 = [2.0, 4.0, 6.0, 8.0, 10.0]
    assert pytest.approx(pearson_correlation(x1, y1)) == 1.0

    # Perfect negative correlation
    x2 = [1.0, 2.0, 3.0, 4.0, 5.0]
    y2 = [10.0, 8.0, 6.0, 4.0, 2.0]
    assert pytest.approx(pearson_correlation(x2, y2)) == -1.0

    # Zero correlation (flat lines / no variance)
    x3 = [1.0, 1.0, 1.0]
    y3 = [2.0, 3.0, 4.0]
    assert pearson_correlation(x3, y3) == 0.0

    # Non-matching lengths
    x4 = [1.0, 2.0]
    y4 = [1.0, 2.0, 3.0]
    assert pearson_correlation(x4, y4) == 0.0


@patch("vix_engine.vix_analytics.fetch_yahoo_chart_data")
def test_calculate_vix_analytics_normal(mock_fetch):
    # Setup mock data for normal VIX (Low Volatility)
    def side_effect(ticker, range_val):
        if ticker == "^INDIAVIX":
            # 260 days of historical VIX data ranging between 12.0 and 13.0
            closes = [12.0 + (i % 2) * 1.0 for i in range(260)]  # Alternates 12.0 and 13.0
            # Last close is 13.0, previous is 12.0
            return {
                "timestamp": [1700000000 + i * 86400 for i in range(260)],
                "indicators": {
                    "quote": [{"close": closes}]
                }
            }
        elif ticker in ("^NSEI", "^NSEBANK"):
            # Simple stock closes
            return {
                "timestamp": [1700000000 + i * 86400 for i in range(30)],
                "indicators": {
                    "quote": [{"close": [24000.0 + i * 10 for i in range(30)]}]
                }
            }
        return {}

    mock_fetch.side_effect = side_effect

    res = calculate_vix_analytics()
    assert res["current_vix"] == 13.0
    assert res["previous_vix"] == 12.0
    # Change %: ((13 - 12) / 12) * 100 = 8.33% (No shock since <= 10%)
    assert res["vix_change_percent"] == 8.33
    assert res["vix_shock"] is False
    assert res["shock_level"] == "None"
    assert res["volatility_regime"] == "Low / Normal"
    assert res["market_risk"] == "Normal"
    assert res["trading_environment"] == "Balanced Environment"
    # percentile over 252 days: sorted has 126 of 12.0 and 126 of 13.0. Count less than 13.0 is 126.
    # 126 / 252 * 100 = 50.0 percentile
    assert res["vix_percentile"] == 50.0
    assert "details" in res
    assert res["details"]["sma_5"] == 12.6
    assert res["details"]["high_52w"] == 13.0
    assert res["details"]["low_52w"] == 12.0


@patch("vix_engine.vix_analytics.fetch_yahoo_chart_data")
def test_calculate_vix_analytics_extreme_shock(mock_fetch):
    # Setup mock data for VIX Extreme Shock
    def side_effect(ticker, range_val):
        if ticker == "^INDIAVIX":
            closes = [14.0] * 250 + [15.0, 20.0]  # last element 20.0, prev 15.0. Change is 33.33%
            return {
                "timestamp": [1700000000 + i * 86400 for i in range(252)],
                "indicators": {
                    "quote": [{"close": closes}]
                }
            }
        return {}

    mock_fetch.side_effect = side_effect

    res = calculate_vix_analytics()
    assert res["current_vix"] == 20.0
    assert res["previous_vix"] == 15.0
    assert res["vix_change_percent"] == 33.33
    assert res["vix_shock"] is True
    assert res["shock_level"] == "Extreme"
    # 20.0 > 19.0 is High Volatility / Extreme Volatility percentile
    assert res["volatility_regime"] == "Extreme / Panic"
    assert res["trading_environment"] == "Premium Buying Environment"


@patch("vix_engine.vix_analytics.fetch_yahoo_chart_data")
def test_calculate_vix_analytics_fallback(mock_fetch):
    # Fetch returns empty dict (simulates network/API issue)
    mock_fetch.return_value = {}

    res = calculate_vix_analytics()
    fallback = get_vix_fallback_data()
    assert res["current_vix"] == fallback["current_vix"]
    assert res["vix_percentile"] == fallback["vix_percentile"]
    assert res["vix_shock"] == fallback["vix_shock"]
    assert res["trading_environment"] == fallback["trading_environment"]


def test_vix_analytics_endpoint():
    # Test FastAPI Client request
    response = client.get("/vix-analytics")
    assert response.status_code == 200
    data = response.json()
    assert "current_vix" in data
    assert "vix_percentile" in data
    assert "vix_shock" in data
    assert "trading_environment" in data
    assert "details" in data
    assert "correlation_nifty_vix" in data["details"]
    assert "correlation_banknifty_vix" in data["details"]


@patch("vix_engine.vix_analytics.calculate_vix_analytics")
def test_vix_analytics_caching(mock_calc):
    from vix_engine.vix_analytics import _cache
    _cache.clear()  # Ensure cache is empty for this test
    
    # Setup mock calc returns
    mock_calc.return_value = {"dummy": "value"}
    
    # First call will invoke calculation
    val1 = get_vix_analytics()
    # Second call should return from cache without invoking calculate again
    val2 = get_vix_analytics()
    
    assert val1 == val2
    assert mock_calc.call_count == 1
