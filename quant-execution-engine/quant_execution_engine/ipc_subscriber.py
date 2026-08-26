import zmq
import zmq.asyncio
import json
import asyncio
import logging
from typing import Any

from quant_execution_engine.order_state import OrderManager
from quant_execution_engine.execution import BinanceUSDTExecutionAdapter

logger = logging.getLogger(__name__)

class ExecutionCommandListener:
    """
    Runs in the dedicated Execution Process. Listens for commands via ZeroMQ 
    and routes them to the asynchronous execution adapter.
    """
    
    def __init__(self, order_manager: OrderManager, adapter: BinanceUSDTExecutionAdapter, ipc_path: str = "ipc:///tmp/quant_exec_pipeline.ipc"):
        self.ipc_path = ipc_path
        self.order_manager = order_manager
        self.adapter = adapter
        
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PULL)
        self.socket.setsockopt(zmq.RCVHWM, 1000)
        self._running = False

    async def start_listening(self):
        self.socket.connect(self.ipc_path)
        self._running = True

        logger.info(f"ZeroMQ Listener connected to {self.ipc_path}")

        try:
            while self._running:
                raw_msg = await self.socket.recv_string()

                asyncio.create_task(self._process_command(raw_msg))

        except asyncio.CancelledError:
            logger.info("Listener task canceled.")

        finally:
            self.socket.close()
            self.context.term()

    async def _process_command(self, raw_msg: str):
        """Parses the ZeroMQ payload and interacts with the execution adapter."""

        try:
            cmd = json.loads(raw_msg)

            action = cmd.get("action")

            if action == "SUBMIT_ORDER":
                order = self.order_manager.create_order(
                    internal_id=cmd["internal_id"],
                    symbol=cmd["symbol"],
                    side=cmd["side"],
                    qty=cmd["qty"],
                    price=cmd["price"]
                )

                await self.adapter.submit_order(order)

            elif action == "CANCEL_ORDER":
                order = self.order_manager.active_orders.get(cmd["internal_id"])

                if order:
                    await self.adapter.cancel_order(order)
                else:
                    logger.warning(f"Cannot cancel unknown order: {cmd['internal_id']}")

        except json.JSONDecodeError:
            logger.error("Received malformed command payload.")

        except ValueError as e:
            logger.error(f"Execution Error: {e}")

    def stop(self):
        self._running = False