import math

class USDTPrecisionFormatter:
    """
    Enforces strict exchange precision rules to prevent rejected orders.
    In a production system, these tick/step sizes are fetched once dynamically at startup.
    """
    
    _RULES = {
        "BTCUSDT": (2, 5),
        "ETHUSDT": (2, 4),
    }

    @classmethod
    def format_price(cls, symbol: str, price: float) -> str:
        """Rounds price to the correct tick size and returns a formatted string."""

        decimals = cls._RULES.get(symbol, (2, 2))[0]

        factor = 10 ** decimals
        rounded = math.floor(price * factor) / factor

        return f"{rounded:.{decimals}f}"

    @classmethod
    def format_qty(cls, symbol: str, qty: float) -> str:
        """Rounds quantity to the correct step size and returns a formatted string."""

        decimals = cls._RULES.get(symbol, (2, 2))[1]
        factor = 10 ** decimals

        rounded = math.floor(qty * factor) / factor

        return f"{rounded:.{decimals}f}"