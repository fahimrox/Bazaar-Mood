import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from smart_money_engine.flow_engine import calculate_smart_money_flow

client = TestClient(app)

@pytest.fixture
def base_mocks():
    with patch("futures_engine.futures_analytics.calculate_futures_analytics") as mock_futures, \
         patch("option_engine.router.get_option_chain") as mock_option_chain, \
         patch("data_engine.router.get_market_structure") as mock_structure, \
         patch("data_engine.router.get_market_breadth") as mock_breadth, \
         patch("sector_engine.router.get_sector_strength") as mock_sector, \
         patch("smart_money_engine.flow_engine.get_vix_analytics") as mock_vix:
         
        yield {
            "futures": mock_futures,
            "options": mock_option_chain,
            "structure": mock_structure,
            "breadth": mock_breadth,
            "sector": mock_sector,
            "vix": mock_vix
        }


def test_bullish_accumulation(base_mocks):
    # Setup mocks for Bullish Accumulation
    base_mocks["futures"].return_value = {
        "institutional_flow": "Mild Buying",
        "futures_signals": [
            {"symbol": "NIFTY", "futures_structure": "Long Buildup", "smart_money_score": 60.0}
        ]
    }
    # To get Bullish Accumulation rather than Short Covering Rally, call_unwinding must be Weak
    base_mocks["options"].return_value = {
        "pcr": 1.4,
        "maxPain": 24000.0,
        "spot": 24100.0,
        "call_unwinding": "Weak",
        "put_unwinding": "Weak",
        "short_covering": "Weak",
        "long_buildup": "Strong"
    }
    base_mocks["structure"].return_value = {
        "classification": "Bullish",
        "state": "Rallying / Expansion"
    }
    base_mocks["breadth"].return_value = {
        "ad_ratio": 2.2,
        "breadth_status": "Bullish"
    }
    base_mocks["sector"].return_value = [
        {"sector": "IT", "strength": "Outperforming"}
    ] * 5
    base_mocks["vix"].return_value = {"current_vix": 11.0}

    res = calculate_smart_money_flow("NIFTY")
    assert res["smart_money_flow"] == "Bullish Accumulation"
    assert res["smart_money_score"] >= 65.0
    assert res["institutional_bias"] == "Aggressive Bullish"
    assert res["market_regime"] == "Low Volatility"
    assert "component_scores" in res
    assert res["component_scores"]["breadth"] == 100.0


def test_bearish_distribution(base_mocks):
    # Setup mocks for Bearish Distribution
    base_mocks["futures"].return_value = {
        "institutional_flow": "Mild Selling",
        "futures_signals": [
            {"symbol": "NIFTY", "futures_structure": "Short Buildup", "smart_money_score": -60.0}
        ]
    }
    # To get Bearish Distribution rather than Profit Booking, put_unwinding must be Weak
    base_mocks["options"].return_value = {
        "pcr": 0.6,
        "maxPain": 24000.0,
        "spot": 23900.0,
        "call_unwinding": "Weak",
        "put_unwinding": "Weak",
        "short_covering": "Weak",
        "long_buildup": "Weak"
    }
    base_mocks["structure"].return_value = {
        "classification": "Bearish",
        "state": "Sell-off"
    }
    base_mocks["breadth"].return_value = {
        "ad_ratio": 0.4,
        "breadth_status": "Bearish"
    }
    base_mocks["sector"].return_value = [
        {"sector": "IT", "strength": "Underperforming"}
    ] * 5
    base_mocks["vix"].return_value = {"current_vix": 14.0}

    res = calculate_smart_money_flow("NIFTY")
    assert res["smart_money_flow"] == "Bearish Distribution"
    assert res["smart_money_score"] <= 35.0
    assert res["institutional_bias"] == "Aggressive Bearish"
    assert res["market_regime"] == "Trending Bearish"


