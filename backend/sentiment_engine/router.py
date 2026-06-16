from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["Sentiment Engine"])

@router.get("/sentiment")
def get_sentiment(symbol: str = Query("NIFTY")):
    raise HTTPException(
        status_code=503,
        detail="Sentiment data is unavailable - live broker feed required."
    )

@router.get("/trade-recommendation")
def get_recommendation(symbol: str = Query("NIFTY")):
    raise HTTPException(
        status_code=503,
        detail="Trade recommendation data is unavailable - live broker feed required."
    )
