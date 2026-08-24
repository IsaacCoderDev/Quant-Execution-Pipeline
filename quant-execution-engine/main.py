import asyncio
import logging
from quant_execution_engine.ring_buffer import TickRingBuffer
from quant_execution_engine.normalizer import BinanceTickNormalizer
from quant_execution_engine.feed_handler import MarketDataFeed

logging.basicConfig(level=logging.INFO)

async def main():
    ring_buffer = TickRingBuffer(capacity=10_000)
    
    normalizer = BinanceTickNormalizer()
    
    feed = MarketDataFeed(
        url="wss://stream.binance.com:9443/ws/btcusdt@bookTicker",
        normalizer=normalizer,
        on_tick_callback=ring_buffer.push
    )
    
    feed.start()
    
    try:

        while True:
            await asyncio.sleep(5)

            if not ring_buffer.is_full:
                print(f"Buffer filled: {len(ring_buffer)} / 10000")

            else:
                latest = ring_buffer.get_latest()

                print(f"Latest BTCUSDT Bid: {latest[1]} | Ask: {latest[3]}")
    except KeyboardInterrupt:
        print("Shutting down...")

        feed.stop()

if __name__ == "__main__":
    asyncio.run(main())