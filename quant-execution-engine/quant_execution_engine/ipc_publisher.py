import zmq
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ExecutionCommandPublisher:
    """
    Pushes execution commands from the Strategy Engine to the decoupled Execution Node.
    Uses ZeroMQ PUSH/PULL pattern over Unix Domain Sockets for microsecond IPC.
    """
    
    def __init__(self, ipc_path: str = "ipc:///tmp/quant_exec_pipeline.ipc"):
        self.ipc_path = ipc_path
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUSH)
        
        self.socket.setsockopt(zmq.SNDHWM, 1000)
        
    def start(self):
        self.socket.bind(self.ipc_path)

        logger.info(f"ZeroMQ Publisher bound to {self.ipc_path}")

    def send_order_command(self, internal_id: str, symbol: str, side: str, qty: float, price: float):
        """Serializes and fires an order command to the execution node."""

        command = {
            "action": "SUBMIT_ORDER",
            "internal_id": internal_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price
        }

        self.socket.send_string(json.dumps(command))

        logger.debug(f"Pushed SUBMIT_ORDER command for {internal_id}")

    def send_cancel_command(self, internal_id: str, symbol: str):
        command = {
            "action": "CANCEL_ORDER",
            "internal_id": internal_id,
            "symbol": symbol
        }

        self.socket.send_string(json.dumps(command))

        logger.debug(f"Pushed CANCEL_ORDER command for {internal_id}")

    def close(self):
        self.socket.close()
        self.context.term()