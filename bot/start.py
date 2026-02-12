import asyncio
from pathlib import Path
from typing import Optional
import time

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, ExceptionTypeFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ErrorEvent, BotCommand, BufferedInputFile, InputMediaPhoto
from aiogram.client.session.aiohttp import AiohttpSession

import aiogram.types as t
t.MediaGroup = None

from middleware.downloader import download_tiktok_content
from middleware.process_buffer import process_buffer
from middleware.telegram.send_message import send_files_one_by_one

from logger.logger import logger
from config.config import STATIC_DIR
from config.config import IMAGE_EXTS_LOWER
from config.config import VIDEO_EXTS_LOWER
from config.config import ALBUM_TIMEOUT

log = logger(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / STATIC_DIR


# ---------------------- Роутеры ----------------------

root_router = Router(name="root_router")
main_router = Router(name="main_router")


# ---------------------- Фильтры и обработчики ----------------------
@root_router.message(CommandStart(deep_link=True))
@root_router.message(CommandStart())
async def cmd_start(message: Message, command: Optional[str] = None):
    """Обработчик /start"""
    text = (
        "Привет! 👋"
        "Я помогаю скачивать видео и фото из соцсетей без водяных знаков.\n\n"  
        "Просто пришли ссылку — и через пару секунд получишь чистый файл."
        "Поддерживаю пока что TikTok (остальные в планах).\n\n"
        "Кидай ссылку и проверяй! 🚀"
    )

    await message.answer(text, disable_web_page_preview=True)

@main_router.message(F.text)
async def handle_any_text(message: Message):
    text = message.text.strip()
    if not text:
        await message.answer("Пустое сообщение ¯\\_(ツ)_/¯")
        return

    if "tiktok.com" not in text and "vm.tiktok.com" not in text:
        await message.answer("Это не TikTok-ссылка. Пришли нормальную ссылку pls")
        return

    await message.answer("Скачиваю без водяного знака… ⏳")

    loop = asyncio.get_running_loop()

    try:
        start = time.perf_counter()
        success, buffer, ext, time_res = await loop.run_in_executor(
            None, download_tiktok_content, text, message.from_user.id, message.message_id
        )
        end = time.perf_counter()

        if not success or not buffer:
            await message.answer("Не получилось скачать 😔")
            return

        buffer.seek(0)

        album_data = await loop.run_in_executor(None, process_buffer, buffer, ext)

        if not album_data:
            await message.answer("Файлы не извлеклись 😕")
            return

        photos = [(d, n) for d, n in album_data if n.lower().endswith(IMAGE_EXTS_LOWER)]

        if len(photos) >= 2:
            media_group = [
                InputMediaPhoto(media=BufferedInputFile(d, n), caption="")
                for d, n in photos
            ]
            try:
                await message.answer_media_group(media=media_group, request_timeout=ALBUM_TIMEOUT)
                log.info("Альбом из %d фото отправлен успешно | down: %ss | %.2fs", len(photos), time_res, end - start)
                return
            except Exception as e: 
                log.warning("Альбом не прошёл (%s), отправляем по одному: %s", type(e).__name__, e)

        sent = await send_files_one_by_one(message, album_data)
        log.info("SEND: %d files | down: %ss | %.2fs", sent, time_res, end - start)

    except Exception as e:
        log.exception("ERROR in processing TikTok")
        await message.answer("Что-то сильно сломалось… Попробуй позже")


#@root_router.message(Command("cancel"))
#async def cmd_cancel(message: Message, state: FSMContext):
#    current_state = await state.get_state()
#    if current_state is None:
#        await message.answer("Нечего отменять")
#        return
#
#    await state.clear()
#    await message.answer("Действие отменено")

# ---------------------- Пример отправки медиа ----------------------

#@main_router.message(Command("photo"))
#async def send_example_photo(message: Message):
#    photo_path = STATIC_DIR / "example.jpg"
#
#    if not photo_path.exists():
#        await message.answer("Файл example.jpg не найден в папке static/")
#        return
#
#    await message.answer_photo(
#        photo=FSInputFile(photo_path),
#        caption="Пример локальной фотографии"
#    )

# ---------------------- Запуск бота ----------------------
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Скачать тикток по ссылке (видео/фото)"),
        BotCommand(command="test", description="Тест"),
    ]
    await bot.set_my_commands(commands)

class TeleBot:
    async def start(bot_token: str):
        session = AiohttpSession(timeout=120)
        bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                protect_content=False,
            ),
            session=session
        )
        storage = MemoryStorage() # Хранение состояний

        dp = Dispatcher(storage=storage)
        dp.include_routers(root_router, main_router)

        await set_commands(bot) # Инициализация комманд в боте

        log.info("BOT START")
        try:
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True,
            )
        finally:
            log.info("BOT STOP")
            await bot.session.close()

    async def stop(bot: Bot):
        if (bot != None):
            try:
                log.info("BOT STOP")
                await bot.session.close()
            except Exception as e:
                log.error("ERROR:", e)



# ---------------------- Обработка ошибок ----------------------

@root_router.errors(ExceptionTypeFilter(Exception))
async def error_handler(event: ErrorEvent):
    log.exception(
        "Произошла ошибка при обработке обновления",
        extra={"update": event.update.model_dump()}
    )

    if event.update.message:
        try:
            await event.update.message.answer(
                "Произошла внутренняя ошибка 😔\n"
                "Администрация уже в курсе."
            )
        except:
            pass