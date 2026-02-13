from aiogram import Bot
import asyncio
from logger.logger import logger

log = logger(__name__) 

async def keep_alive_ping(bot: Bot):
    while True:
        try:
            await bot.get_me()
            log.debug("BOT ALIVE")
        except Exception as e:
            log.error("ERROR", e)
        await asyncio.sleep(30)