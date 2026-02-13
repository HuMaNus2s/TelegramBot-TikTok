import asyncio
import time
import hashlib
import os

from aiogram import F
from aiogram.types import Message, BufferedInputFile
from aiogram.exceptions import TelegramRetryAfter, TelegramNetworkError, TelegramBadRequest

from middleware.hash.sha256.hash_ext import hash_ext
from middleware.wraper.send_retry import send_with_retry

from logger.logger import logger

log = logger(__name__)

from config.config import REQUEST_TIMEOUT
from config.config import SLEEP_BETWEEN_FILES
from config.config import IMAGE_EXTS_LOWER
from config.config import VIDEO_EXTS_LOWER

async def send_files_one_by_one(message: Message, files: list[tuple[bytes, str]]) -> int:
    sent, send_time = 0, 0

    for data, name in files:
        try:
            start = time.perf_counter()
            name = hash_ext(name)
            if name.endswith(IMAGE_EXTS_LOWER):
                await send_with_retry(
                    lambda: message.answer_photo(
                        BufferedInputFile(data, filename=name),
                        request_timeout=REQUEST_TIMEOUT
                    )
                )
            elif name.endswith(VIDEO_EXTS_LOWER):
                await send_with_retry(
                    lambda: message.answer_video(
                        BufferedInputFile(data, filename=name),
                        request_timeout=REQUEST_TIMEOUT
                    )
                )
            else: 
                await send_with_retry(
                    lambda: message.answer_document(
                        BufferedInputFile(data, filename=name),
                        request_timeout=REQUEST_TIMEOUT
                    )
                )
            end = time.perf_counter()
            send_time += end - start
            sent += 1
            log.info("FILE: %s | SEND: %.2fs", name, send_time)      
            await asyncio.sleep(SLEEP_BETWEEN_FILES)

        except TelegramRetryAfter as rte:
            await asyncio.sleep(rte.retry_after + 1)
        except (TelegramNetworkError, TelegramBadRequest) as e:
            log.error("Не удалось отправить %s: %s", name, e)
            await message.answer(f"Извините, не получилось отправить файл 😢")
        except Exception as e:
            log.exception("Ошибка отправки файла %s", name)
            await message.answer(f"Извините, не получилось отправить файл 😢")

    return sent, send_time