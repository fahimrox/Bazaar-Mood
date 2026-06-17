"""ATM strike detection utilities for the Fyers option chain engine."""

def get_atm_strike(spot_price: float, strikes: list[float]) -> float:
    """
    Returns the strike price closest to spot_price.
    Ties are broken by taking the lower strike.
    """
    if not strikes:
        return 0.0
    return min(strikes, key=lambda k: (abs(k - spot_price), k))
