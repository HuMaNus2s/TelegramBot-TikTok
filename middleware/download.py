import contextlib
import io
import zipfile
import yt_dlp
from typing import Optional, Tuple

from config.config import PROXY
from logger.logger import log


def download_tiktok_content(url: str) -> Tuple[bool, Optional[io.BytesIO], Optional[str]]:
    proxy = f"socks5://{PROXY}" if PROXY else None

    # ── yt-dlp для видео (остаётся как есть) ───────────────────────────
    ydl_opts = {
        'outtmpl': '-',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'proxy': proxy,
        'noplaylist': True,
        'quiet': True,
        'simulate': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'referer': 'https://www.tiktok.com/',
        'impersonate': 'chrome',
        'socket_timeout': 60,
        'retries': 10,
    }

    buffer = io.BytesIO()

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if info.get('duration') or any(f.get('acodec') != 'none' for f in info.get('formats', [])):
                with contextlib.redirect_stdout(buffer):
                    ydl.download([url])
                size = buffer.tell()
                if size > 100_000:
                    log.info("yt-dlp → видео скачано в память (%.1f MB)", size / 1_048_576)
                    buffer.seek(0)
                    return True, buffer, 'mp4'

    except Exception as e:
        log.warning("yt-dlp ошибка: %s", str(e))

    # ── gallery-dl-bytes для фото/слайдшоу ─────────────────────────────
    try:
        from gallery_dl_bytes import download_to_bytes

        result = download_to_bytes(url, proxy=proxy)

        if result:
            if len(result) == 1:
                filename, data = result[0]
                ext = filename.split('.')[-1].lower() or 'jpg'
                buffer = io.BytesIO(data)
                size = len(data)
                log.info("gallery-dl-bytes → одиночный файл в память (%.1f MB, %s)", size / 1_048_576, ext)
                return True, buffer, ext

            else:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for filename, data in result:
                        zf.writestr(filename, data)
                zip_buffer.seek(0)
                size = zip_buffer.tell()
                log.info("gallery-dl-bytes → %d файлов zipped в память (%.1f MB)", len(result), size / 1_048_576)
                return True, zip_buffer, 'zip'

    except ImportError:
        log.error("gallery-dl-bytes не установлен (pip install gallery-dl-bytes)")
    except Exception as e:
        log.error("gallery-dl-bytes ошибка: %s", str(e))

    log.error("Скачивание провалено: %s", url)
    return False, None, None