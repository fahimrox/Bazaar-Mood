from fastapi import APIRouter, HTTPException
from vix_engine.vix_analytics import get_vix_analytics
import logging

logger = logging.getLogger("BazaarMood.VixRouter")
router = APIRouter(tags=["VIX Volatility Engine"])

@router.get("/vix-analytics")
def get_vix():
    """
    Returns aggregated volatility analytics for India VIX.
    Includes moving averages, percentiles, expected move ranges, daily shock metrics,
    trading environments, and index correlations.
    """
    try:
        return get_vix_analytics()
    except Exception as e:
        logger.error(f"Failed to generate India VIX analytics: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Volatility analytics analysis failed: {str(e)}"
        )
