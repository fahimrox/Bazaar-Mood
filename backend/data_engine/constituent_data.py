import urllib.request
import json
import logging
import time
import concurrent.futures
from fastapi import HTTPException

# Configure Logger
logger = logging.getLogger("BazaarMood.ConstituentData")
logging.basicConfig(level=logging.INFO)

# Configurable Cache TTL
CACHE_TTL = 60  # seconds

# Global Cache State
_constituent_cache = None
_cache_expiry = 0.0

# Isolate Sector Mapping and Shares Outstanding in one dedicated metadata structure.
# Shares outstanding are based on recent corporate reports (approximate).
# Fallback market cap is in INR.
NIFTY50_METADATA = {
    "ADANIENT.NS": {
        "company_name": "Adani Enterprises Ltd.",
        "sector": "Energy",
        "shares_outstanding": 1140000000,
        "fallback_market_cap": 3500000000000
    },
    "ADANIPORTS.NS": {
        "company_name": "Adani Ports & SEZ Ltd.",
        "sector": "Infrastructure",
        "shares_outstanding": 2160000000,
        "fallback_market_cap": 2800000000000
    },
    "APOLLOHOSP.NS": {
        "company_name": "Apollo Hospitals Enterprise Ltd.",
        "sector": "Healthcare",
        "shares_outstanding": 143800000,
        "fallback_market_cap": 900000000000
    },
    "ASIANPAINT.NS": {
        "company_name": "Asian Paints Ltd.",
        "sector": "Consumer Goods",
        "shares_outstanding": 959000000,
        "fallback_market_cap": 2700000000000
    },
    "AXISBANK.NS": {
        "company_name": "Axis Bank Ltd.",
        "sector": "Financial Services",
        "shares_outstanding": 3080000000,
        "fallback_market_cap": 3400000000000
    },
    "BAJAJ-AUTO.NS": {
        "company_name": "Bajaj Auto Ltd.",
        "sector": "Automobile",
        "shares_outstanding": 283000000,
        "fallback_market_cap": 2800000000000
    },
    "BAJFINANCE.NS": {
        "company_name": "Bajaj Finance Ltd.",
        "sector": "Financial Services",
        "shares_outstanding": 619000000,
        "fallback_market_cap": 4200000000000
    },
    "BAJAJFINSV.NS": {
        "company_name": "Bajaj Finserv Ltd.",
        "sector": "Financial Services",
        "shares_outstanding": 1590000000,
        "fallback_market_cap": 2500000000000
    },
    "BEL.NS": {
        "company_name": "Bharat Electronics Ltd.",
        "sector": "Capital Goods",
        "shares_outstanding": 7310000000,
        "fallback_market_cap": 2100000000000
    },
    "BPCL.NS": {
        "company_name": "Bharat Petroleum Corporation Ltd.",
        "sector": "Energy",
        "shares_outstanding": 2169000000,
        "fallback_market_cap": 1300000000000
    },
    "BHARTIARTL.NS": {
        "company_name": "Bharti Airtel Ltd.",
        "sector": "Telecom",
        "shares_outstanding": 5970000000,
        "fallback_market_cap": 8500000000000
    },
    "BRITANNIA.NS": {
        "company_name": "Britannia Industries Ltd.",
        "sector": "FMCG",
        "shares_outstanding": 240000000,
        "fallback_market_cap": 1200000000000
    },
    "CIPLA.NS": {
        "company_name": "Cipla Ltd.",
        "sector": "Healthcare",
        "shares_outstanding": 807000000,
        "fallback_market_cap": 1100000000000
    },
    "COALINDIA.NS": {
        "company_name": "Coal India Ltd.",
        "sector": "Energy",
        "shares_outstanding": 6160000000,
        "fallback_market_cap": 2700000000000
    },
    "DIVISLAB.NS": {
        "company_name": "Divi's Laboratories Ltd.",
        "sector": "Healthcare",
        "shares_outstanding": 265000000,
        "fallback_market_cap": 1200000000000
    },
    "DRREDDY.NS": {
        "company_name": "Dr. Reddy's Laboratories Ltd.",
        "sector": "Healthcare",
        "shares_outstanding": 166000000,
        "fallback_market_cap": 1000000000000
    },
    "EICHERMOT.NS": {
        "company_name": "Eicher Motors Ltd.",
        "sector": "Automobile",
        "shares_outstanding": 273000000,
        "fallback_market_cap": 1100000000000
    },
    "GRASIM.NS": {
        "company_name": "Grasim Industries Ltd.",
        "sector": "Materials",
        "shares_outstanding": 680000000,
        "fallback_market_cap": 1500000000000
    },
    "HCLTECH.NS": {
        "company_name": "HCL Technologies Ltd.",
        "sector": "IT",
        "shares_outstanding": 2710000000,
        "fallback_market_cap": 4000000000000
    },
    "HDFCBANK.NS": {
        "company_name": "HDFC Bank Ltd.",
        "sector": "Financial Services",
        "shares_outstanding": 7600000000,
        "fallback_market_cap": 12500000000000
    },
    "HDFCLIFE.NS": {
        "company_name": "HDFC Life Insurance Co. Ltd.",
        "sector": "Financial Services",
        "shares_outstanding": 2150000000,
        "fallback_market_cap": 1300000000000
    },
    "HEROMOTOCO.NS": {
        "company_name": "Hero MotoCorp Ltd.",
        "sector": "Automobile",
        "shares_outstanding": 200000000,
        "fallback_market_cap": 950000000000
    },
    "HINDALCO.NS": {
        "company_name": "Hindalco Industries Ltd.",
        "sector": "Metals",
        "shares_outstanding": 2240000000,
        "fallback_market_cap": 1400000000000
    },
    "HINDUNILVR.NS": {
        "company_name": "Hindustan Unilever Ltd.",
        "sector": "FMCG",
        "shares_outstanding": 2350000000,
        "fallback_market_cap": 5800000000000
    },
    "ICICIBANK.NS": {
        "company_name": "ICICI Bank Ltd.",
        "sector": "Financial Services",
        "shares_outstanding": 7000000000,
        "fallback_market_cap": 8200000000000
    },
    "INDUSINDBK.NS": {
        "company_name": "IndusInd Bank Ltd.",
        "sector": "Financial Services",
        "shares_outstanding": 778000000,
        "fallback_market_cap": 1000000000000
    },
    "INFY.NS": {
        "company_name": "Infosys Ltd.",
        "sector": "IT",
        "shares_outstanding": 4150000000,
        "fallback_market_cap": 6200000000000
    },
    "ITC.NS": {
        "company_name": "ITC Ltd.",
        "sector": "FMCG",
        "shares_outstanding": 12480000000,
        "fallback_market_cap": 5400000000000
    },
    "JSWSTEEL.NS": {
        "company_name": "JSW Steel Ltd.",
        "sector": "Metals",
        "shares_outstanding": 2440000000,
        "fallback_market_cap": 2200000000000
    },
    "KOTAKBANK.NS": {
        "company_name": "Kotak Mahindra Bank Ltd.",
        "sector": "Financial Services",
        "shares_outstanding": 1980000000,
        "fallback_market_cap": 3400000000000
    },
    "LT.NS": {
        "company_name": "Larsen & Toubro Ltd.",
        "sector": "Construction",
        "shares_outstanding": 1370000000,
        "fallback_market_cap": 4800000000000
    },
    "LTM.NS": {
        "company_name": "LTIMindtree Ltd.",
        "sector": "IT",
        "shares_outstanding": 296000000,
        "fallback_market_cap": 1500000000000
    },
    "M&M.NS": {
        "company_name": "Mahindra & Mahindra Ltd.",
        "sector": "Automobile",
        "shares_outstanding": 1240000000,
        "fallback_market_cap": 3100000000000
    },
    "MARUTI.NS": {
        "company_name": "Maruti Suzuki India Ltd.",
        "sector": "Automobile",
        "shares_outstanding": 314000000,
        "fallback_market_cap": 3800000000000
    },
    "NESTLEIND.NS": {
        "company_name": "Nestle India Ltd.",
        "sector": "FMCG",
        "shares_outstanding": 96400000,
        "fallback_market_cap": 2400000000000
    },
    "NTPC.NS": {
        "company_name": "NTPC Ltd.",
        "sector": "Energy",
        "shares_outstanding": 9690000000,
        "fallback_market_cap": 3300000000000
    },
    "ONGC.NS": {
        "company_name": "Oil & Natural Gas Corporation Ltd.",
        "sector": "Energy",
        "shares_outstanding": 12580000000,
        "fallback_market_cap": 3400000000000
    },
    "POWERGRID.NS": {
        "company_name": "Power Grid Corporation of India Ltd.",
        "sector": "Energy",
        "shares_outstanding": 9300000000,
        "fallback_market_cap": 2800000000000
    },
    "RELIANCE.NS": {
        "company_name": "Reliance Industries Ltd.",
        "sector": "Energy",
        "shares_outstanding": 6760000000,
        "fallback_market_cap": 19200000000000
    },
    "SBILIFE.NS": {
        "company_name": "SBI Life Insurance Co. Ltd.",
        "sector": "Financial Services",
        "shares_outstanding": 1000000000,
        "fallback_market_cap": 1500000000000
    },
    "SBIN.NS": {
        "company_name": "State Bank of India",
        "sector": "Financial Services",
        "shares_outstanding": 8920000000,
        "fallback_market_cap": 7200000000000
    },
    "SHRIRAMFIN.NS": {
        "company_name": "Shriram Finance Ltd.",
        "sector": "Financial Services",
        "shares_outstanding": 375000000,
        "fallback_market_cap": 1100000000000
    },
    "SUNPHARMA.NS": {
        "company_name": "Sun Pharmaceutical Industries Ltd.",
        "sector": "Healthcare",
        "shares_outstanding": 2390000000,
        "fallback_market_cap": 3600000000000
    },
    "TATACONSUM.NS": {
        "company_name": "Tata Consumer Products Ltd.",
        "sector": "FMCG",
        "shares_outstanding": 929000000,
        "fallback_market_cap": 1000000000000
    },
    "TMCV.NS": {
        "company_name": "Tata Motors Ltd.",
        "sector": "Automobile",
        "shares_outstanding": 3320000000,
        "fallback_market_cap": 3500000000000
    },
    "TATASTEEL.NS": {
        "company_name": "Tata Steel Ltd.",
        "sector": "Metals",
        "shares_outstanding": 12480000000,
        "fallback_market_cap": 1800000000000
    },
    "TCS.NS": {
        "company_name": "Tata Consultancy Services Ltd.",
        "sector": "IT",
        "shares_outstanding": 3610000000,
        "fallback_market_cap": 14200000000000
    },
    "TECHM.NS": {
        "company_name": "Tech Mahindra Ltd.",
        "sector": "IT",
        "shares_outstanding": 973000000,
        "fallback_market_cap": 1300000000000
    },
    "TITAN.NS": {
        "company_name": "Titan Company Ltd.",
        "sector": "Consumer Goods",
        "shares_outstanding": 887000000,
        "fallback_market_cap": 2900000000000
    },
    "ULTRACEMCO.NS": {
        "company_name": "UltraTech Cement Ltd.",
        "sector": "Materials",
        "shares_outstanding": 28800000,
        "fallback_market_cap": 2800000000000
    }
}


