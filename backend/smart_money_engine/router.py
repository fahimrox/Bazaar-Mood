from fastapi import APIRouter, Query, HTTPException
from smart_money_engine.flow_engine import get_smart_money_flow
import logging

logger = logging.getLogger("BazaarMood.SmartMoneyRouter")
router = APIRouter(tags=["Smart Money Flow Engine"])

@router.get("/smart-money-flow")
def get_flow(symbol: str = Query("NIFTY")):
    """
    Returns the aggregated Smart Money Flow analytics for the requested index.
    Includes smart_money_flow, smart_money_score, institutional_bias, market_regime,
    component_scores, and descriptive factors.
    """
    try:
        return get_smart_money_flow(symbol)
    except Exception as e:
        logger.error(f"Failed to fetch smart money flow for {symbol}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Smart money flow analysis failed: {str(e)}"
        )
