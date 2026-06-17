"""Call and Put Writing Detection for option chain."""

def analyze_writing(chain: list[dict], atm_strike: float) -> dict:
    """
    Analyzes option chain to determine Call Writing and Put Writing strength.
    """
    res = {
        "call_writing": "Weak",
        "call_writing_strike": 0.0,
        "put_writing": "Weak",
        "put_writing_strike": 0.0
    }

    if not chain or atm_strike <= 0:
        return res

    # Find the index of the ATM strike in the sorted chain
    atm_idx = -1
    for idx, row in enumerate(chain):
        if row.get("strike") == atm_strike:
            atm_idx = idx
            break

    if atm_idx == -1:
        # Fallback: find closest index
        closest_diff = float("inf")
        for idx, row in enumerate(chain):
            diff = abs(row.get("strike", 0.0) - atm_strike)
            if diff < closest_diff:
                closest_diff = diff
                atm_idx = idx

    # Define Near ATM as ±5 strikes around the ATM strike
    start_idx = max(0, atm_idx - 5)
    end_idx = min(len(chain), atm_idx + 6)
    near_atm = chain[start_idx:end_idx]

    if not near_atm:
        return res

    # ── Call Writing ──
    # Safe dictionary access with .get()
    max_ce_oich = max((max(0, int(r.get("call", {}).get("oiChange") or 0)) for r in near_atm), default=0)
    max_ce_vol = max((int(r.get("call", {}).get("volume") or 0) for r in near_atm), default=0)

    best_ce_score = -1.0
    for r in near_atm:
        ce_oich = max(0, int(r.get("call", {}).get("oiChange") or 0))
        ce_vol = int(r.get("call", {}).get("volume") or 0)
        
        oich_score = (ce_oich / max_ce_oich) if max_ce_oich > 0 else 0.0
        vol_score = (ce_vol / max_ce_vol) if max_ce_vol > 0 else 0.0
        score = 0.6 * oich_score + 0.4 * vol_score
        
        if score > best_ce_score:
            best_ce_score = score
            res["call_writing_strike"] = float(r.get("strike") or 0.0)

    if best_ce_score >= 0.75:
        res["call_writing"] = "Strong"
    elif best_ce_score >= 0.45:
        res["call_writing"] = "Moderate"

    # ── Put Writing ──
    max_pe_oich = max((max(0, int(r.get("put", {}).get("oiChange") or 0)) for r in near_atm), default=0)
    max_pe_vol = max((int(r.get("put", {}).get("volume") or 0) for r in near_atm), default=0)

    best_pe_score = -1.0
    for r in near_atm:
        pe_oich = max(0, int(r.get("put", {}).get("oiChange") or 0))
        pe_vol = int(r.get("put", {}).get("volume") or 0)
        
        oich_score = (pe_oich / max_pe_oich) if max_pe_oich > 0 else 0.0
        vol_score = (pe_vol / max_pe_vol) if max_pe_vol > 0 else 0.0
        score = 0.6 * oich_score + 0.4 * vol_score
        
        if score > best_pe_score:
            best_pe_score = score
            res["put_writing_strike"] = float(r.get("strike") or 0.0)

    if best_pe_score >= 0.75:
        res["put_writing"] = "Strong"
    elif best_pe_score >= 0.45:
        res["put_writing"] = "Moderate"

    return res
