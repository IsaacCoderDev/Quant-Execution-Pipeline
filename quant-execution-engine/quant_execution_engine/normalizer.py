import json
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class BinanceTickNormalizer:
    """
    Normalizes raw Binance Book Ticker (BBA) streams into a standard tuple:
    (timestamp, bid_price, bid_qty, ask_price, ask_qty)
    """
    
    @staticmethod
    def normalize(raw_payload: str) -> Optional[Tuple[float, float, float, float, float]]:
        try:
            data = json.loads(raw_payload)
            
            return (
                float(data['T']),
                float(data['b']),
                float(data['B']),
                float(data['a']),
                float(data['A'])
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.debug(f"Dropped malformed payload: {raw_payload}. Error: {e}")

            return None
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON: {raw_payload}")

            return None