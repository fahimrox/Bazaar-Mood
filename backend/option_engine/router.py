import math
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Query
from option_engine.fyers_client import FyersClient
from option_engine.strike_utils import get_atm_strike
from option_engine.support_resistance import calculate_support_resistance

router = APIRouter(tags=["Option Engine"])
fyers_client = FyersClient()

# ─────────────────────────────────────────────────────────────────────────────
# Fyers optionsChain live response structure (verified 2026-06-17):
#
#   response["data"] = {
#       "callOi": int,
#       "putOi":  int,
#       "expiryData": [
#           {"date": "23-06-2026", "expiry": "1782208800", "expiry_flag": "W"},
#           ...
#       ],
#       "indiavixData": { "ltp": float, ... },
#       "optionsChain": [
#           # Row 0 — underlying index (strike_price == -1, option_type == "")
#           { "ltp": 24085.7, "strike_price": -1, "option_type": "", ... },
#
#           # Rows 1+ — individual CE / PE contracts for the requested expiry
#           {
#               "strike_price": 24000,
#               "option_type":  "CE" | "PE",
#               "ltp":    float,   # last traded price
#               "ltpch":  float,   # price change
#               "oi":     int,     # open interest
#               "oich":   int,     # OI change
#               "oichp":  float,   # OI change %
#               "volume": int,
#               "prev_oi": int,
#               "ask":    float,
#               "bid":    float,
#               "greeks": { "delta": float, "gamma": float,
#                           "theta": float, "vega": float, "iv": float },
#           },
#           ...
#       ]
#   }
#
#   Key facts:
#   - Expiry filter is applied server-side by Fyers via the "timestamp" param.
#     When timestamp="" → nearest expiry is returned.
#   - There is NO per-row expiry field. Use expiryData[0] for display.
#   - CE and PE for the same strike are separate flat rows (not nested).
#   - Underlying spot = optionsChain[0].ltp  (where strike_price == -1)
# ─────────────────────────────────────────────────────────────────────────────


# ── Helpers ──────────────────────────────────────────────────────────────────

def _spot_from_chain(options: list) -> float:
    """Extract underlying spot price from the index row (strike_price == -1)."""
    for row in options:
        if row.get("strike_price") == -1:
            return float(row.get("ltp") or row.get("fp") or 0.0)
    return 0.0


def _days_to_expiry_from_timestamp(expiry_ts_str: str) -> float:
    """Convert Fyers Unix timestamp string (seconds) to calendar days from today."""
    try:
        expiry_date = datetime.fromtimestamp(int(expiry_ts_str)).date()
        return max(0.0, float((expiry_date - date.today()).days))
    except Exception:
        return 0.0


def _calculate_delta(spot: float, strike: float, dte: float,
                     iv: float, is_call: bool) -> float:
    """Black-Scholes N(d1) delta approximation."""
    if dte <= 0 or iv <= 0 or spot <= 0 or strike <= 0:
        return 0.5 if is_call else -0.5
    t = dte / 365.0
    r = 0.07  # 7 % risk-free rate (NSE standard)
    try:
        d1 = (math.log(spot / strike) + (r + (iv ** 2) / 2.0) * t) / (iv * math.sqrt(t))
        nd1 = 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
        return float(nd1) if is_call else float(nd1 - 1.0)
    except Exception:
        return 0.5 if is_call else -0.5


def _normalize_contract(row: dict, spot: float, dte: float, is_call: bool) -> dict:
    """
    Map a single Fyers contract row to the frontend-expected contract dict.
    Confirmed live field names: oi, oich, volume, ltp, ltpch, greeks.delta, greeks.iv
    """
    oi     = int(row.get("oi") or 0)
    oich   = int(row.get("oich") or 0)
    volume = int(row.get("volume") or 0)
    price  = float(row.get("ltp") or 0.0)
    strike = float(row.get("strike_price") or 0.0)

    greeks = row.get("greeks") or {}
    iv_raw = greeks.get("iv") or 0.15        # already in % form from Fyers (e.g. 12.04)
    iv     = iv_raw / 100.0 if iv_raw > 1.0 else iv_raw  # normalise to 0–1

    delta = greeks.get("delta")
    if delta is None:
        delta = _calculate_delta(spot, strike, dte, iv, is_call)

    return {
        "oi":       oi,
        "oiChange": oich,
        "volume":   volume,
        "price":    price,
        "delta":    float(delta),
    }


