"""Greeks Engine V1 to extract ATM Greeks from the option chain."""

def calculate_atm_greeks(options_list: list, atm_strike: float) -> dict:
    """
    Extracts Greeks (IV, Delta, Gamma, Theta, Vega) for the At-The-Money (ATM) strike.
    Handles missing Greeks by falling back to safe default values.
    """
    res = {
        "strike": float(atm_strike),
        "ce_iv": 0.0,
        "ce_delta": 0.5,
        "ce_gamma": 0.0,
        "ce_theta": 0.0,
        "ce_vega": 0.0,
        "pe_iv": 0.0,
        "pe_delta": -0.5,
        "pe_gamma": 0.0,
        "pe_theta": 0.0,
        "pe_vega": 0.0
    }

    if not options_list or atm_strike <= 0:
        return res

    ce_row = None
    pe_row = None

    for row in options_list:
        sp = row.get("strike_price")
        if sp is None or sp == -1:
            continue
        if float(sp) == atm_strike:
            opt_type = row.get("option_type", "").upper()
            if opt_type == "CE":
                ce_row = row
            elif opt_type == "PE":
                pe_row = row

    if ce_row:
        greeks = ce_row.get("greeks") or {}
        res["ce_iv"] = float(greeks.get("iv") or 0.0)
        res["ce_delta"] = float(greeks.get("delta") if greeks.get("delta") is not None else 0.5)
        res["ce_gamma"] = float(greeks.get("gamma") or 0.0)
        res["ce_theta"] = float(greeks.get("theta") or 0.0)
        res["ce_vega"] = float(greeks.get("vega") or 0.0)

    if pe_row:
        greeks = pe_row.get("greeks") or {}
        res["pe_iv"] = float(greeks.get("iv") or 0.0)
        res["pe_delta"] = float(greeks.get("delta") if greeks.get("delta") is not None else -0.5)
        res["pe_gamma"] = float(greeks.get("gamma") or 0.0)
        res["pe_theta"] = float(greeks.get("theta") or 0.0)
        res["pe_vega"] = float(greeks.get("vega") or 0.0)

    return res
