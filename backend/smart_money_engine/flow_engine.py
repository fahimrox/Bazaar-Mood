import logging
import urllib.request
import json
import time

# Configure logger
logger = logging.getLogger("BazaarMood.SmartMoneyFlowEngine")

# Cache configuration
CACHE_TTL = 30  # 30 seconds cache TTL
_cache = {}

from vix_engine.vix_analytics import get_vix_analytics


def calculate_smart_money_flow(symbol: str = "NIFTY") -> dict:
    """
    Core algorithmic calculation to detect institutional flow, smart money score,
    and market regime based on futures, options, OI structure, breadth, and sector rotation.
    """
    symbol_upper = symbol.upper().strip()
    
    # ── 1. Futures Analytics Component ────────────────────────────────────────
    futures_score = 0.0
    futures_desc = "Futures data unavailable."
    futures_structure_val = "Neutral"
    try:
        from futures_engine.futures_analytics import calculate_futures_analytics
        futures_data = calculate_futures_analytics()
        futures_signal = next((s for s in futures_data["futures_signals"] if s["symbol"] == symbol_upper), None)
        if futures_signal:
            futures_score = float(futures_signal["smart_money_score"])
            futures_structure_val = futures_signal["futures_structure"]
            futures_desc = f"Futures is in {futures_structure_val} with Smart Money Score of {futures_score:.1f} (Institutional Flow: {futures_data['institutional_flow']})."
        else:
            futures_desc = "Futures signal for this symbol unavailable."
    except Exception as e:
        logger.warning(f"Futures Analytics fetch failed in Smart Money Flow: {e}. Applying fallbacks.")
        # Fallback using Yahoo Finance Price Change
        try:
            from futures_engine.futures_analytics import fetch_index_price_yahoo
            yahoo_data = fetch_index_price_yahoo(symbol_upper)
            change_pct = yahoo_data["change_pct"]
            if change_pct > 0.15:
                futures_score = 50.0 + min(50.0, 0.8 * 20.0 + change_pct * 10.0)
                futures_structure_val = "Long Buildup"
            elif change_pct < -0.15:
                futures_score = -50.0 - min(50.0, 1.1 * 20.0 + abs(change_pct) * 10.0)
                futures_structure_val = "Short Buildup"
            else:
                futures_score = 0.0
                futures_structure_val = "Neutral"
            futures_desc = f"Futures data offline; Yahoo Finance fallback indicates {futures_structure_val} (Est score: {futures_score:.1f})."
        except Exception as ey:
            logger.error(f"Yahoo Finance fallback also failed for futures: {ey}")
            futures_score = 0.0
            futures_desc = "Futures data and fallback unavailable."

    # ── 2. Option Analytics Component ─────────────────────────────────────────
    options_score = 0.0
    options_desc = "Option chain data unavailable."
    pcr = 1.0
    max_pain = 0.0
    spot = 0.0
    call_unwinding, put_unwinding, short_covering, long_buildup = "Weak", "Weak", "Weak", "Weak"
    try:
        from option_engine.router import get_option_chain
        chain_data = get_option_chain(symbol=symbol_upper, expiry="weekly")
        pcr = float(chain_data.get("pcr", 1.0))
        max_pain = float(chain_data.get("maxPain", 0.0))
        spot = float(chain_data.get("spot", 0.0))
        call_unwinding = chain_data.get("call_unwinding", "Weak")
        put_unwinding = chain_data.get("put_unwinding", "Weak")
        short_covering = chain_data.get("short_covering", "Weak")
        long_buildup = chain_data.get("long_buildup", "Weak")
        
        # Options PCR scoring
        if pcr > 1.3:
            options_score = 100.0
        elif pcr >= 1.0:
            options_score = 50.0
        elif pcr >= 0.8:
            options_score = -20.0
        else:
            options_score = -100.0

        # Adjust score by Max Pain Proximity
        if max_pain > 0 and spot > 0:
            pain_diff = (spot - max_pain) / max_pain * 100.0
            if pain_diff > 0.5:
                options_score += 10.0
            elif pain_diff < -0.5:
                options_score -= 10.0
        
        options_score = max(-100.0, min(100.0, options_score))
        options_desc = f"PCR at {pcr:.2f}. Max Pain proximity shows spot relative to {max_pain:.0f}."
    except Exception as e:
        logger.warning(f"Option Engine fetch failed in Smart Money Flow: {e}. Applying fallbacks.")
        options_score = 0.0
        options_desc = "Option chain data offline; options component score set to neutral (0)."

    # ── 3. OI Structure Component ─────────────────────────────────────────────
    oi_structure_score = 0.0
    oi_desc = "OI Structure Analytics unavailable."
    structure_class = "Neutral"
    try:
        # Map strength values
        strength_map = {"Strong": 1.0, "Moderate": 0.5, "Weak": 0.0}
        lb_val = strength_map.get(long_buildup, 0.0)
        sc_val = strength_map.get(short_covering, 0.0)
        pu_val = strength_map.get(put_unwinding, 0.0)
        cu_val = strength_map.get(call_unwinding, 0.0)

        # Retrieve market trend classification
        from data_engine.router import get_market_structure
        struct = get_market_structure(symbol=symbol_upper)
        structure_class = struct.get("classification", "Neutral")
        structure_state = struct.get("state", "Consolidation")

        oi_base = (lb_val * 40.0 + sc_val * 30.0) - (pu_val * 40.0 + cu_val * 30.0)
        if structure_class == "Bullish":
            oi_base += 30.0
        elif structure_class == "Bearish":
            oi_base -= 30.0
            
        oi_structure_score = max(-100.0, min(100.0, oi_base))
        oi_desc = f"OI structure shows long buildup: {long_buildup}, short covering: {short_covering}. Trend is {structure_class} ({structure_state})."
    except Exception as e:
        logger.warning(f"OI Structure calculations failed in Smart Money Flow: {e}")
        oi_structure_score = 0.0
        oi_desc = "OI structure analytics offline; using neutral baseline."

    # ── 4. Market Breadth Component ───────────────────────────────────────────
    breadth_score = 0.0
    breadth_desc = "Market Breadth data unavailable."
    ad_ratio = 1.0
    breadth_status = "Neutral"
    try:
        from data_engine.router import get_market_breadth
        breadth_data = get_market_breadth(symbol=symbol_upper)
        ad_ratio = float(breadth_data.get("ad_ratio", 1.0))
        breadth_status = breadth_data.get("breadth_status", "Neutral")

        if ad_ratio >= 2.0:
            breadth_score = 100.0
        elif ad_ratio >= 1.2:
            breadth_score = 50.0
        elif ad_ratio >= 0.8:
            breadth_score = 0.0
        elif ad_ratio >= 0.5:
            breadth_score = -50.0
        else:
            breadth_score = -100.0

        breadth_desc = f"Market Breadth is {breadth_status} with A/D ratio of {ad_ratio:.2f}."
    except Exception as e:
        logger.warning(f"Market Breadth fetch failed in Smart Money Flow: {e}")
        breadth_score = 0.0
        breadth_desc = "Market Breadth data offline."

    # ── 5. Sector Rotation Component ──────────────────────────────────────────
    sector_score = 0.0
    sector_desc = "Sector strength rotation data unavailable."
    try:
        from sector_engine.router import get_sector_strength
        sectors = get_sector_strength(symbol=symbol_upper)
        if sectors:
            strong_sectors = sum(1 for s in sectors if s["strength"] in ("Outperforming", "Strong"))
            weak_sectors = sum(1 for s in sectors if s["strength"] in ("Underperforming", "Weak"))
            sector_score = ((strong_sectors - weak_sectors) / len(sectors)) * 100.0
            sector_score = max(-100.0, min(100.0, sector_score))
            sector_desc = f"Sector rotation shows {strong_sectors} strong vs {weak_sectors} weak sectors out of {len(sectors)} total."
    except Exception as e:
        logger.warning(f"Sector rotation fetch failed in Smart Money Flow: {e}")
        sector_score = 0.0
        sector_desc = "Sector rotation data offline."

    try:
        vix_data = get_vix_analytics()
        vix = vix_data["current_vix"]
    except Exception as ev:
        logger.warning(f"VIX Analytics Engine fetch failed in Smart Money Flow: {ev}")
        vix = 15.0

    # ── 7. Calculate Smart Money Score & Institutional Bias ──────────────────
    # Smart Money Score runs from 0 to 100 (derived from average raw score -100 to +100)
    average_raw_score = (
        futures_score +
        options_score +
        oi_structure_score +
        breadth_score +
        sector_score
    ) / 5.0
    
    smart_money_score = round((average_raw_score + 100.0) / 2.0, 1)

    # Determine Institutional Bias
    if average_raw_score >= 60.0:
        institutional_bias = "Aggressive Bullish"
    elif average_raw_score >= 15.0:
        institutional_bias = "Bullish"
    elif average_raw_score <= -60.0:
        institutional_bias = "Aggressive Bearish"
    elif average_raw_score <= -15.0:
        institutional_bias = "Bearish"
    else:
        institutional_bias = "Neutral"

    # ── 8. Classify Smart Money Flow & Market Regime ──────────────────────────
    # Smart Money Flow: Bullish Accumulation | Bearish Distribution | Short Covering Rally | Profit Booking | Neutral
    if smart_money_score >= 65.0:
        if futures_structure_val == "Short Covering" or call_unwinding == "Strong":
            smart_money_flow = "Short Covering Rally"
        else:
            smart_money_flow = "Bullish Accumulation"
    elif smart_money_score <= 35.0:
        if futures_structure_val == "Long Unwinding" or put_unwinding == "Strong":
            smart_money_flow = "Profit Booking"
        else:
            smart_money_flow = "Bearish Distribution"
    else:
        if futures_structure_val == "Short Covering" or short_covering == "Strong":
            smart_money_flow = "Short Covering Rally"
        elif futures_structure_val == "Long Unwinding" or put_unwinding in ("Strong", "Moderate"):
            smart_money_flow = "Profit Booking"
        else:
            smart_money_flow = "Neutral"

    # Market Regime: Trending Bullish | Trending Bearish | Range Bound | High Volatility | Low Volatility
    if vix > 19.0:
        market_regime = "High Volatility"
    elif vix < 11.5:
        market_regime = "Low Volatility"
    elif structure_class == "Bullish" and ad_ratio > 1.4:
        market_regime = "Trending Bullish"
    elif structure_class == "Bearish" and ad_ratio < 0.7:
        market_regime = "Trending Bearish"
    else:
        market_regime = "Range Bound"

    # ── 9. Confidence Engine ──────────────────────────────────────────────────
    scores = [futures_score, options_score, oi_structure_score, breadth_score, sector_score]
    pos_count = sum(1 for s in scores if s > 15.0)
    neg_count = sum(1 for s in scores if s < -15.0)
    neutral_count = len(scores) - pos_count - neg_count
    
    max_alignment = max(pos_count, neg_count)
    if max_alignment == 5:
        confidence = 90
    elif max_alignment == 4:
        confidence = 75
    elif max_alignment == 3:
        confidence = 60
    else:
        confidence = 50
        
    if neutral_count >= 3:
        confidence = 50

    return {
        "symbol": symbol_upper,
        "smart_money_flow": smart_money_flow,
        "confidence": confidence,
        "smart_money_score": smart_money_score,
        "institutional_bias": institutional_bias,
        "market_regime": market_regime,
        "component_scores": {
            "futures": round(futures_score, 1),
            "options": round(options_score, 1),
            "oi_structure": round(oi_structure_score, 1),
            "breadth": round(breadth_score, 1),
            "sectors": round(sector_score, 1)
        },
        "factors": {
            "futures": futures_desc,
            "options": options_desc,
            "oi_structure": oi_desc,
            "breadth": breadth_desc,
            "sectors": sector_desc,
            "vix": f"India VIX currently stands at {vix:.2f}."
        }
    }


def get_smart_money_flow(symbol: str = "NIFTY") -> dict:
    """
    Cached accessor method to get Smart Money Flow insights, preventing repeated
    cross-engine requests. Cache expires after 30 seconds.
    """
    symbol_upper = symbol.upper().strip()
    now = time.time()
    if symbol_upper in _cache:
        cached_val, expiry = _cache[symbol_upper]
        if now < expiry:
            logger.info(f"Serving Smart Money Flow for {symbol_upper} from cache.")
            return cached_val
            
    data = calculate_smart_money_flow(symbol_upper)
    _cache[symbol_upper] = (data, now + CACHE_TTL)
    return data
