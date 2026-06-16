import urllib.request
import json
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(tags=["Data Engine"])

TICKER_MAP = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "MIDCPNIFTY": "^NSEMDCP50",
    "SENSEX": "^BSESN",
    "INDIAVIX": "^INDIAVIX",
    "INDIA VIX": "^INDIAVIX"
}

def fetch_from_yahoo(symbol: str):
    symbol_upper = symbol.upper().strip()
    symbol_key = symbol_upper.replace(" ", "")
    ticker = TICKER_MAP.get(symbol_key)
    
    if not ticker:
        raise HTTPException(status_code=400, detail=f"Unsupported index symbol: {symbol}")
    
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read())
            if not res_data.get("chart", {}).get("result"):
                raise HTTPException(status_code=503, detail=f"Yahoo Finance returned empty result for {symbol}")
                
            result = res_data["chart"]["result"][0]
            meta = result["meta"]
            
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
            
            if price is None or prev_close is None:
                raise HTTPException(status_code=503, detail=f"Quote fields missing from Yahoo Finance response for {symbol}")
                
            change = price - prev_close
            pct = (change / prev_close) * 100 if prev_close else 0.0
            
            open_val = meta.get("regularMarketOpen") or prev_close
            high_val = meta.get("regularMarketDayHigh") or price
            low_val = meta.get("regularMarketDayLow") or price
            
            return {
                "name": symbol_upper,
                "price": float(price),
                "change": float(change),
                "pct": float(pct),
                "details": {
                    "open": float(open_val),
                    "high": float(high_val),
                    "low": float(low_val),
                    "prevClose": float(prev_close)
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Live market data source query failed for {symbol}: {str(e)}"
        )

@router.get("/market")
def get_market(symbol: str = Query("NIFTY")):
    return fetch_from_yahoo(symbol)

@router.get("/chart")
def get_chart(
    symbol: str = Query("NIFTY"), 
    range_val: str = Query("1d", alias="range"), 
    interval: str = Query("1m")
):
    symbol_upper = symbol.upper().strip()
    symbol_key = symbol_upper.replace(" ", "")
    ticker = TICKER_MAP.get(symbol_key)
    
    if not ticker:
        raise HTTPException(status_code=400, detail=f"Unsupported index symbol: {symbol}")
    
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_val}&interval={interval}"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read())
            if not res_data.get("chart", {}).get("result"):
                raise HTTPException(status_code=503, detail=f"Yahoo Finance returned empty chart result for {symbol}")
                
            result = res_data["chart"]["result"][0]
            timestamps = result.get("timestamp", [])
            indicators = result.get("indicators", {}).get("quote", [{}])[0]
            close_prices = indicators.get("close", [])
            
            chart_data = []
            for t, c in zip(timestamps, close_prices):
                if t is not None and c is not None:
                    chart_data.append({
                        "timestamp": int(t),
                        "close": float(c)
                    })
            return chart_data
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Live historical chart query failed for {symbol}: {str(e)}"
        )

@router.get("/indices")
def get_indices():
    results = []
    for sym in ["NIFTY", "BANKNIFTY", "MIDCPNIFTY", "SENSEX", "INDIA VIX"]:
        try:
            data = fetch_from_yahoo(sym)
            results.append({
                "symbol": sym,
                "name": data["name"],
                "price": data["price"],
                "change": data["change"],
                "pct": data["pct"]
            })
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Indices fetch failed at index {sym}: {str(e)}"
            )
    return results

@router.get("/market-breadth")
def get_market_breadth(symbol: str = Query("NIFTY")):
    raise HTTPException(
        status_code=503, 
        detail="Market breadth data is unavailable - live broker feed required."
    )

@router.get("/top-movers")
def get_top_movers(symbol: str = Query("NIFTY")):
    raise HTTPException(
        status_code=503, 
        detail="Top component movers data is unavailable - live broker feed required."
    )

@router.get("/market-structure")
def get_market_structure(symbol: str = Query("NIFTY")):
    symbol_upper = symbol.upper().strip()
    
    # Fetch historical chart to perform standard SMA calculation
    try:
        chart_data = get_chart(symbol_upper, "1d", "15m")
        closes = [item["close"] for item in chart_data]
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Historical market data query failed for {symbol_upper}: {str(e)}"
        )
        
    if len(closes) < 5:
        raise HTTPException(
            status_code=503,
            detail=f"Insufficient historical data points to compute market structure for {symbol_upper}."
        )
        
    # Simple Technical Analysis
    current_price = closes[-1]
    # Simple Moving Average (last 10 periods of 15m chart)
    sma_period = min(10, len(closes))
    sma = sum(closes[-sma_period:]) / sma_period
    
    # Compare current price to SMA
    diff_pct = ((current_price - sma) / sma) * 100
    
    # Slope of the last few bars
    recent_sma = sum(closes[-5:]) / 5.0
    prior_sma = sum(closes[-10:-5]) / 5.0 if len(closes) >= 10 else closes[0]
    slope = ((recent_sma - prior_sma) / prior_sma) * 100
    
    classification = "Neutral"
    if diff_pct > 0.05:
        classification = "Bullish"
    elif diff_pct < -0.05:
        classification = "Bearish"
        
    strength = "Sideways Neutral"
    if abs(slope) > 0.15:
        strength = "Strong Momentum" if slope > 0 else "Strong Selling"
    elif abs(slope) > 0.05:
        strength = "Moderate Trend" if slope > 0 else "Moderate Distribution"
        
    state = "Consolidation"
    if classification == "Bullish" and slope > 0.1:
        state = "Rallying / Expansion"
    elif classification == "Bearish" and slope < -0.1:
        state = "Retracing / Sell-off"
    elif abs(diff_pct) < 0.05 and abs(slope) < 0.05:
        state = "Accumulation / Consolidation"
        
    return {
        "symbol": symbol_upper,
        "state": state,
        "strength": strength,
        "classification": classification
    }

@router.get("/screeners")
def get_screeners():
    raise HTTPException(
        status_code=503,
        detail="Screener data is unavailable - live broker feed required."
    )

@router.get("/heatmaps")
def get_heatmaps():
    raise HTTPException(
        status_code=503,
        detail="Heatmap data is unavailable - live broker feed required."
    )


