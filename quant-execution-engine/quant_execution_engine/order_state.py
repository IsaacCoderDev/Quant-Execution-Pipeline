from enum import Enum, auto
import time
import logging

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    """Explicit lifecycle states for a live market order."""

    NEW = auto()
    SUBMITTED = auto()
    OPEN = auto()
    PARTIAL_FILL = auto()
    FILLED = auto()
    CANCEL_PENDING = auto()
    CANCELED = auto()
    REJECTED = auto()

class OrderStateMachine:
    """
    Manages the lifecycle of a single order. Enforces strict state transitions
    to prevent ghost orders and double-execution.
    """

    _VALID_TRANSITIONS = {
        OrderStatus.NEW: [OrderStatus.SUBMITTED, OrderStatus.REJECTED],
        OrderStatus.SUBMITTED: [OrderStatus.OPEN, OrderStatus.REJECTED, OrderStatus.FILLED, OrderStatus.PARTIAL_FILL],
        OrderStatus.OPEN: [OrderStatus.PARTIAL_FILL, OrderStatus.FILLED, OrderStatus.CANCEL_PENDING],
        OrderStatus.PARTIAL_FILL: [OrderStatus.PARTIAL_FILL, OrderStatus.FILLED, OrderStatus.CANCEL_PENDING],
        OrderStatus.CANCEL_PENDING: [OrderStatus.CANCELED, OrderStatus.FILLED, OrderStatus.REJECTED],

        OrderStatus.FILLED: [],
        OrderStatus.CANCELED: [],
        OrderStatus.REJECTED: [],
    }

    def __init__(self, internal_order_id: str, symbol: str, side: str, qty: float, price: float):
        self.internal_id = internal_order_id
        self.exchange_id = None
        self.symbol = symbol
        self.side = side.upper()
        self.qty = qty
        self.price = price
        
        self.status = OrderStatus.NEW
        self.filled_qty = 0.0
        self.created_at = time.time()
        self.last_update = self.created_at

    def transition_to(self, new_status: OrderStatus) -> bool:
        """
        Attempts to transition the order to a new state.
        Raises a ValueError if the transition is illegal, preventing ghost states.
        """

        if new_status not in self._VALID_TRANSITIONS[self.status]:
            error_msg = f"Illegal transition for {self.internal_id}: {self.status.name} -> {new_status.name}"
            logger.critical(error_msg)
            raise ValueError(error_msg)

        logger.debug(f"Order {self.internal_id} transitioning: {self.status.name} -> {new_status.name}")

        self.status = new_status
        self.last_update = time.time()

        return True

    @property
    def is_terminal(self) -> bool:
        return self.status in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED)

    @property
    def is_cancelable(self) -> bool:
        return self.status in (OrderStatus.OPEN, OrderStatus.PARTIAL_FILL, OrderStatus.SUBMITTED)