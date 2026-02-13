import asyncio
from aiogram.exceptions import TelegramNetworkError, TelegramBadRequest
async def send_with_retry(factory, max_retries=3, base_delay=2):
    for attempt in range(max_retries):
        try:
            coro = factory() 
            return await coro
        except (TelegramNetworkError, TelegramBadRequest) as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(base_delay * (attempt + 1))
        except Exception as e:
            raise