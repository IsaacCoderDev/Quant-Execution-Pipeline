import numpy as np


class LiquidityProfiler:
    """
    A purely functional, vectorized metrics engine for high-frequency tick data.
    Assumes input `window` is a 2D NumPy array structured as:
    [timestamp, bid_price, bid_qty, ask_price, ask_qty]
    """

    @staticmethod
    def calculate_obi(window: np.ndarray) -> np.ndarray:
        """
        Calculates Order Book Imbalance: (BidQty - AskQty) / (BidQty + AskQty)
        Returns an array of floats between -1.0 and 1.0.
        """
        
        bid_qty = window[:, 2]
        ask_qty = window[:, 4]

        total_qty = bid_qty + ask_qty
        
        obi = np.divide(
            (bid_qty - ask_qty),
            total_qty,
            out=np.zeros_like(total_qty),
            where=total_qty != 0
        )

        return obi

    @staticmethod
    def calculate_spread(window: np.ndarray) -> np.ndarray:
        """
        Calculates the dynamic bid-ask spread in absolute price terms.
        """

        bid_price = window[:, 1]
        ask_price = window[:, 3]

        return ask_price - bid_price

    @staticmethod
    def calculate_micro_price(window: np.ndarray) -> np.ndarray:
        """
        Calculates the volume-weighted micro-price.
        Micro-price adjusts the mid-price based on where the heavy liquidity sits.
        """

        bid_price = window[:, 1]
        bid_qty = window[:, 2]
        ask_price = window[:, 3]
        ask_qty = window[:, 4]
        
        total_qty = bid_qty + ask_qty
        
        bid_weight = np.divide(bid_qty, total_qty, out=np.zeros_like(total_qty), where=total_qty!=0)
        ask_weight = np.divide(ask_qty, total_qty, out=np.zeros_like(total_qty), where=total_qty!=0)
        
        return (bid_price * ask_weight) + (ask_price * bid_weight)

    @classmethod
    def get_market_snapshot(cls, window: np.ndarray) -> dict:
        """
        Returns a summarized dictionary of the current market state for the strategy engine.
        """

        if len(window) == 0:
            return {}

        obi_array = cls.calculate_obi(window)
        spread_array = cls.calculate_spread(window)
        
        return {
            "current_obi": float(obi_array[-1]),
            "mean_obi_100": float(np.mean(obi_array[-100:] if len(obi_array) >= 100 else obi_array)),
            "current_spread": float(spread_array[-1]),
            "is_spread_widening": float(spread_array[-1]) > float(np.mean(spread_array)),
        }