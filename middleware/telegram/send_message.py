import asyncio
import logging

from aiogram import F
from aiogram.types import Message, BufferedInputFile
from aiogram.exceptions import TelegramRetryAfter, TelegramNetworkError, TelegramBadRequest

logger = logging.getLogger(__name__)

from config.config import IMAGE_EXTS_LOWER
from config.config import VIDEO_EXTS_LOWER
from config.config import REQUEST_TIMEOUT
from config.config import SLEEP_BETWEEN_FILES

async def send_files_one_by_one(message: Message, files: list[tuple[bytes, str]]) -> int:
    sent = 0
    for data, name in files:
        file_io = BufferedInputFile(file=data, filename=name)
        lower = name.lower()

        try:
            if lower.endswith(IMAGE_EXTS_LOWER):
                await message.answer_photo(photo=file_io, request_timeout=REQUEST_TIMEOUT)
            elif lower.endswith(VIDEO_EXTS_LOWER):
                await message.answer_video(video=file_io, request_timeout=REQUEST_TIMEOUT)
            else:
                await message.answer_document(document=file_io, request_timeout=REQUEST_TIMEOUT)

            sent += 1
            await asyncio.sleep(SLEEP_BETWEEN_FILES)

        except TelegramRetryAfter as rte:
            await asyncio.sleep(rte.retry_after + 1)
        except (TelegramNetworkError, TelegramBadRequest) as e:
            logger.error("Не удалось отправить %s: %s", name, e)
            await message.answer(f"Не получилось отправить {name}")
        except Exception as e:
            logger.exception("Ошибка отправки файла %s", name)
            await message.answer(f"Ошибка при отправке {name}")

    return sent