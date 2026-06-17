from fastapi import APIRouter, HTTPException, Query
from sentiment_engine.market_sentiment_v2 import calculate_sentiment_v2
import logging

logger = logging.getLogger("BazaarMood.SentimentRouter")
router = APIRouter(tags=["Sentiment Engine"])

@router.get("/sentiment")
def get_sentiment(symbol: str = Query("NIFTY")):
    """
    Returns the aggregated AI Sentiment V2 scoring matrix.
    Includes factor scores, market regime, confidence, and backward-compatible fields.
    """
    try:
        return calculate_sentiment_v2(symbol)
    except Exception as e:
        logger.error(f"Failed to calculate sentiment for {symbol}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Sentiment calculation failed: {str(e)}"
        )


@router.get("/trade-recommendation")
def get_recommendation(symbol: str = Query("NIFTY")):
    """
    Generates technical trade recommendations (BUY/SELL/HOLD) consuming
    the Sentiment V2 signal as its primary input, enhanced by Smart Money Flow V1.
    """
    try:
        sentiment = calculate_sentiment_v2(symbol)
        bias = sentiment["market_sentiment"]
        signal = sentiment["signal"]
        score = sentiment["score"]
        confidence = sentiment["confidence"]
        regime = sentiment["market_regime"]
        
        # Fetch smart money flow
        try:
            from smart_money_engine.flow_engine import get_smart_money_flow
            sm_flow = get_smart_money_flow(symbol=symbol)
            sm_flow_name = sm_flow["smart_money_flow"]
            sm_score = sm_flow["smart_money_score"]
            sm_bias = sm_flow["institutional_bias"]
        except Exception as esm:
            logger.error(f"Failed to fetch smart money flow for trade recommendation: {esm}")
            sm_flow_name = "Neutral"
            sm_score = 50.0
            sm_bias = "Neutral"

        # Attempt to retrieve support/resistance levels from Support Engine
        try:
            from support_engine.router import get_support_resistance
            levels = get_support_resistance(symbol=symbol)
            pivot = float(levels.get("pivot", 0.0))
            r1 = float(levels.get("r1", 0.0))
            s1 = float(levels.get("s1", 0.0))
            r2 = float(levels.get("r2", 0.0))
            s2 = float(levels.get("s2", 0.0))
            r3 = float(levels.get("r3", 0.0))
        except Exception as exc:
            logger.error(f"Support levels fetch failed for trade recommendation: {exc}")
            # Dynamic fallbacks in case support engine fails
            spot = sentiment.get("spot") or 24000.0
            pivot = spot
            r1 = spot * 1.005
            s1 = spot * 0.995
            r2 = spot * 1.01
            s2 = spot * 0.990
            r3 = spot * 1.015
            
        spot = sentiment.get("spot") or pivot
        if spot <= 0.0:
            spot = pivot

        # Structure recommendations based on sentiment scoring
        if signal == "BUY":
            action = "BUY"
            entry = spot
            if r1 > spot:
                target = r2 if bias == "Strong Bullish" else r1
            elif r2 > spot:
                target = r3 if bias == "Strong Bullish" else r2
            else:
                target = spot * (1.01 if bias == "Strong Bullish" else 1.005)
            
            if s1 < spot:
                stop_loss = s1
            else:
                stop_loss = spot * 0.995

            # Enhance confidence if smart money flow is bullish
            if sm_flow_name in ("Bullish Accumulation", "Short Covering Rally"):
                confidence = min(95, confidence + 5)
                sm_note = f" Smart Money Flow is in '{sm_flow_name}' ({sm_bias}), confirming buy momentum."
            else:
                sm_note = f" Smart Money Flow is '{sm_flow_name}'."

            rationale = (
                f"Macro sentiment is {bias} (Score: {score}) with {confidence}% confidence.{sm_note} "
                f"{sentiment['factors']['breadth']} "
                f"{sentiment['factors']['options']} "
                f"Market regime classified as '{regime}'."
            )
        elif signal == "SELL":
            action = "SELL"
            entry = spot
            if s1 < spot:
                target = s2 if bias == "Strong Bearish" else s1
            elif s2 < spot:
                target = s3 if bias == "Strong Bearish" else s2
            else:
                target = spot * (0.99 if bias == "Strong Bearish" else 0.995)

            if r1 > spot:
                stop_loss = r1
            else:
                stop_loss = spot * 1.005

            # Enhance confidence if smart money flow is bearish
            if sm_flow_name in ("Bearish Distribution", "Profit Booking"):
                confidence = min(95, confidence + 5)
                sm_note = f" Smart Money Flow is in '{sm_flow_name}' ({sm_bias}), confirming sell pressure."
            else:
                sm_note = f" Smart Money Flow is '{sm_flow_name}'."

            rationale = (
                f"Macro sentiment is {bias} (Score: {score}) with {confidence}% confidence.{sm_note} "
                f"{sentiment['factors']['breadth']} "
                f"{sentiment['factors']['options']} "
                f"Market regime classified as '{regime}'."
            )
        else:
            action = "HOLD"
            target = spot
            stop_loss = spot
            entry = spot
            rationale = (
                f"Macro sentiment is Neutral (Score: {score}). Smart Money Flow is '{sm_flow_name}' (Score: {sm_score:.1f}). "
                f"Market indicators show conflict. Volatility regime is '{regime}'. "
                f"Recommendation is to hold current positions and wait for range expansion."
            )

        return {
            "action": action,
            "entry": round(entry, 2),
            "target": round(target, 2),
            "stopLoss": round(stop_loss, 2),  # CamelCase for frontend compatibility
            "stop_loss": round(stop_loss, 2), # Snake_case for backend consistency
            "rationale": rationale,
            "confidence": confidence,
            "regime": regime,
            "sentiment_score": score,
            "smart_money_flow": sm_flow_name,
            "smart_money_score": sm_score,
            "institutional_bias": sm_bias
        }
        
    except Exception as e:
        logger.error(f"Failed to generate trade recommendation for {symbol}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Trade recommendation generation failed: {str(e)}"
        )
