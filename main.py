import asyncio

from logger.logger import log
from bot.start import TeleBot
from middleware.proxy import Proxy

from config.config import BOT_TOKEN

if __name__ == "__main__":
    try:
        asyncio.run(TeleBot.start(BOT_TOKEN))
        pass
    except (KeyboardInterrupt, SystemExit):
        log.warning("Бот остановлен пользователем")