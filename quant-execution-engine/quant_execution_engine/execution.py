import time
import hmac
import hashlib
import urllib.parse
import aiohttp
import logging
from typing import Dict, Any

from quant_execution_engine.order_state import OrderStateMachine, OrderStatus
from quant_execution_engine.precision import USDTPrecisionFormatter

logger = logging.getLogger(__name__)

class BinanceUSDTExecutionAdapter:
    """
    Asynchronous REST adapter for routing orders to Binance USDT Spot markets.
    Tightly coupled with the OrderStateMachine to guarantee state integrity.
    """
    
    BASE_URL = "https://api.binance.com"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret.encode('utf-8')
        self.session: aiohttp.ClientSession | None = None

    async def start(self):
        """Initializes the connection pool."""

        self.session = aiohttp.ClientSession(headers={"X-MBX-APIKEY": self.api_key})

    async def close(self):
        """Tears down the connection pool."""

        if self.session:
            await self.session.close()

    def _sign_payload(self, payload: Dict[str, Any]) -> str:
        """Generates the HMAC SHA256 signature required by the exchange."""

        query_string = urllib.parse.urlencode(payload)
        signature = hmac.new(self.api_secret, query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        return f"{query_string}&signature={signature}"

    async def submit_order(self, order: OrderStateMachine) -> bool:
        """
        Formats, signs, and fires the order. Transitions the FSM state.
        """

        if not self.session:
            raise RuntimeError("Adapter session not started.")

        str_price = USDTPrecisionFormatter.format_price(order.symbol, order.price)
        str_qty = USDTPrecisionFormatter.format_qty(order.symbol, order.qty)

        payload = {
            "symbol": order.symbol,
            "side": order.side,
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": str_qty,
            "price": str_price,
            "newClientOrderId": order.internal_id, # Link exchange to our FSM
            "timestamp": int(time.time() * 1000)
        }

        signed_query = self._sign_payload(payload)
        url = f"{self.BASE_URL}/api/v3/order?{signed_query}"

        order.transition_to(OrderStatus.SUBMITTED)

        try:

            async with self.session.post(url) as response:
                data = await response.json()
                
                if response.status == 200:
                    logger.info(f"Order {order.internal_id} successfully routed. Exchange ID: {data.get('orderId')}")

                    return True
                else:
                    logger.error(f"Exchange rejected order {order.internal_id}: {data}")

                    order.transition_to(OrderStatus.REJECTED)

                    return False
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error routing order {order.internal_id}: {e}")

            return False

    async def cancel_order(self, order: OrderStateMachine) -> bool:
        """
        Cancels an active order safely using the FSM.
        """

        if not order.is_cancelable:
            logger.warning(f"Order {order.internal_id} is not in a cancelable state.")

            return False

        payload = {
            "symbol": order.symbol,
            "origClientOrderId": order.internal_id,
            "timestamp": int(time.time() * 1000)
        }

        signed_query = self._sign_payload(payload)
        url = f"{self.BASE_URL}/api/v3/order?{signed_query}"

        order.transition_to(OrderStatus.CANCEL_PENDING)

        try:
            async with self.session.delete(url) as response:

                if response.status == 200:
                    logger.info(f"Cancel request sent for {order.internal_id}.")

                    return True
                else:
                    logger.error(f"Failed to cancel {order.internal_id}: {await response.text()}")

                    return False

        except aiohttp.ClientError as e:
            logger.error(f"Network error canceling order {order.internal_id}: {e}")

            return False