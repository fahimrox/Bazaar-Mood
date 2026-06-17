from fastapi import APIRouter, HTTPException
from futures_engine.futures_analytics import calculate_futures_analytics
import logging

logger = logging.getLogger("BazaarMood.FuturesRouter")
router = APIRouter(tags=["Futures Engine"])

@router.get("/futures-analytics")
def get_futures_analytics():
    """
    Returns the market-level futures summary and individual index signals.
    Tracks Open Interest changes, price movements, smart money flows, and classifications.
    """
    try:
        return calculate_futures_analytics()
    except Exception as e:
        logger.error(f"Failed to calculate futures analytics: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Futures analytics generation failed: {str(e)}"
        )
