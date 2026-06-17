"""OI-Based Support & Resistance Engine V2 for option chain."""

def calculate_support_resistance(chain: list[dict], atm_strike: float) -> dict:
    """
    Calculates support and resistance levels based on Open Interest.

    1. Reference strike: atm_strike.
    2. Support Logic:
       - Consider only strikes below ATM (strike < atm_strike).
       - Find strike with highest Put (PE) OI.
       - Return as support_1.
    3. Resistance Logic:
       - Consider only strikes above ATM (strike > atm_strike).
       - Find strike with highest Call (CE) OI.
       - Return as resistance_1.
    4. Confidence Score:
       - Calculate support_confidence based on support strike PE OI relative to the total PE OI below ATM.
       - Calculate resistance_confidence based on resistance strike CE OI relative to the total CE OI above ATM.
       - Return rounded values between 0.0 and 100.0.
    """
    res = {
        "support_1": 0.0,
        "support_confidence": 0.0,
        "resistance_1": 0.0,
        "resistance_confidence": 0.0
    }

    if not chain or atm_strike <= 0:
        return res

    # Support Logic (strikes < atm_strike)
    below_atm = [r for r in chain if r.get("strike", 0.0) < atm_strike]
    if below_atm:
        max_pe_oi = max(int(r["put"]["oi"]) for r in below_atm)
        best_supports = [r for r in below_atm if int(r["put"]["oi"]) == max_pe_oi]
        if best_supports and max_pe_oi > 0:
            # Pick the strike closest to ATM in case of ties
            best_support = max(best_supports, key=lambda r: r["strike"])
            res["support_1"] = float(best_support["strike"])

            total_pe_oi = sum(int(r["put"]["oi"]) for r in below_atm)
            if total_pe_oi > 0:
                res["support_confidence"] = round((float(best_support["put"]["oi"]) / total_pe_oi) * 100.0, 2)

    # Resistance Logic (strikes > atm_strike)
    above_atm = [r for r in chain if r.get("strike", 0.0) > atm_strike]
    if above_atm:
        max_ce_oi = max(int(r["call"]["oi"]) for r in above_atm)
        best_resistances = [r for r in above_atm if int(r["call"]["oi"]) == max_ce_oi]
        if best_resistances and max_ce_oi > 0:
            # Pick the strike closest to ATM in case of ties
            best_resistance = min(best_resistances, key=lambda r: r["strike"])
            res["resistance_1"] = float(best_resistance["strike"])

            total_ce_oi = sum(int(r["call"]["oi"]) for r in above_atm)
            if total_ce_oi > 0:
                res["resistance_confidence"] = round((float(best_resistance["call"]["oi"]) / total_ce_oi) * 100.0, 2)

    return res
