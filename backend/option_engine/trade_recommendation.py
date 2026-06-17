"""AI Trade Recommendation V2 for option chain."""

def generate_recommendation(
    spot_price: float,
    pcr: float,
    max_pain: float,
    atm_strike: float,
    support_1: float,
    support_confidence: float,
    resistance_1: float,
    resistance_confidence: float,
    call_writing: str,
    put_writing: str,
    market_bias: str,
    confidence_score: float
) -> dict:
    """
    Generates AI Trade Recommendations based on technical option indicators.
    """
    reasons = []
    trade_signal = "NO TRADE"
    entry = 0.0
    stop_loss = 0.0
    target = 0.0
    trade_confidence = 0.0

    # Determine proximity signals for reasons list
    if spot_price > 0 and atm_strike > 0:
        if support_1 > 0 and (abs(spot_price - support_1) / atm_strike) <= 0.015:
            reasons.append("Spot Near Support")
        if resistance_1 > 0 and (abs(resistance_1 - spot_price) / atm_strike) <= 0.015:
            reasons.append("Spot Near Resistance")

    # Add general signals to reasons list if they are relevant/active
    if pcr >= 1.1:
        reasons.append("Bullish PCR")
    elif pcr <= 0.9:
        reasons.append("Bearish PCR")

    if put_writing in ("Strong", "Moderate"):
        reasons.append(f"{put_writing} Put Writing")
    if call_writing in ("Strong", "Moderate"):
        reasons.append(f"{call_writing} Call Writing")

    reasons.append(f"{market_bias} Market Bias")

    # Triggering Logic
    is_bullish_setup = (
        market_bias == "Bullish" and
        confidence_score >= 60.0 and
        put_writing in ("Strong", "Moderate")
    )
    
    is_bearish_setup = (
        market_bias == "Bearish" and
        confidence_score >= 60.0 and
        call_writing in ("Strong", "Moderate")
    )

    if is_bullish_setup:
        trade_signal = "BUY CE"
        entry = float(atm_strike)
        stop_loss = float(support_1)
        target = float(resistance_1)
        trade_confidence = float(confidence_score)
    elif is_bearish_setup:
        trade_signal = "BUY PE"
        entry = float(atm_strike)
        stop_loss = float(resistance_1)
        target = float(support_1)
        trade_confidence = float(confidence_score)
    else:
        trade_signal = "NO TRADE"
        entry = 0.0
        stop_loss = 0.0
        target = 0.0
        trade_confidence = 0.0
        # If no trade, prefix reasons list with why there's no trade
        no_trade_reasons = []
        if confidence_score < 60.0:
            no_trade_reasons.append(f"Low Confidence Score ({confidence_score} < 60)")
        if market_bias == "Neutral":
            no_trade_reasons.append("Neutral Market Bias")
        if market_bias == "Bullish" and put_writing == "Weak":
            no_trade_reasons.append("Weak Put Writing")
        if market_bias == "Bearish" and call_writing == "Weak":
            no_trade_reasons.append("Weak Call Writing")
        
        reasons = no_trade_reasons + reasons

    return {
        "trade_signal": trade_signal,
        "entry": entry,
        "stop_loss": stop_loss,
        "target": target,
        "trade_confidence": round(trade_confidence, 2),
        "reason": reasons
    }
