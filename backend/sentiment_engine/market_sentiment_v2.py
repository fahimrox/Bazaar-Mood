import logging
import urllib.request
import json
import time
from vix_engine.vix_analytics import get_vix_analytics

# Configure logger
logger = logging.getLogger("BazaarMood.SentimentEngineV2")

def fetch_india_vix() -> float:
    """Fetches the current India VIX price from Yahoo Finance."""
    url = "https://query1.finance.yahoo.com/v8/finance/chart/^INDIAVIX"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            result = res_data["chart"]["result"][0]
            vix_price = result["meta"].get("regularMarketPrice")
            if vix_price is not None:
                return float(vix_price)
    except Exception as e:
        logger.error(f"Failed to fetch India VIX: {e}")
    return 15.0  # Safe default moderate volatility


def calculate_sentiment_v2(symbol: str = "NIFTY") -> dict:
    """
    Calculates weighted market sentiment based on:
    - Market Breadth (Data Engine constituents)
    - Option Analytics (PCR & Max Pain proximity)
    - OI Structure & Market Structure
    - Sector Analytics (sector strength rotation)
    - India VIX (volatility regime)
    """
    symbol_upper = symbol.upper().strip()
    
    # ── 1. Fetch Market Breadth ──────────────────────────────────────────────
    try:
        from data_engine.constituent_data import get_constituent_data
        constituents = get_constituent_data()
        advances = sum(1 for c in constituents if c["change_percent"] > 0.05)
        declines = sum(1 for c in constituents if c["change_percent"] < -0.05)
        unchanged = len(constituents) - advances - declines
    except Exception as e:
        logger.error(f"Failed to get constituent data for sentiment: {e}")
        constituents, advances, declines, unchanged = [], 25, 25, 0

    total_stocks = len(constituents) or 50
    ad_ratio = (advances / declines) if declines > 0 else float(advances)
    
    # Breadth Score (-1.0 to +1.0)
    if ad_ratio >= 2.0:
        breadth_score = 1.0
        breadth_desc = "Strong advances over declines indicating broad-market buying."
    elif ad_ratio >= 1.2:
        breadth_score = 0.5
        breadth_desc = "Moderate positive market breadth with advancing stocks leading."
    elif ad_ratio >= 0.8:
        breadth_score = 0.0
        breadth_desc = "Balanced market breadth with flat price action."
    elif ad_ratio >= 0.5:
        breadth_score = -0.5
        breadth_desc = "Negative market breadth with declining stocks in control."
    else:
        breadth_score = -1.0
        breadth_desc = "Severe negative market breadth indicating broad-market distribution."

    # ── 2. Fetch Option Chain and OI Structure ───────────────────────────────
    try:
        from option_engine.router import get_option_chain
        # Internally call the option chain router
        chain_data = get_option_chain(symbol=symbol_upper, expiry="weekly")
        pcr = float(chain_data.get("pcr", 1.0))
        max_pain = float(chain_data.get("maxPain", 0.0))
        spot = float(chain_data.get("spot", 0.0))
        call_unwinding = chain_data.get("call_unwinding", "Weak")
        put_unwinding = chain_data.get("put_unwinding", "Weak")
        short_covering = chain_data.get("short_covering", "Weak")
        long_buildup = chain_data.get("long_buildup", "Weak")
        atm_strike = float(chain_data.get("atm_strike", 0.0))
    except Exception as e:
        logger.error(f"Option Engine fetch failed for sentiment, applying defaults: {e}")
        pcr, max_pain, spot, atm_strike = 1.0, 0.0, 0.0, 0.0
        call_unwinding, put_unwinding, short_covering, long_buildup = "Weak", "Weak", "Weak", "Weak"

    # PCR Scoring
    if pcr > 1.3:
        pcr_score = 1.0
        pcr_bias = "Bullish (Put writing heavy)"
    elif pcr >= 1.0:
        pcr_score = 0.5
        pcr_bias = "Mildly Bullish (Balanced bias)"
    elif pcr >= 0.8:
        pcr_score = -0.2
        pcr_bias = "Mildly Bearish"
    else:
        pcr_score = -1.0
        pcr_bias = "Bearish (Call writing heavy)"

    # Max Pain Proximity
    if max_pain > 0 and spot > 0:
        pain_diff = (spot - max_pain) / max_pain * 100.0
        if abs(pain_diff) <= 0.5:
            pain_score = 0.0
            pain_desc = f"Spot close to Max Pain ({max_pain:.0f})"
        elif pain_diff > 0.5:
            pain_score = 0.5
            pain_desc = f"Spot above Max Pain by {pain_diff:.2f}%"
        else:
            pain_score = -0.5
            pain_desc = f"Spot below Max Pain by {abs(pain_diff):.2f}%"
    else:
        pain_score = 0.0
        pain_desc = "Max Pain data unavailable"

    options_score = float(0.7 * pcr_score + 0.3 * pain_score)

    # OI Structure Scoring
    strength_map = {"Strong": 1.0, "Moderate": 0.5, "Weak": 0.0}
    lb_val = strength_map.get(long_buildup, 0.0)
    sc_val = strength_map.get(short_covering, 0.0)
    pu_val = strength_map.get(put_unwinding, 0.0)
    cu_val = strength_map.get(call_unwinding, 0.0)

    # Fetch Market Structure Technical Trend
    try:
        from data_engine.router import get_market_structure
        struct = get_market_structure(symbol=symbol_upper)
        structure_class = struct.get("classification", "Neutral")
        structure_state = struct.get("state", "Consolidation")
    except Exception as e:
        logger.error(f"Market structure fetch failed for sentiment: {e}")
        structure_class = "Neutral"
        structure_state = "Consolidation"

    oi_base = (lb_val * 0.4 + sc_val * 0.3) - (pu_val * 0.4 + cu_val * 0.3)
    if structure_class == "Bullish":
        oi_base += 0.3
    elif structure_class == "Bearish":
        oi_base -= 0.3

    oi_score = float(max(-1.0, min(1.0, oi_base)))
    oi_desc = f"OI Buildups: Long Buildup is {long_buildup}, Short Covering is {short_covering}. Structure is {structure_class} ({structure_state})."

    # ── 3. Fetch Sector Strength ─────────────────────────────────────────────
    try:
        from sector_engine.router import get_sector_strength
        sectors = get_sector_strength(symbol=symbol_upper)
    except Exception as e:
        logger.error(f"Sector Engine fetch failed for sentiment: {e}")
        sectors = []

    if sectors:
        strong_sectors = sum(1 for s in sectors if s["strength"] in ("Outperforming", "Strong"))
        weak_sectors = sum(1 for s in sectors if s["strength"] in ("Underperforming", "Weak"))
        
        # Calculate average change percent
        total_pct = sum(s["pct"] for s in sectors)
        avg_pct = total_pct / len(sectors)
        
        sector_score = (strong_sectors - weak_sectors) / len(sectors)
        sector_score = float(max(-1.0, min(1.0, sector_score)))
        
        sector_desc = f"Sector rotation shows {strong_sectors} strong vs {weak_sectors} weak sectors. Avg change: {avg_pct:.2f}%."
    else:
        sector_score = 0.0
        sector_desc = "Sector rotation matrix details unavailable."

    # ── 4. Fetch India VIX ───────────────────────────────────────────────────
    try:
        vix_data = get_vix_analytics()
        vix = vix_data["current_vix"]
        vix_class = vix_data["volatility_regime"]
        vix_desc = f"India VIX at {vix:.2f} is in {vix_class} regime (Risk: {vix_data['market_risk']})."
        
        if vix < 12.0:
            vix_score = 0.5
        elif vix <= 18.0:
            vix_score = 0.0
        else:
            vix_score = -0.8
    except Exception as ev:
        logger.error(f"VIX Analytics Engine fetch failed in sentiment: {ev}")
        vix = 15.0
        vix_score = 0.0
        vix_class = "Low / Normal"
        vix_desc = "India VIX at 15.0 is in normal moderate volatility bands."
        vix_data = None

    # ── 5. Market Regime Classification ──────────────────────────────────────
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

    # ── 5.5. Fetch Futures Analytics ─────────────────────────────────────────
    try:
        from futures_engine.futures_analytics import calculate_futures_analytics
        futures_data = calculate_futures_analytics()
        futures_signal = next((s for s in futures_data["futures_signals"] if s["symbol"] == symbol_upper), None)
        if futures_signal:
            futures_score = futures_signal["smart_money_score"] / 100.0  # normalise -1.0 to +1.0
            futures_desc = f"Futures structure is {futures_signal['futures_structure']} with smart money score of {futures_signal['smart_money_score']} (Institutional Flow: {futures_data['institutional_flow']})."
        else:
            futures_score = None
            futures_desc = "Futures data unavailable for this index."
    except Exception as e:
        logger.error(f"Futures Analytics fetch failed for sentiment: {e}")
        futures_score = None
        futures_desc = "Futures data analytics failed or unavailable."

    # ── 6. Weighted Sentiment Score & Confidence ─────────────────────────────
    if futures_score is not None:
        # Weights: Breadth (15%), Options (15%), OI (20%), Sector (15%), VIX (15%), Futures (20%)
        total_score = (
            (breadth_score * 0.15) +
            (options_score * 0.15) +
            (oi_score * 0.20) +
            (sector_score * 0.15) +
            (vix_score * 0.15) +
            (futures_score * 0.20)
        )
    else:
        # Fallback Weights: Breadth (20%), Options (20%), OI (25%), Sector (20%), VIX (15%)
        total_score = (
            (breadth_score * 0.20) +
            (options_score * 0.20) +
            (oi_score * 0.25) +
            (sector_score * 0.20) +
            (vix_score * 0.15)
        )
    total_score = round(max(-1.0, min(1.0, total_score)), 2)

    # Resolve Sentiment Bias Label and Trade Signal
    if total_score >= 0.6:
        market_sentiment = "Strong Bullish"
        signal = "BUY"
    elif total_score >= 0.15:
        market_sentiment = "Bullish"
        signal = "BUY"
    elif total_score > -0.15:
        market_sentiment = "Neutral"
        signal = "HOLD"
    elif total_score > -0.6:
        market_sentiment = "Bearish"
        signal = "SELL"
    else:
        market_sentiment = "Strong Bearish"
        signal = "SELL"

    # Confidence calculation: measures directional alignment
    if futures_score is not None:
        scores = [breadth_score, options_score, oi_score, sector_score, vix_score, futures_score]
        pos_count = sum(1 for s in scores if s > 0.05)
        neg_count = sum(1 for s in scores if s < -0.05)
        neutral_count = len(scores) - pos_count - neg_count

        max_alignment = max(pos_count, neg_count)
        if max_alignment == 6:
            confidence = 95
        elif max_alignment == 5:
            confidence = 85
        elif max_alignment == 4:
            confidence = 70
        elif max_alignment == 3:
            confidence = 55
        else:
            confidence = 45
    else:
        scores = [breadth_score, options_score, oi_score, sector_score, vix_score]
        pos_count = sum(1 for s in scores if s > 0.05)
        neg_count = sum(1 for s in scores if s < -0.05)
        neutral_count = len(scores) - pos_count - neg_count

        max_alignment = max(pos_count, neg_count)
        if max_alignment == 5:
            confidence = 90
        elif max_alignment == 4:
            confidence = 75
        elif max_alignment == 3:
            confidence = 60
        else:
            confidence = 45

    if neutral_count >= 3:
        confidence = 50

    try:
        from smart_money_engine.flow_engine import get_smart_money_flow
        sm_flow = get_smart_money_flow(symbol=symbol_upper)
        sm_flow_name = sm_flow["smart_money_flow"]
        sm_flow_score = sm_flow["smart_money_score"]
        sm_inst_bias = sm_flow["institutional_bias"]
    except Exception as e:
        logger.error(f"Failed to integrate smart money flow in sentiment: {e}")
        sm_flow_name = "Neutral"
        sm_flow_score = 50.0
        sm_inst_bias = "Neutral"

    return {
        "market_sentiment": market_sentiment,
        "confidence": confidence,
        "score": total_score,
        "market_regime": market_regime,
        "smart_money_flow": sm_flow_name,
        "smart_money_score": sm_flow_score,
        "institutional_bias": sm_inst_bias,
        "vix_analytics": vix_data,
        "factor_scores": {
            "breadth": round(breadth_score, 2),
            "options": round(options_score, 2),
            "oi_structure": round(oi_score, 2),
            "sector_strength": round(sector_score, 2),
            "vix": round(vix_score, 2),
            "futures": round(futures_score, 2) if futures_score is not None else 0.0
        },
        "factors": {
            "breadth": breadth_desc,
            "options": f"{pcr_bias}. {pain_desc}.",
            "oi_structure": oi_desc,
            "sector_strength": sector_desc,
            "vix": vix_desc,
            "futures": futures_desc
        },
        # Backward compatibility fields for Dashboard.jsx
        "bias": market_sentiment,
        "pcr": str(pcr) if pcr > 0 else "1.0",
        "strength": confidence,
        "signal": signal,
        "spot": spot,
        "max_pain": max_pain,
        "central_pivot": atm_strike if atm_strike > 0 else spot
    }
