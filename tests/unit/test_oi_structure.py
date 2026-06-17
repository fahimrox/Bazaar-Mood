import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the logic function and router/app
from option_engine.oi_structure import analyze_oi_structure
from main import app

client = TestClient(app)

# Helper to create basic mock row template
def make_mock_row(strike, ce_oi=1000, ce_oich=0, ce_vol=100, pe_oi=1000, pe_oich=0, pe_vol=100, is_atm=False):
    return {
        "strike": strike,
        "is_atm": is_atm,
        "call": {
            "oi": ce_oi,
            "oiChange": ce_oich,
            "volume": ce_vol,
            "price": 100.0,
            "delta": 0.5
        },
        "put": {
            "oi": pe_oi,
            "oiChange": pe_oich,
            "volume": pe_vol,
            "price": 100.0,
            "delta": -0.5
        }
    }

# 1. Fallbacks on missing or incomplete data
def test_fallback_empty_chain():
    res = analyze_oi_structure([], 24000.0)
    assert res == {
        "call_unwinding": "Weak",
        "put_unwinding": "Weak",
        "short_covering": "Weak",
        "long_buildup": "Weak"
    }

def test_fallback_none_chain():
    res = analyze_oi_structure(None, 24000.0)
    assert res == {
        "call_unwinding": "Weak",
        "put_unwinding": "Weak",
        "short_covering": "Weak",
        "long_buildup": "Weak"
    }

def test_fallback_invalid_atm():
    chain = [make_mock_row(24000)]
    res = analyze_oi_structure(chain, -1)
    assert res == {
        "call_unwinding": "Weak",
        "put_unwinding": "Weak",
        "short_covering": "Weak",
        "long_buildup": "Weak"
    }

def test_fallback_incomplete_rows():
    # Rows missing 'call' or 'put' fields completely
    chain = [
        {"strike": 24000.0, "is_atm": True}
    ]
    res = analyze_oi_structure(chain, 24000.0)
    assert res == {
        "call_unwinding": "Weak",
        "put_unwinding": "Weak",
        "short_covering": "Weak",
        "long_buildup": "Weak"
    }

# 2. Call Unwinding
def test_call_unwinding_strong():
    # Call Unwinding: CE OI Change < 0 and CE Volume high
    # We create a chain where one strike has very high negative CE OI Change and high volume.
    chain = [
        make_mock_row(23800, ce_oich=0, ce_vol=10),
        make_mock_row(23900, ce_oich=-1000, ce_vol=5000),  # Strong unwinding strike
        make_mock_row(24000, ce_oich=10, ce_vol=100, is_atm=True),
        make_mock_row(24100, ce_oich=20, ce_vol=100),
        make_mock_row(24200, ce_oich=0, ce_vol=10)
    ]
    res = analyze_oi_structure(chain, 24000.0)
    assert res["call_unwinding"] == "Strong"

# 3. Put Unwinding
def test_put_unwinding_strong():
    # Put Unwinding: PE OI Change < 0 and PE Volume high
    chain = [
        make_mock_row(23800, pe_oich=0, pe_vol=10),
        make_mock_row(23900, pe_oich=-1000, pe_vol=5000),  # Strong unwinding
        make_mock_row(24000, pe_oich=10, pe_vol=100, is_atm=True),
        make_mock_row(24100, pe_oich=20, pe_vol=100),
        make_mock_row(24200, pe_oich=0, pe_vol=10)
    ]
    res = analyze_oi_structure(chain, 24000.0)
    assert res["put_unwinding"] == "Strong"

# 4. Short Covering (CE OI decreasing near ATM)
def test_short_covering_strong():
    # Short Covering: CE OI Change < 0 near ATM
    chain = [
        make_mock_row(23800, ce_oich=0, ce_vol=10),
        make_mock_row(23900, ce_oich=0, ce_vol=10),
        # ATM region ±5 strikes. Let's make 24000 the ATM strike.
        # ATM-1 (23950) has CE OI decrease:
        make_mock_row(23950, ce_oich=-500, ce_vol=1000),
        make_mock_row(24000, ce_oich=0, ce_vol=10, is_atm=True),
        make_mock_row(24050, ce_oich=0, ce_vol=10),
        make_mock_row(24100, ce_oich=0, ce_vol=10)
    ]
    res = analyze_oi_structure(chain, 24000.0)
    assert res["short_covering"] == "Strong"

