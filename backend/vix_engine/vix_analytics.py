import logging
import urllib.request
import json
import time
import math
from datetime import datetime

# Configure logger
logger = logging.getLogger("BazaarMood.VixEngine")

# Cache configuration
CACHE_TTL = 300  # 5 minutes cache TTL
_cache = {}

def pearson_correlation(x: list[float], y: list[float]) -> float:
    """Calculates Pearson's correlation coefficient (r) between two lists."""
    n = len(x)
    if n < 2 or n != len(y):
        return 0.0
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    den_y = sum((y[i] - mean_y) ** 2 for i in range(n))
    
    if den_x == 0.0 or den_y == 0.0:
        return 0.0
        
    return float(num / math.sqrt(den_x * den_y))


def fetch_yahoo_chart_data(ticker: str, range_val: str) -> dict:
    """Helper to fetch chart data from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_val}&interval=1d"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("chart", {}).get("result", [{}])[0]
    except Exception as e:
        logger.error(f"Yahoo Finance fetch failed for ticker {ticker}: {e}")
    return {}


def calculate_vix_analytics() -> dict:
    """
    Computes India VIX volatility analytics, including moving averages, percentile ranking,
    expected daily move range, daily VIX shock levels, correlation metrics, and option environments.
    """
    # ── Step 1: Fetch VIX 1-year Historical Daily Closes ──────────────────────
    vix_result = fetch_yahoo_chart_data("^INDIAVIX", "1y")
    vix_timestamps = vix_result.get("timestamp") or []
    vix_quotes = vix_result.get("indicators", {}).get("quote", [{}])[0]
    vix_closes = [c for c in vix_quotes.get("close", []) if c is not None]

    if not vix_closes:
        logger.error("VIX closes are empty or failed to load. Applying safe fallbacks.")
        return get_vix_fallback_data()

    # Current Price, Previous Price, Daily Change %
    current_vix = float(vix_closes[-1])
    previous_vix = float(vix_closes[-2]) if len(vix_closes) >= 2 else current_vix
    vix_change_pct = ((current_vix - previous_vix) / previous_vix) * 100.0 if previous_vix else 0.0

    # Moving Averages
    sma_5 = sum(vix_closes[-5:]) / min(5, len(vix_closes))
    sma_20 = sum(vix_closes[-20:]) / min(20, len(vix_closes))
    sma_50 = sum(vix_closes[-50:]) / min(50, len(vix_closes))

    # 52 Week High and Low
    high_52w = float(max(vix_closes))
    low_52w = float(min(vix_closes))

    # Percentile Analysis (over the last 252 trading days)
    lookback_252 = vix_closes[-252:]
    sorted_lookback = sorted(lookback_252)
    less_count = sum(1 for c in sorted_lookback if c < current_vix)
    vix_percentile = (less_count / len(sorted_lookback)) * 100.0

    # ── Step 2: Determine VIX Shock Detection ────────────────────────────────
    vix_shock = False
    shock_level = "None"
    if vix_change_pct > 30.0:
        vix_shock = True
        shock_level = "Extreme"
    elif vix_change_pct > 20.0:
        vix_shock = True
        shock_level = "High"
    elif vix_change_pct > 10.0:
        vix_shock = True
        shock_level = "Moderate"

    # ── Step 3: Determine VIX Trend & Volatility Regime ──────────────────────
    # Trend
    if current_vix > sma_20 * 1.025 and sma_20 > sma_50:
        vix_trend = "Rising"
    elif current_vix < sma_20 * 0.975 and sma_20 < sma_50:
        vix_trend = "Falling"
    else:
        vix_trend = "Flat / Consolidating"

    # Volatility Regime
    if current_vix < 11.5:
        vol_regime = "Complacency / Extremely Low"
        market_risk = "Low"
    elif current_vix < 15.0:
        vol_regime = "Low / Normal"
        market_risk = "Normal"
    elif current_vix <= 19.0:
        vol_regime = "Elevated / Moderate"
        market_risk = "Moderate"
    else:
        vol_regime = "Extreme / Panic"
        market_risk = "High"

    # ── Step 4: Determine Option & Trading Environment ────────────────────────
    # Expected daily move percentage = VIX / sqrt(252)
    expected_daily_move_pct = current_vix / math.sqrt(252.0)
    if expected_daily_move_pct < 0.75:
        expected_move_class = "Low Range"
    elif expected_daily_move_pct < 1.25:
        expected_move_class = "Moderate Range"
    else:
        expected_move_class = "High Range"

    # Option Environment
    if current_vix < 15.0:
        opt_env = "Option Seller Advantage (Low IV)"
    elif current_vix <= 19.0:
        opt_env = "Balanced"
    else:
        opt_env = "Option Buyer Advantage (High IV)"

    # Trading Environment
    if current_vix > 19.0 or vix_percentile > 80.0:
        if vix_shock or vix_trend == "Rising":
            trading_env = "Premium Buying Environment"
        else:
            trading_env = "Premium Selling Environment"
    elif current_vix < 11.5 or vix_percentile < 20.0:
        if vix_trend == "Rising":
            trading_env = "Premium Buying Environment"
        else:
            trading_env = "Premium Selling Environment"
    else:
        trading_env = "Balanced Environment"

    # ── Step 5: Pearson Correlation Coefficients (NIFTY & BANKNIFTY vs VIX) ───
    corr_nifty = -0.70
    corr_banknifty = -0.65
    try:
        nifty_result = fetch_yahoo_chart_data("^NSEI", "1mo")
        bank_result = fetch_yahoo_chart_data("^NSEBANK", "1mo")
        
        vix_map = map_closes_by_date(vix_timestamps, vix_quotes.get("close", []))
        
        # Nifty alignment
        if nifty_result.get("timestamp"):
            nifty_quotes = nifty_result.get("indicators", {}).get("quote", [{}])[0]
            nifty_map = map_closes_by_date(nifty_result["timestamp"], nifty_quotes.get("close", []))
            common_nifty_dates = sorted(list(set(vix_map.keys()) & set(nifty_map.keys())))[-20:]
            if len(common_nifty_dates) >= 5:
                v_aligned = [vix_map[d] for d in common_nifty_dates]
                n_aligned = [nifty_map[d] for d in common_nifty_dates]
                corr_nifty = pearson_correlation(v_aligned, n_aligned)
                
        # Bank Nifty alignment
        if bank_result.get("timestamp"):
            bank_quotes = bank_result.get("indicators", {}).get("quote", [{}])[0]
            bank_map = map_closes_by_date(bank_result["timestamp"], bank_quotes.get("close", []))
            common_bank_dates = sorted(list(set(vix_map.keys()) & set(bank_map.keys())))[-20:]
            if len(common_bank_dates) >= 5:
                v_aligned = [vix_map[d] for d in common_bank_dates]
                b_aligned = [bank_map[d] for d in common_bank_dates]
                corr_banknifty = pearson_correlation(v_aligned, b_aligned)
    except Exception as ec:
        logger.warning(f"Failed to calculate indices vs VIX correlations: {ec}")

    # Confidence calculation based on data availability
    confidence = 80 if len(vix_closes) >= 200 else 60

    return {
        "current_vix": round(current_vix, 2),
        "previous_vix": round(previous_vix, 2),
        "vix_change_percent": round(vix_change_pct, 2),
        "vix_trend": vix_trend,
        "volatility_regime": vol_regime,
        "market_risk": market_risk,
        "option_environment": opt_env,
        "expected_move": expected_move_class,
        "confidence": confidence,
        "vix_percentile": round(vix_percentile, 1),
        "vix_shock": vix_shock,
        "shock_level": shock_level,
        "trading_environment": trading_env,
        "details": {
            "sma_5": round(sma_5, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "high_52w": round(high_52w, 2),
            "low_52w": round(low_52w, 2),
            "correlation_nifty_vix": round(corr_nifty, 3),
            "correlation_banknifty_vix": round(corr_banknifty, 3),
            "expected_daily_move_pct": round(expected_daily_move_pct, 3)
        }
    }


def map_closes_by_date(timestamps: list, closes: list) -> dict:
    """Maps daily closing price lists to string dates YYYY-MM-DD for joining."""
    res = {}
    for t, c in zip(timestamps, closes):
        if t is not None and c is not None:
            date_str = datetime.fromtimestamp(int(t)).strftime("%Y-%m-%d")
            res[date_str] = float(c)
    return res


def get_vix_fallback_data() -> dict:
    """Safe fallback dictionary returned in case of connection or scrape failures."""
    return {
        "current_vix": 15.0,
        "previous_vix": 15.0,
        "vix_change_percent": 0.0,
        "vix_trend": "Flat / Consolidating",
        "volatility_regime": "Low / Normal",
        "market_risk": "Normal",
        "option_environment": "Balanced",
        "expected_move": "Moderate Range",
        "confidence": 50,
        "vix_percentile": 50.0,
        "vix_shock": False,
        "shock_level": "None",
        "trading_environment": "Balanced Environment",
        "details": {
            "sma_5": 15.0,
            "sma_20": 15.0,
            "sma_50": 15.0,
            "high_52w": 22.0,
            "low_52w": 10.0,
            "correlation_nifty_vix": -0.70,
            "correlation_banknifty_vix": -0.65,
            "expected_daily_move_pct": 0.945
        }
    }


def get_vix_analytics() -> dict:
    """
    Cached accessor method to prevent Yahoo Finance throttling.
    Caches VIX calculations for 300 seconds (5 minutes).
    """
    now = time.time()
    cache_key = "VIX_GLOBAL"
    if cache_key in _cache:
        cached_val, expiry = _cache[cache_key]
        if now < expiry:
            logger.info("Serving VIX Analytics from cache.")
            return cached_val
            
    data = calculate_vix_analytics()
    _cache[cache_key] = (data, now + CACHE_TTL)
    return data
