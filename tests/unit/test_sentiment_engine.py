import pytest
from unittest.mock import patch, MagicMock
from sentiment_engine.market_sentiment_v2 import calculate_sentiment_v2, fetch_india_vix
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@patch("urllib.request.urlopen")
def test_fetch_india_vix_success(mock_urlopen):
    # Mock successful response from Yahoo Finance for VIX
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"chart": {"result": [{"meta": {"regularMarketPrice": 14.5}}]}}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    vix = fetch_india_vix()
    assert vix == 14.5


@patch("urllib.request.urlopen")
def test_fetch_india_vix_failure(mock_urlopen):
    # Mock failure returning safe default
    mock_urlopen.side_effect = Exception("HTTP Error")
    vix = fetch_india_vix()
    assert vix == 15.0


@patch("data_engine.constituent_data.get_constituent_data")
@patch("option_engine.router.get_option_chain")
@patch("data_engine.router.get_market_structure")
@patch("sector_engine.router.get_sector_strength")
@patch("sentiment_engine.market_sentiment_v2.get_vix_analytics")
def test_calculate_sentiment_v2_bullish(
    mock_vix, mock_sector, mock_structure, mock_option_chain, mock_constituents
):
    # Mock Nifty constituent data (28 advances, 21 declines, 1 unchanged)
    mock_constituents.return_value = [
        {"symbol": "SBIN", "change_percent": 1.5, "sector": "Financial Services"},
        {"symbol": "INFY", "change_percent": 2.0, "sector": "IT"},
    ] * 14 + [
        {"symbol": "TCS", "change_percent": -1.2, "sector": "IT"},
    ] * 21 + [
        {"symbol": "HDFC", "change_percent": 0.0, "sector": "Financial Services"}
    ]

    # Mock Option Chain
    mock_option_chain.return_value = {
        "pcr": 1.4,
        "maxPain": 24000.0,
        "spot": 24100.0,
        "call_unwinding": "Strong",
        "put_unwinding": "Weak",
        "short_covering": "Strong",
        "long_buildup": "Strong",
        "atm_strike": 24100.0,
    }

    # Mock Market Structure
    mock_structure.return_value = {
        "classification": "Bullish",
        "state": "Rallying / Expansion",
    }

    # Mock Sector Strength
    mock_sector.return_value = [
        {"sector": "IT", "strength": "Outperforming", "pct": 1.5},
        {"sector": "Financial Services", "strength": "Strong", "pct": 1.2},
        {"sector": "Metals", "strength": "Weak", "pct": -0.5},
    ]

    # Mock India VIX (Low Volatility)
    mock_vix.return_value = {
        "current_vix": 11.0,
        "vix_percentile": 10.0,
        "vix_shock": False,
        "volatility_regime": "Complacency / Extremely Low",
        "market_risk": "Low",
        "trading_environment": "Premium Selling Environment"
    }

    sentiment = calculate_sentiment_v2("NIFTY")
    
    assert sentiment["market_sentiment"] in ["Bullish", "Strong Bullish"]
    assert sentiment["market_regime"] == "Low Volatility"
    assert "factor_scores" in sentiment
    assert sentiment["factor_scores"]["vix"] == 0.5
    assert sentiment["factor_scores"]["oi_structure"] > 0
    assert sentiment["bias"] == sentiment["market_sentiment"]
    assert sentiment["signal"] == "BUY"


def test_sentiment_endpoints_integration():
    # Test through FastAPI Client
    response = client.get("/sentiment?symbol=NIFTY")
    assert response.status_code == 200
    data = response.json()
    assert "market_sentiment" in data
    assert "factor_scores" in data
    assert "bias" in data

    response_rec = client.get("/trade-recommendation?symbol=NIFTY")
    assert response_rec.status_code == 200
    data_rec = response_rec.json()
    assert "action" in data_rec
    assert "entry" in data_rec
    assert "target" in data_rec
    assert "stopLoss" in data_rec
