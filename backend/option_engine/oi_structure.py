"""OI Structure Analytics for option chain."""

def analyze_oi_structure(chain: list[dict], atm_strike: float) -> dict:
    """
    Analyzes option chain to determine Option Interest (OI) structure trends:
    - Call Unwinding (CE OI Change < 0 and CE Volume high)
    - Put Unwinding (PE OI Change < 0 and PE Volume high)
    - Short Covering (CE OI decreasing near ATM)
    - Long Buildup (PE OI increasing near ATM)
    
    Returns:
        dict: {
            "call_unwinding": "Strong"|"Moderate"|"Weak",
            "put_unwinding": "Strong"|"Moderate"|"Weak",
            "short_covering": "Strong"|"Moderate"|"Weak",
            "long_buildup": "Strong"|"Moderate"|"Weak"
        }
    """
    default_res = {
        "call_unwinding": "Weak",
        "put_unwinding": "Weak",
        "short_covering": "Weak",
        "long_buildup": "Weak"
    }

    if not chain or atm_strike <= 0:
        return default_res

    try:
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

        # --- 1. Call Unwinding (CE OI Change < 0 and CE Volume high) ---
        # Look at the whole chain
        ce_unwinding_strikes = [r for r in chain if int(r.get("call", {}).get("oiChange") or 0) < 0]
        call_unwinding_strength = "Weak"
        if ce_unwinding_strikes:
            max_ce_decrease = max((abs(int(r.get("call", {}).get("oiChange") or 0)) for r in ce_unwinding_strikes), default=0)
            max_ce_vol = max((int(r.get("call", {}).get("volume") or 0) for r in chain), default=0)
            
            best_cu_score = -1.0
            for r in ce_unwinding_strikes:
                ce_oich_dec = abs(int(r.get("call", {}).get("oiChange") or 0))
                ce_vol = int(r.get("call", {}).get("volume") or 0)
                
                oich_score = (ce_oich_dec / max_ce_decrease) if max_ce_decrease > 0 else 0.0
                vol_score = (ce_vol / max_ce_vol) if max_ce_vol > 0 else 0.0
                score = 0.6 * oich_score + 0.4 * vol_score
                
                if score > best_cu_score:
                    best_cu_score = score
            
            if best_cu_score >= 0.75:
                call_unwinding_strength = "Strong"
            elif best_cu_score >= 0.45:
                call_unwinding_strength = "Moderate"

        # --- 2. Put Unwinding (PE OI Change < 0 and PE Volume high) ---
        # Look at the whole chain
        pe_unwinding_strikes = [r for r in chain if int(r.get("put", {}).get("oiChange") or 0) < 0]
        put_unwinding_strength = "Weak"
        if pe_unwinding_strikes:
            max_pe_decrease = max((abs(int(r.get("put", {}).get("oiChange") or 0)) for r in pe_unwinding_strikes), default=0)
            max_pe_vol = max((int(r.get("put", {}).get("volume") or 0) for r in chain), default=0)
            
            best_pu_score = -1.0
            for r in pe_unwinding_strikes:
                pe_oich_dec = abs(int(r.get("put", {}).get("oiChange") or 0))
                pe_vol = int(r.get("put", {}).get("volume") or 0)
                
                oich_score = (pe_oich_dec / max_pe_decrease) if max_pe_decrease > 0 else 0.0
                vol_score = (pe_vol / max_pe_vol) if max_pe_vol > 0 else 0.0
                score = 0.6 * oich_score + 0.4 * vol_score
                
                if score > best_pu_score:
                    best_pu_score = score
            
            if best_pu_score >= 0.75:
                put_unwinding_strength = "Strong"
            elif best_pu_score >= 0.45:
                put_unwinding_strength = "Moderate"

        # --- 3. Short Covering (CE OI decreasing near ATM) ---
        # Look at near_atm region
        short_covering_strikes = [r for r in near_atm if int(r.get("call", {}).get("oiChange") or 0) < 0]
        short_covering_strength = "Weak"
        if short_covering_strikes:
            max_sc_decrease = max((abs(int(r.get("call", {}).get("oiChange") or 0)) for r in short_covering_strikes), default=0)
            max_sc_vol = max((int(r.get("call", {}).get("volume") or 0) for r in near_atm), default=0)
            
            best_sc_score = -1.0
            for r in short_covering_strikes:
                ce_oich_dec = abs(int(r.get("call", {}).get("oiChange") or 0))
                ce_vol = int(r.get("call", {}).get("volume") or 0)
                
                oich_score = (ce_oich_dec / max_sc_decrease) if max_sc_decrease > 0 else 0.0
                vol_score = (ce_vol / max_sc_vol) if max_sc_vol > 0 else 0.0
                score = 0.6 * oich_score + 0.4 * vol_score
                
                if score > best_sc_score:
                    best_sc_score = score
            
            if best_sc_score >= 0.75:
                short_covering_strength = "Strong"
            elif best_sc_score >= 0.45:
                short_covering_strength = "Moderate"

        # --- 4. Long Buildup (PE OI increasing near ATM) ---
        # Look at near_atm region
        long_buildup_strikes = [r for r in near_atm if int(r.get("put", {}).get("oiChange") or 0) > 0]
        long_buildup_strength = "Weak"
        if long_buildup_strikes:
            max_lb_increase = max((int(r.get("put", {}).get("oiChange") or 0) for r in long_buildup_strikes), default=0)
            max_lb_vol = max((int(r.get("put", {}).get("volume") or 0) for r in near_atm), default=0)
            
            best_lb_score = -1.0
            for r in long_buildup_strikes:
                pe_oich_inc = int(r.get("put", {}).get("oiChange") or 0)
                pe_vol = int(r.get("put", {}).get("volume") or 0)
                
                oich_score = (pe_oich_inc / max_lb_increase) if max_lb_increase > 0 else 0.0
                vol_score = (pe_vol / max_lb_vol) if max_lb_vol > 0 else 0.0
                score = 0.6 * oich_score + 0.4 * vol_score
                
                if score > best_lb_score:
                    best_lb_score = score
            
            if best_lb_score >= 0.75:
                long_buildup_strength = "Strong"
            elif best_lb_score >= 0.45:
                long_buildup_strength = "Moderate"

        return {
            "call_unwinding": call_unwinding_strength,
            "put_unwinding": put_unwinding_strength,
            "short_covering": short_covering_strength,
            "long_buildup": long_buildup_strength
        }

    except Exception:
        # Fallback to default on any structural mismatch or parsing error
        return default_res
