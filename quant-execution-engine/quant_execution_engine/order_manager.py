from typing import Dict
import logging
from quant_execution_engine.order_state import OrderStateMachine, OrderStatus

logger = logging.getLogger(__name__)

class OrderManager:
    """
    Maintains the state of all live orders. Provides O(1) lookups for the execution layer.
    """

    def __init__(self):
        self.active_orders: Dict[str, OrderStateMachine] = {}

    def create_order(self, internal_id: str, symbol: str, side: str, qty: float, price: float) -> OrderStateMachine:

        if internal_id in self.active_orders:
            raise ValueError(f"Order {internal_id} already exists.")
            
        order = OrderStateMachine(internal_id, symbol, side, qty, price)

        self.active_orders[internal_id] = order

        return order

    def update_from_exchange_event(self, internal_id: str, event_type: str, exchange_id: str = None, filled_qty: float = 0.0) -> None:
        """
        Processes callbacks from the exchange WebSocket (e.g. 'ExecutionReport').
        """

        if internal_id not in self.active_orders:
            logger.warning(f"Received event for unknown order: {internal_id}")

            return
            
        order = self.active_orders[internal_id]
        
        if exchange_id and not order.exchange_id:
            order.exchange_id = exchange_id

        try:
            
            match event_type:
                case "NEW":
                    order.transition_to(OrderStatus.OPEN)

                case "PARTIALLY_FILLED":
                    order.filled_qty += filled_qty
                    order.transition_to(OrderStatus.PARTIAL_FILL)

                case "FILLED":
                    order.filled_qty += filled_qty
                    order.transition_to(OrderStatus.FILLED)

                case "CANCELED":
                    order.transition_to(OrderStatus.CANCELED)

                case "REJECTED":
                    order.transition_to(OrderStatus.REJECTED)

        except ValueError as e:
            logger.error(f"State machine violation on {internal_id}: {e}")

        if order.is_terminal:
            del self.active_orders[internal_id]