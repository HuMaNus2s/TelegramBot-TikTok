import asyncio

from logger.logger import logger
from bot.start import TeleBot

log = logger(__name__)

try:
    from config.config import BOT_TOKEN
except ImportError:
    log.error("TOKEN NOT FOUND")

if __name__ == "__main__":
    try:
        log.info("BOT STARTING")
        asyncio.run(TeleBot.start(BOT_TOKEN))
        pass
    except (KeyboardInterrupt, SystemExit):
        log.warning("Бот остановлен пользователем")
    except NameError:
        log.error("TOKEN NOT FOUND")