def test_short_covering_rally(base_mocks):
    # Setup mocks for Short Covering Rally (Price up, OI down in Futures)
    base_mocks["futures"].return_value = {
        "institutional_flow": "Neutral",
        "futures_signals": [
            {"symbol": "NIFTY", "futures_structure": "Short Covering", "smart_money_score": 40.0}
        ]
    }
    # Set PCR to 1.1 so options_score becomes +50, pushing institutional_bias to Bullish (average raw >= 15.0)
    base_mocks["options"].return_value = {
        "pcr": 1.1,
        "maxPain": 24000.0,
        "spot": 24050.0,
        "call_unwinding": "Strong",
        "put_unwinding": "Weak",
        "short_covering": "Strong",
        "long_buildup": "Weak"
    }
    base_mocks["structure"].return_value = {
        "classification": "Neutral",
        "state": "Consolidation"
    }
    base_mocks["breadth"].return_value = {
        "ad_ratio": 1.1,
        "breadth_status": "Neutral"
    }
    base_mocks["sector"].return_value = []
    base_mocks["vix"].return_value = {"current_vix": 13.0}

    res = calculate_smart_money_flow("NIFTY")
    assert res["smart_money_flow"] == "Short Covering Rally"
    assert res["institutional_bias"] == "Bullish"


def test_profit_booking(base_mocks):
    # Setup mocks for Profit Booking (Price down, OI down in Futures)
    base_mocks["futures"].return_value = {
        "institutional_flow": "Neutral",
        "futures_signals": [
            {"symbol": "NIFTY", "futures_structure": "Long Unwinding", "smart_money_score": -40.0}
        ]
    }
    # Set PCR to 0.7 so options_score becomes -100, pushing institutional_bias to Bearish (average raw <= -15)
    base_mocks["options"].return_value = {
        "pcr": 0.7,
        "maxPain": 24000.0,
        "spot": 23980.0,
        "call_unwinding": "Weak",
        "put_unwinding": "Strong",
        "short_covering": "Weak",
        "long_buildup": "Weak"
    }
    base_mocks["structure"].return_value = {
        "classification": "Neutral",
        "state": "Consolidation"
    }
    base_mocks["breadth"].return_value = {
        "ad_ratio": 0.9,
        "breadth_status": "Neutral"
    }
    base_mocks["sector"].return_value = []
    base_mocks["vix"].return_value = {"current_vix": 12.0}

    res = calculate_smart_money_flow("NIFTY")
    assert res["smart_money_flow"] == "Profit Booking"
    assert res["institutional_bias"] == "Bearish"


def test_neutral_flow(base_mocks):
    # Setup mocks for Neutral flow
    # Set PCR to 0.9 so options_score is -20, and set futures_score to 20.0. Net average raw becomes exactly 0.0.
    base_mocks["futures"].return_value = {
        "institutional_flow": "Neutral",
        "futures_signals": [
            {"symbol": "NIFTY", "futures_structure": "Neutral", "smart_money_score": 20.0}
        ]
    }
    base_mocks["options"].return_value = {
        "pcr": 0.9,
        "maxPain": 24000.0,
        "spot": 24000.0,
        "call_unwinding": "Weak",
        "put_unwinding": "Weak",
        "short_covering": "Weak",
        "long_buildup": "Weak"
    }
    base_mocks["structure"].return_value = {
        "classification": "Neutral",
        "state": "Consolidation"
    }
    base_mocks["breadth"].return_value = {
        "ad_ratio": 1.0,
        "breadth_status": "Neutral"
    }
    base_mocks["sector"].return_value = []
    base_mocks["vix"].return_value = {"current_vix": 13.0}

    res = calculate_smart_money_flow("NIFTY")
    assert res["smart_money_flow"] == "Neutral"
    assert res["smart_money_score"] == 50.0
    assert res["institutional_bias"] == "Neutral"


def test_smart_money_flow_endpoint():
    response = client.get("/smart-money-flow?symbol=NIFTY")
    assert response.status_code == 200
    data = response.json()
    assert "smart_money_flow" in data
    assert "smart_money_score" in data
    assert "institutional_bias" in data
    assert "component_scores" in data
    assert "factors" in data
