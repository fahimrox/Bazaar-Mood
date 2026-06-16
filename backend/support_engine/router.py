import urllib.request
import json
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["Support Engine"])

TICKER_MAP = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "MIDCPNIFTY": "^NSEMDCP50",
    "SENSEX": "^BSESN",
    "INDIAVIX": "^INDIAVIX",
    "INDIA VIX": "^INDIAVIX"
}

@router.get("/support-resistance")
def get_support_resistance(symbol: str = Query(..., description="Ticker symbol or Index name")):
    symbol_upper = symbol.upper().strip()
    symbol_key = symbol_upper.replace(" ", "")
    ticker = TICKER_MAP.get(symbol_key)
    
    if not ticker:
        raise HTTPException(status_code=400, detail=f"Unsupported index symbol: {symbol}")
        
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read())
            if not res_data.get("chart", {}).get("result"):
                raise HTTPException(status_code=503, detail="Empty chart result from Yahoo Finance")
                
            result = res_data["chart"]["result"][0]
            meta = result["meta"]
            current_price = meta.get("regularMarketPrice") or 0.0
            
            indicators = result.get("indicators", {}).get("quote", [{}])[0]
            highs = [h for h in indicators.get("high", []) if h is not None]
            lows = [l for l in indicators.get("low", []) if l is not None]
            closes = [c for c in indicators.get("close", []) if c is not None]
            
            if not highs or not lows or not closes:
                raise HTTPException(
                    status_code=503,
                    detail=f"Technical chart data is incomplete for {symbol_upper} - cannot calculate pivots."
                )
            
            # If we have daily bars, yesterday's completed bar is usually second to last
            # if today's market is currently trading (today's bar is last).
            # If only 1 bar is returned or today hasn't started, last is yesterday.
            idx = -2 if len(closes) >= 2 else -1
            high_val = highs[idx]
            low_val = lows[idx]
            close_val = closes[idx]
            
            # Standard Floor Pivot Points
            pivot = (high_val + low_val + close_val) / 3.0
            r1 = (2.0 * pivot) - low_val
            s1 = (2.0 * pivot) - high_val
            r2 = pivot + (high_val - low_val)
            s2 = pivot - (high_val - low_val)
            r3 = high_val + 2.0 * (pivot - low_val)
            s3 = low_val - 2.0 * (high_val - pivot)
            
            return {
                "symbol": symbol_upper,
                "pivot": float(pivot),
                "r1": float(r1),
                "s1": float(s1),
                "r2": float(r2),
                "s2": float(s2),
                "r3": float(r3),
                "s3": float(s3)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Live support/resistance calculation failed for {symbol_upper}: {str(e)}"
        )


