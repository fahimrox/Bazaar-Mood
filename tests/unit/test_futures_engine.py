import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from futures_engine.futures_analytics import (
    get_current_futures_symbol,
    analyze_futures_structure,
    calculate_futures_analytics
)

client = TestClient(app)

def test_get_current_futures_symbol_with_date():
    # Test with exact monthly expiry date
    sym = get_current_futures_symbol("NIFTY", "25-06-2026")
    assert sym == "NSE:NIFTY26JUNFUT"

    sym_bank = get_current_futures_symbol("BANKNIFTY", "30-07-2026")
    assert sym_bank == "NSE:BANKNIFTY26JULFUT"

    sym_mid = get_current_futures_symbol("MIDCPNIFTY", "24-12-2026")
    assert sym_mid == "NSE:MIDCPNIFTY26DECFUT"


def test_get_current_futures_symbol_fallback():
    # Test fallback formatting
    sym = get_current_futures_symbol("NIFTY")
    assert sym.startswith("NSE:NIFTY")
    assert sym.endswith("FUT")


def test_analyze_futures_structure():
    # Long Buildup: price up, oi up
    struct, sm_score, strength, bias = analyze_futures_structure(0.5, 1.2)
    assert struct == "Long Buildup"
    assert sm_score > 50.0
    assert strength == "Strong"
    assert bias == "Bullish"

    # Short Buildup: price down, oi up
    struct, sm_score, strength, bias = analyze_futures_structure(-0.6, 1.5)
    assert struct == "Short Buildup"
    assert sm_score < -50.0
    assert strength == "Strong"
    assert bias == "Bearish"

    # Long Unwinding: price down, oi down
    struct, sm_score, strength, bias = analyze_futures_structure(-0.3, -0.5)
    assert struct == "Long Unwinding"
    assert sm_score < -25.0
    assert strength == "Moderate"
    assert bias == "Bearish"

    # Short Covering: price up, oi down
    struct, sm_score, strength, bias = analyze_futures_structure(0.4, -0.6)
    assert struct == "Short Covering"
    assert sm_score > 25.0
    assert strength == "Moderate"
    assert bias == "Bullish"

    # Neutral: no change
    struct, sm_score, strength, bias = analyze_futures_structure(0.0, 0.0)
    assert struct == "Neutral"
    assert sm_score == 0.0
    assert strength == "Weak"
    assert bias == "Neutral"


@patch("option_engine.fyers_client.FyersClient.fetch_raw_option_chain")
@patch("option_engine.fyers_client.FyersClient.fetch_quotes")
def test_calculate_futures_analytics_success(mock_fetch_quotes, mock_fetch_chain):
    # Mock Option Chain ExpiryData response
    mock_fetch_chain.return_value = {
        "expiryData": [
            {"date": "25-06-2026", "expiry": "1782208800", "expiry_flag": "M"}
        ]
    }

    # Mock Fyers Quotes response for NSE:NIFTY26JUNFUT, NSE:BANKNIFTY26JUNFUT, NSE:MIDCPNIFTY26JUNFUT
    mock_fetch_quotes.return_value = [
        {
            "n": "NSE:NIFTY26JUNFUT",
            "v": {"lp": 24100.0, "chp": 0.45, "oi": 15000000, "oich": 300000}
        },
        {
            "n": "NSE:BANKNIFTY26JUNFUT",
            "v": {"lp": 52000.0, "chp": -0.65, "oi": 4000000, "oich": 100000}
        },
        {
            "n": "NSE:MIDCPNIFTY26JUNFUT",
            "v": {"lp": 12500.0, "chp": 0.25, "oi": 1200000, "oich": -20000}
        }
    ]

    res = calculate_futures_analytics()
    assert "market_bias" in res
    assert "confidence" in res
    assert "institutional_flow" in res
    assert "futures_signals" in res
    assert len(res["futures_signals"]) == 3

    # Check NIFTY (Long Buildup: price positive, oi positive (300000/(15000000-300000) = 2.04%))
    nifty_sig = next(s for s in res["futures_signals"] if s["symbol"] == "NIFTY")
    assert nifty_sig["futures_structure"] == "Long Buildup"
    assert nifty_sig["smart_money_score"] > 50
    assert nifty_sig["bias"] == "Bullish"

    # Check BANKNIFTY (Short Buildup: price negative, oi positive (100000/(4000000-100000) = 2.56%))
    bank_sig = next(s for s in res["futures_signals"] if s["symbol"] == "BANKNIFTY")
    assert bank_sig["futures_structure"] == "Short Buildup"
    assert bank_sig["smart_money_score"] < -50
    assert bank_sig["bias"] == "Bearish"


@patch("option_engine.fyers_client.FyersClient.fetch_raw_option_chain")
@patch("option_engine.fyers_client.FyersClient.fetch_quotes")
@patch("futures_engine.futures_analytics.fetch_index_price_yahoo")
def test_calculate_futures_analytics_fallback(mock_yahoo, mock_fetch_quotes, mock_fetch_chain):
    # Mock Fyers failure
    mock_fetch_chain.side_effect = Exception("Fyers API offline")
    mock_fetch_quotes.side_effect = Exception("Fyers Quotes API offline")

    # Mock Yahoo Finance responses
    mock_yahoo.side_effect = lambda sym: {
        "NIFTY": {"price": 24085.7, "change_pct": 0.45},
        "BANKNIFTY": {"price": 52100.0, "change_pct": -0.55},
        "MIDCPNIFTY": {"price": 12600.0, "change_pct": 0.05}
    }.get(sym, {"price": 0.0, "change_pct": 0.0})

    res = calculate_futures_analytics()
    assert res["market_bias"] == "Neutral"
    assert res["institutional_flow"] in ["Neutral / Mixed", "Mild Buying", "Mild Selling"]
    assert len(res["futures_signals"]) == 3

    nifty_sig = next(s for s in res["futures_signals"] if s["symbol"] == "NIFTY")
    assert nifty_sig["price_change"] == 0.45
    assert nifty_sig["futures_structure"] == "Long Buildup"
    assert nifty_sig["bias"] == "Bullish"


def test_futures_analytics_endpoint():
    # Query FastAPI Client
    response = client.get("/futures-analytics")
    assert response.status_code == 200
    data = response.json()
    assert "market_bias" in data
    assert "confidence" in data
    assert "institutional_flow" in data
    assert "futures_signals" in data
