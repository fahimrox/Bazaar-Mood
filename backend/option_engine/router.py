from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["Option Engine"])

@router.get("/option-chain")
def get_option_chain(symbol: str = Query("NIFTY"), expiry: str = Query("weekly")):
    raise HTTPException(
        status_code=503, 
        detail="Option chain data is unavailable - live broker feed required."
    )

@router.get("/oi-activity")
def get_oi_activity(symbol: str = Query("NIFTY")):
    raise HTTPException(
        status_code=503, 
        detail="Open Interest activity data is unavailable - live broker feed required."
    )