# 5. Long Buildup (PE OI increasing near ATM)
def test_long_buildup_strong():
    # Long Buildup: PE OI Change > 0 near ATM
    chain = [
        make_mock_row(23800, pe_oich=0, pe_vol=10),
        make_mock_row(23900, pe_oich=0, pe_vol=10),
        make_mock_row(23950, pe_oich=800, pe_vol=1000),  # PE increase near ATM
        make_mock_row(24000, pe_oich=0, pe_vol=10, is_atm=True),
        make_mock_row(24050, pe_oich=0, pe_vol=10),
        make_mock_row(24100, pe_oich=0, pe_vol=10)
    ]
    res = analyze_oi_structure(chain, 24000.0)
    assert res["long_buildup"] == "Strong"

# 6. Integration Test via /option-chain endpoint
@patch('option_engine.fyers_client.FyersClient.fetch_raw_option_chain')
def test_option_chain_endpoint_integration(mock_fetch):
    # Setup a mock raw response from Fyers Client
    mock_raw_response = {
        "expiryData": [
            {"date": "23-06-2026", "expiry": "1782208800", "expiry_flag": "W"}
        ],
        "optionsChain": [
            # Spot index row
            {
                "strike_price": -1,
                "option_type": "",
                "ltp": 24000.0
            },
            # Contract rows
            {
                "strike_price": 23900,
                "option_type": "CE",
                "ltp": 120.0,
                "ltpch": 5.0,
                "oi": 5000,
                "oich": -100,
                "volume": 2000,
                "greeks": {"delta": 0.6, "gamma": 0.001, "theta": -10.0, "vega": 5.0, "iv": 15.0}
            },
            {
                "strike_price": 23900,
                "option_type": "PE",
                "ltp": 50.0,
                "ltpch": -2.0,
                "oi": 8000,
                "oich": 500,
                "volume": 3000,
                "greeks": {"delta": -0.4, "gamma": 0.001, "theta": -8.0, "vega": 5.0, "iv": 14.5}
            },
            {
                "strike_price": 24000,
                "option_type": "CE",
                "ltp": 70.0,
                "ltpch": 1.0,
                "oi": 10000,
                "oich": 50,
                "volume": 500,
                "greeks": {"delta": 0.5, "gamma": 0.002, "theta": -12.0, "vega": 6.0, "iv": 16.0}
            },
            {
                "strike_price": 24000,
                "option_type": "PE",
                "ltp": 70.0,
                "ltpch": -1.0,
                "oi": 9000,
                "oich": -50,
                "volume": 400,
                "greeks": {"delta": -0.5, "gamma": 0.002, "theta": -11.0, "vega": 6.0, "iv": 15.5}
            }
        ]
    }
    mock_fetch.return_value = mock_raw_response

    response = client.get("/option-chain?symbol=NIFTY&expiry=weekly")
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify existing API response fields remain intact
    assert "symbol" in data
    assert "spot" in data
    assert "expiry" in data
    assert "pcr" in data
    assert "maxPain" in data
    assert "atm_strike" in data
    assert "support_1" in data
    assert "support_confidence" in data
    assert "resistance_1" in data
    assert "resistance_confidence" in data
    assert "call_writing" in data
    assert "call_writing_strike" in data
    assert "put_writing" in data
    assert "put_writing_strike" in data
    assert "market_bias" in data
    assert "confidence_score" in data
    assert "atm_greeks" in data
    assert "trade_signal" in data
    assert "entry" in data
    assert "stop_loss" in data
    assert "target" in data
    assert "trade_confidence" in data
    assert "reason" in data
    assert "chain" in data

    # Verify newly added additive fields are returned correctly
    assert "call_unwinding" in data
    assert "put_unwinding" in data
    assert "short_covering" in data
    assert "long_buildup" in data
    assert "oi_structure" in data
    
    # Check structure values are valid
    assert data["call_unwinding"] in ["Strong", "Moderate", "Weak"]
    assert data["put_unwinding"] in ["Strong", "Moderate", "Weak"]
    assert data["short_covering"] in ["Strong", "Moderate", "Weak"]
    assert data["long_buildup"] in ["Strong", "Moderate", "Weak"]
    
    assert data["oi_structure"] == {
        "call_unwinding": data["call_unwinding"],
        "put_unwinding": data["put_unwinding"],
        "short_covering": data["short_covering"],
        "long_buildup": data["long_buildup"]
    }
