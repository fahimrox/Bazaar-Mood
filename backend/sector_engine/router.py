import urllib.request
import json
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["Sector Engine"])

SECTORS = {
    "NIFTY IT": "^CNXIT",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY REALTY": "^CNXREALTY",
    "NIFTY ENERGY": "^CNXENERGY",
    "NIFTY INFRA": "^CNXINFRA"
}

def fetch_sector_price(ticker: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read())
            if not res_data.get("chart", {}).get("result"):
                return None
            result = res_data["chart"]["result"][0]
            meta = result["meta"]
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
            
            if price is not None and prev_close is not None:
                change = price - prev_close
                pct = (change / prev_close) * 100
                return float(price), float(change), float(pct)
    except Exception:
        return None
    return None

@router.get("/sector-strength")
def get_sector_strength(symbol: str = Query("NIFTY")):
    results = []
    
    for name, ticker in SECTORS.items():
        data = fetch_sector_price(ticker)
        if not data:
            raise HTTPException(
                status_code=503,
                detail=f"Sector strength data is unavailable for {name} - live broker feed required."
            )
            
        price, change, pct = data
        
        strength = "Neutral"
        if pct > 1.0:
            strength = "Outperforming"
        elif pct > 0.3:
            strength = "Strong"
        elif pct < -1.0:
            strength = "Underperforming"
        elif pct < -0.3:
            strength = "Weak"
            
        results.append({
            "sector": name,
            "ticker": ticker,
            "price": round(price, 2),
            "change": round(change, 2),
            "pct": round(pct, 2),
            "strength": strength
        })
        
    return results