def _calculate_pcr(chain: list) -> float:
    total_call_oi = sum(r["call"]["oi"] for r in chain)
    total_put_oi  = sum(r["put"]["oi"]  for r in chain)
    if total_call_oi == 0:
        return 0.0
    return round(total_put_oi / total_call_oi, 2)


def _calculate_max_pain(chain: list) -> float:
    if not chain:
        return 0.0
    strikes = [r["strike"] for r in chain]
    min_pain   = float("inf")
    best_strike = strikes[0]
    for k in strikes:
        pain = sum(
            max(0, k - r["strike"]) * r["call"]["oi"] +
            max(0, r["strike"] - k) * r["put"]["oi"]
            for r in chain
        )
        if pain < min_pain:
            min_pain    = pain
            best_strike = k
    return float(best_strike)


def _expiry_timestamp_for(expiry_selector: str, expiry_data: list) -> str:
    """
    Choose a Fyers expiry timestamp string based on the user's selector.

    expiry_selector: "weekly" | "monthly" | bare date string "23-06-2026"
    expiry_data: list of {"date": "DD-MM-YYYY", "expiry": "unix_ts", "expiry_flag": "W"|"M"}

    Returns the "expiry" timestamp string to pass back to Fyers, or "" for nearest.
    """
    if not expiry_data:
        return ""

    if expiry_selector in ("weekly", ""):
        # Nearest weekly (flag "W"), else just nearest overall
        for ed in expiry_data:
            if ed.get("expiry_flag") == "W":
                return ed["expiry"]
        return expiry_data[0]["expiry"]

    if expiry_selector == "monthly":
        # Nearest monthly
        for ed in expiry_data:
            if ed.get("expiry_flag") == "M":
                return ed["expiry"]
        return expiry_data[-1]["expiry"]

    # Treat as a literal date string "DD-MM-YYYY" or timestamp
    for ed in expiry_data:
        if ed.get("date") == expiry_selector or ed.get("expiry") == expiry_selector:
            return ed["expiry"]

    return expiry_data[0]["expiry"]


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/option-chain")
def get_option_chain(
    symbol: str = Query("NIFTY"),
    expiry: str = Query("weekly"),
):
    """
    Returns a normalised option chain for the given symbol and expiry.

    Step 1 — fetch nearest expiry to get expiryData list.
    Step 2 — re-fetch with the exact expiry timestamp for the requested expiry.
    Step 3 — parse the flat optionsChain rows into strike-grouped dicts.
    """
    # ── Step 1: get expiryData from a quick nearest-expiry fetch ──────────
    raw_nearest = fyers_client.fetch_raw_option_chain(symbol, timestamp="")
    expiry_data = raw_nearest.get("expiryData") or []
    if not expiry_data:
        raise HTTPException(status_code=503, detail="Fyers returned no expiry data.")

    # ── Step 2: resolve the requested expiry → Fyers timestamp ────────────
    target_ts = _expiry_timestamp_for(expiry, expiry_data)

    # If target_ts matches the nearest expiry we already fetched, reuse it
    nearest_ts = expiry_data[0]["expiry"] if expiry_data else ""
    if target_ts == nearest_ts or target_ts == "":
        raw = raw_nearest
    else:
        raw = fyers_client.fetch_raw_option_chain(symbol, timestamp=target_ts)

    options_list = raw.get("optionsChain") or []
    if not options_list:
        raise HTTPException(status_code=503, detail="Empty option chain returned from Fyers.")

    # ── Step 3: extract spot from index row (strike_price == -1) ──────────
    spot = _spot_from_chain(options_list)

    # Find the matching expiryData entry for DTE calculation
    matched_expiry = next(
        (ed for ed in expiry_data if ed["expiry"] == target_ts),
        expiry_data[0]
    )
    dte = _days_to_expiry_from_timestamp(matched_expiry["expiry"])
    expiry_date_display = matched_expiry.get("date", "")

    # ── Step 4: group flat rows by strike ─────────────────────────────────
    # Skip the index row (strike_price == -1)
    strike_map: dict[float, dict] = {}
    for row in options_list:
        sp = row.get("strike_price")
        if sp is None or sp == -1:
            continue
        strike = float(sp)
        opt_type = row.get("option_type", "").upper()
        if opt_type not in ("CE", "PE"):
            continue

        is_call = (opt_type == "CE")
        contract = _normalize_contract(row, spot, dte, is_call)

        if strike not in strike_map:
            strike_map[strike] = {
                "strike": strike,
                "is_atm": False,
                "call": {"oi": 0, "oiChange": 0, "volume": 0, "price": 0.0, "delta": 0.5},
                "put":  {"oi": 0, "oiChange": 0, "volume": 0, "price": 0.0, "delta": -0.5},
            }

        if is_call:
            strike_map[strike]["call"] = contract
        else:
            strike_map[strike]["put"] = contract

    if not strike_map:
        raise HTTPException(
            status_code=503,
            detail="No valid CE/PE rows found in option chain. Check symbol and expiry."
        )

    # ── Step 5: sort + mark ATM ───────────────────────────────────────────
    chain = sorted(strike_map.values(), key=lambda x: x["strike"])

    atm_strike = 0.0
    if chain and spot > 0:
        strikes = [r["strike"] for r in chain]
        atm_strike = get_atm_strike(spot, strikes)
        for row in chain:
            row["is_atm"] = (row["strike"] == atm_strike)

    pcr       = _calculate_pcr(chain)
    max_pain  = _calculate_max_pain(chain)

    sr_data = calculate_support_resistance(chain, atm_strike)

    return {
        "symbol":                symbol.upper(),
        "spot":                  float(spot),
        "expiry":                expiry_date_display,
        "pcr":                   float(pcr),
        "maxPain":               float(max_pain),
        "atm_strike":            float(atm_strike),
        "support_1":             float(sr_data["support_1"]),
        "support_confidence":    float(sr_data["support_confidence"]),
        "resistance_1":          float(sr_data["resistance_1"]),
        "resistance_confidence": float(sr_data["resistance_confidence"]),
        "chain":                 chain,
    }


