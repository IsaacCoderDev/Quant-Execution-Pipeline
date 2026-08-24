import asyncio
import aiohttp
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class MarketDataFeed:
    """
    Resilient WebSocket client that ingests market data, normalizes it, 
    and pushes it to a decoupled data structure via a callback.
    """
    
    def __init__(self, url: str, normalizer: Any, on_tick_callback: Callable):
        self.url = url
        self.normalizer = normalizer
        self.on_tick_callback = on_tick_callback
        self._running = False
        self._task = None

    async def connect(self) -> None:
        self._running = True
        backoff = 1.0

        async with aiohttp.ClientSession() as session:

            while self._running:
                try:
                    logger.info(f"Attempting connection to {self.url}...")
                    
                    async with session.ws_connect(self.url, heartbeat=10.0) as ws:
                        logger.info("WebSocket connected successfully.")

                        backoff = 1.0
                        
                        async for msg in ws:
                            if not self._running:
                                break
                                
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                
                                parsed_tick = self.normalizer.normalize(msg.data)
                                
                                if parsed_tick:
                                    self.on_tick_callback(*parsed_tick)
                                    
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                logger.warning("WebSocket closed by remote server.")

                                break
                                
                except aiohttp.ClientError as e:
                    logger.error(f"Network error: {e}")

                except asyncio.TimeoutError:
                    logger.error("Connection timed out.")

                except Exception as e:
                    logger.exception(f"Unexpected error in feed handler: {e}")

                if self._running:
                    logger.warning(f"Reconnecting in {backoff} seconds...")

                    await asyncio.sleep(backoff)

                    backoff = min(backoff * 2, 60.0)

    def start(self) -> None:
        """Schedules the connection loop on the current asyncio event loop."""

        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.connect())

    def stop(self) -> None:
        """Triggers a graceful shutdown of the connection loop."""

        self._running = False

        if self._task:
            self._task.cancel()