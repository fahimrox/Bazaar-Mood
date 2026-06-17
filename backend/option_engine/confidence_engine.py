"""Confidence Engine V3 for option market bias and confidence calculations."""

def calculate_confidence(
    spot_price: float,
    pcr: float,
    max_pain: float,
    atm_strike: float,
    support_1: float,
    support_confidence: float,
    resistance_1: float,
    resistance_confidence: float,
    call_writing: str,
    put_writing: str
) -> dict:
    """
    Evaluates options indicators to return market bias and confidence score.

    total_score = bullish_score + bearish_score
    confidence_score = (abs(bullish_score - bearish_score) / total_score) * 100
    with divide-by-zero protection.
    """
    bullish_score = 0.0
    bearish_score = 0.0

    # 1. PCR scoring (Max 25 pts)
    if pcr >= 1.2:
        bullish_score += 25.0
    elif pcr > 1.1:
        bullish_score += 15.0
    elif pcr <= 0.8:
        bearish_score += 25.0
    elif pcr < 0.9:
        bearish_score += 15.0

    # 2. Writing scoring (Max 30 pts)
    if put_writing == "Strong":
        bullish_score += 30.0
    elif put_writing == "Moderate":
        bullish_score += 15.0

    if call_writing == "Strong":
        bearish_score += 30.0
    elif call_writing == "Moderate":
        bearish_score += 15.0

    # 3. Max Pain scoring (Max 20 pts)
    if spot_price > 0 and max_pain > 0:
        if spot_price < max_pain:
            bullish_score += 20.0
        elif spot_price > max_pain:
            bearish_score += 20.0

    # 4. Support & Resistance proximity (Max 25 pts)
    if spot_price > 0 and atm_strike > 0:
        if support_1 > 0:
            dist_to_support = abs(spot_price - support_1) / atm_strike
            if dist_to_support <= 0.01:
                bullish_score += 25.0 * (support_confidence / 100.0)
                
        if resistance_1 > 0:
            dist_to_resistance = abs(resistance_1 - spot_price) / atm_strike
            if dist_to_resistance <= 0.01:
                bearish_score += 25.0 * (resistance_confidence / 100.0)

    # Calculate conviction-based confidence score
    total_score = bullish_score + bearish_score
    if total_score > 0:
        confidence_score = (abs(bullish_score - bearish_score) / total_score) * 100.0
    else:
        confidence_score = 0.0

    # Bias classification based on confidence threshold
    if confidence_score >= 20.0:
        if bullish_score > bearish_score:
            market_bias = "Bullish"
        else:
            market_bias = "Bearish"
    else:
        market_bias = "Neutral"

    return {
        "market_bias": market_bias,
        "confidence_score": round(confidence_score, 2)
    }
