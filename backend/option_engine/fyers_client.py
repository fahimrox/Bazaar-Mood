import os
from fastapi import HTTPException
from fyers_apiv3 import fyersModel


def get_fyers_credentials():
    """Read Fyers credentials from environment variables."""
    client_id = os.getenv("FYERS_CLIENT_ID")
    access_token = os.getenv("FYERS_ACCESS_TOKEN")

    if not client_id or not access_token:
        raise HTTPException(
            status_code=503,
            detail="Fyers API credentials missing or invalid. Please check your .env configuration."
        )
    return client_id, access_token


class FyersClient:
    """
    Wrapper around the official fyers-apiv3 SDK.

    Authorization format confirmed from SDK source:
        header = "{client_id}:{access_token}"
        Additional headers added by SDK: {"version": "3", "Content-Type": "application/json"}

    Options chain endpoint (from SDK Config):
        DATA_API = "https://api-t1.fyers.in/data"
        option_chain = "/options-chain-v3"
        → Full URL: https://api-t1.fyers.in/data/options-chain-v3
    """

    # Symbol map: frontend shorthand → Fyers-required format
    SYMBOL_MAP = {
        "NIFTY":       "NSE:NIFTY50-INDEX",
        "NIFTY50":     "NSE:NIFTY50-INDEX",
        "BANKNIFTY":   "NSE:NIFTYBANK-INDEX",
        "MIDCPNIFTY":  "NSE:MIDCPNIFTY-INDEX",
        "FINNIFTY":    "NSE:FINNIFTY-INDEX",
        "SENSEX":      "BSE:SENSEX-INDEX",
    }

    def _get_fyers_model(self) -> fyersModel.FyersModel:
        """Instantiate a fresh FyersModel using current env credentials."""
        client_id, access_token = get_fyers_credentials()
        return fyersModel.FyersModel(
            client_id=client_id,
            token=access_token,
            is_async=False,
            log_path=""        # suppress file logging
        )

    def fetch_raw_option_chain(self, symbol: str, timestamp: str = "") -> dict:
        """
        Fetch live option chain data from Fyers via the official SDK.

        The SDK builds the Authorization header as "{client_id}:{access_token}"
        and automatically appends the required "version: 3" header.

        Args:
            symbol:    Frontend shorthand e.g. "NIFTY", "BANKNIFTY".
            timestamp: Fyers Unix timestamp string for a specific expiry
                       (from expiryData[n]["expiry"]).  "" = nearest expiry.

        Returns the raw `data` dict from Fyers response on success.
        Raises HTTPException on auth/network/API errors.
        """
        fyers_symbol = self.SYMBOL_MAP.get(
            symbol.upper().strip().replace(" ", ""),
            symbol
        )

        fyers = self._get_fyers_model()

        # SDK optionchain() accepts:
        #   symbol     : str       e.g. "NSE:NIFTY50-INDEX"
        #   strikecount: int       ITM + ATM + OTM strikes per side
        #   timestamp  : str|int   "" = nearest expiry; Unix ts = specific expiry
        #   greeks     : str       "1" → include delta/gamma/theta/vega/iv
        payload = {
            "symbol":      fyers_symbol,
            "strikecount": 30,
            "timestamp":   timestamp,
            "greeks":      "1",
        }

        try:
            response = fyers.optionchain(data=payload)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Fyers SDK raised an exception: {str(e)}"
            )

        # Fyers returns {"s": "ok", "data": {...}} on success
        if not isinstance(response, dict):
            raise HTTPException(
                status_code=503,
                detail="Unexpected non-dict response from Fyers SDK."
            )

        status = response.get("s") or response.get("code")

        if status not in ("ok", 200):
            # Surface the exact Fyers error message for easier debugging
            fyers_message = (
                response.get("message")
                or response.get("errmsg")
                or response.get("msg")
                or str(response)
            )
            raise HTTPException(
                status_code=503,
                detail=f"Fyers API error ({status}): {fyers_message}"
            )

        data = response.get("data")
        if not data:
            raise HTTPException(
                status_code=503,
                detail="Fyers returned an empty 'data' field in option chain response."
            )

        return data