def _calculate_rsi_14(closes: list[float]) -> float:
    """Calculates Relative Strength Index (RSI) using standard formula."""
    if len(closes) < 15:
        return 50.0  # Default neutral
    
    diffs = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0.0 for d in diffs]
    losses = [-d if d < 0 else 0.0 for d in diffs]
    
    avg_gain = sum(gains) / 14.0
    avg_loss = sum(losses) / 14.0
    
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def fetch_single_ticker(ticker: str, meta: dict) -> dict:
    """
    Fetches raw 15-day historical price and volume data for a single ticker.
    Computes dynamic market cap, RSI, and volume average metrics.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=15d&interval=1d"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if not res_data.get("chart", {}).get("result"):
                raise ValueError("Empty chart result returned")
            
            result = res_data["chart"]["result"][0]
            chart_meta = result["meta"]
            
            # Extract current prices
            last_price = chart_meta.get("regularMarketPrice")
            prev_close = chart_meta.get("chartPreviousClose") or chart_meta.get("previousClose")
            
            # Extract arrays
            timestamps = result.get("timestamp", [])
            indicators = result.get("indicators", {}).get("quote", [{}])[0]
            closes = [c for c in indicators.get("close", []) if c is not None]
            volumes = [v for v in indicators.get("volume", []) if v is not None]
            
            # Validation
            if last_price is None or prev_close is None or not closes:
                raise ValueError("Missing critical fields in response")
            
            change = last_price - prev_close
            change_percent = (change / prev_close) * 100.0 if prev_close else 0.0
            volume = volumes[-1] if volumes else 0
            
            # Calculate dynamic market cap: Price * Shares Outstanding
            shares = meta.get("shares_outstanding", 0)
            market_cap = float(last_price * shares) if (last_price and shares) else float(meta.get("fallback_market_cap", 0.0))
            
            # Calculate RSI-14
            rsi = _calculate_rsi_14(closes)
            
            # Calculate 10-day volume average (excluding today)
            prev_volumes = volumes[:-1] if len(volumes) > 1 else volumes
            if prev_volumes:
                avg_vol_10 = sum(prev_volumes[-10:]) / len(prev_volumes[-10:])
            else:
                avg_vol_10 = volume
                
            volume_ratio = (volume / avg_vol_10) if avg_vol_10 > 0 else 1.0
            
            # Clean symbol for frontend consumption (strip .NS)
            clean_symbol = ticker.replace(".NS", "")
            
            return {
                "symbol": clean_symbol,
                "company_name": meta.get("company_name", clean_symbol),
                "last_price": float(last_price),
                "change_percent": float(change_percent),
                "volume": int(volume),
                "market_cap": float(market_cap),
                "sector": meta.get("sector", "Other"),
                "rsi_14": float(rsi),
                "volume_ratio": float(volume_ratio),
                "avg_vol_10": float(avg_vol_10)
            }
            
    except Exception as e:
        logger.error(f"Yahoo fetch failure for {ticker}: {str(e)}")
        # Return fallback mock/default item in case of request failures to prevent overall crash
        clean_symbol = ticker.replace(".NS", "")
        fallback_price = 100.0
        fallback_mc = float(meta.get("fallback_market_cap", 0.0))
        return {
            "symbol": clean_symbol,
            "company_name": meta.get("company_name", clean_symbol),
            "last_price": fallback_price,
            "change_percent": 0.0,
            "volume": 10000,
            "market_cap": fallback_mc,
            "sector": meta.get("sector", "Other"),
            "rsi_14": 50.0,
            "volume_ratio": 1.0,
            "avg_vol_10": 10000,
            "error": True
        }


def get_constituent_data(force_refresh: bool = False) -> list[dict]:
    """
    Returns aggregated constituent details for all Nifty 50 stocks.
    Uses in-memory caching with configurable TTL (CACHE_TTL).
    """
    global _constituent_cache, _cache_expiry
    now = time.time()
    
    if force_refresh or _constituent_cache is None or now > _cache_expiry:
        logger.info("Cache expired or empty. Refreshing Nifty 50 constituent data...")
        
        constituents = []
        # Query constituents in parallel to optimize API response times
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ticker = {
                executor.submit(fetch_single_ticker, ticker, meta): ticker
                for ticker, meta in NIFTY50_METADATA.items()
            }
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    constituents.append(data)
                except Exception as exc:
                    logger.error(f"Thread execution failed for {ticker}: {exc}")
                    
        _constituent_cache = constituents
        _cache_expiry = now + CACHE_TTL
        logger.info(f"Nifty 50 cache refreshed. Next refresh in {CACHE_TTL} seconds.")
    else:
        logger.info("Serving Nifty 50 constituent data from cache.")
        
    return _constituent_cache
