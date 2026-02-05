import asyncio
import logging
from pathlib import Path
from typing import Optional
import io

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, ErrorEvent, FSInputFile, BotCommand

from middleware.download import download_tiktok_content

from logger.logger import log
from config.config import STATIC_DIR


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
    user = message.from_user
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

    if "tiktok.com" in text or "vm.tiktok.com" in text:
        await message.answer("Сейчас скачаю тикток без водяного знака… ⏳")
        success, buffer, ext = download_tiktok_content("https://tiktok.com/...")
        if success and buffer:
            data = buffer.read()
            message.answer_document(document=io.BytesIO(data), filename=f"tiktok-file.{ext}")
    else:
        await message.answer(
            "Похоже, это не ссылка на TikTok.\n\n"
            "Пришли пожалуйста ссылку вида:\n"
            "https://www.tiktok.com/@username/video/123456789\n"
            "или короткую vm.tiktok.com/xxxxx"
        )



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
        BotCommand(command="start", description="Перезапустить бота"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="download", description="Скачать тикток по ссылке (видео/фото)"),
        BotCommand(command="cancel", description="Отменить действие"),
    ]
    await bot.set_my_commands(commands)

class TeleBot:
    async def start(bot_token: str):
        bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                protect_content=False,
            )
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