@router.get("/oi-activity")
def get_oi_activity(symbol: str = Query("NIFTY")):
    """
    Returns the top-10 OI build-up / unwinding activity for the nearest expiry.
    Uses the flat optionsChain rows directly — no grouping needed.
    """
    raw = fyers_client.fetch_raw_option_chain(symbol, timestamp="")
    options_list = raw.get("optionsChain") or []
    if not options_list:
        raise HTTPException(status_code=503, detail="Empty option chain returned from Fyers.")

    activity = []
    for row in options_list:
        sp = row.get("strike_price")
        if sp is None or sp == -1:
            continue
        opt_type = row.get("option_type", "").upper()
        if opt_type not in ("CE", "PE"):
            continue

        oi_change  = int(row.get("oich") or 0)
        price      = float(row.get("ltp") or 0.0)
        price_chg  = float(row.get("ltpch") or 0.0)

        if oi_change == 0:
            continue

        # Four-way buildup classification
        if price_chg >= 0 and oi_change >= 0:
            buildup, tone = "Long Buildup", "bullish"
        elif price_chg < 0 and oi_change >= 0:
            buildup, tone = "Short Buildup", "bearish"
        elif price_chg < 0 and oi_change < 0:
            buildup, tone = "Long Unwinding", "bearish"
        else:
            buildup, tone = "Short Covering", "bullish"

        activity.append({
            "strike":    f"{int(sp)} {opt_type}",
            "type":      buildup,
            "oiChange":  oi_change,
            "tone":      tone,
            "absChange": abs(oi_change),
        })

    activity.sort(key=lambda x: x["absChange"], reverse=True)

    return [
        {
            "strike":   a["strike"],
            "type":     a["type"],
            "oiChange": f"{'+' if a['oiChange'] >= 0 else ''}{a['oiChange']:,}",
            "tone":     a["tone"],
        }
        for a in activity[:10]
    ]
