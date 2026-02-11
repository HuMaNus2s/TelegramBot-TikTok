import io
import subprocess
import tempfile
import os
import zipfile
from typing import Optional, Tuple

from middleware.proxy import Proxy
from logger.logger import logger
from config.config import COUNT_RETRIES

log = logger(__name__)


def _run_yt_dlp(url: str, proxy_str: Optional[str], timeout: int = 35) -> Tuple[bool, Optional[bytes], str]:
    """Попытка скачать через yt-dlp в память"""
    cmd = [
        'yt-dlp',
        '-o', '-',                    # вывод в stdout
        '--no-part',
        '--quiet',
        '--no-warnings',
        '--merge-output-format', 'mp4',
        url
    ]
    if proxy_str:
        cmd.extend(['--proxy', proxy_str])

    log.debug("Запуск yt-dlp: %s", " ".join(cmd))

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False  # получаем байты
        )
        stdout, stderr = process.communicate(timeout=timeout)

        if process.returncode != 0:
            log.warning("yt-dlp завершился с ошибкой (код %d): %s", process.returncode, stderr.decode(errors='replace').strip())
            return False, None, ""

        size_mb = len(stdout) / 1_048_576
        if len(stdout) < 50_000:
            log.warning("yt-dlp вернул слишком маленький файл: %.1f KB", len(stdout) / 1024)
            return False, None, ""

        log.info("yt-dlp успех: %.2f MB", size_mb)
        return True, stdout, 'mp4'

    except subprocess.TimeoutExpired:
        log.error("yt-dlp превышен таймаут (%d сек)", timeout)
        process.kill()
        return False, None, ""
    except Exception as e:
        log.error("yt-dlp исключение: %s", str(e), exc_info=True)
        return False, None, ""


def _run_gallery_dl(url: str, proxy_str: Optional[str], timeout: int = 40) -> Tuple[bool, Optional[io.BytesIO], Optional[str]]:
    """Попытка скачать через gallery-dl во временную папку"""
    with tempfile.TemporaryDirectory(prefix="tg_tiktok_dl_") as tmp_dir:
        cmd = [
            'gallery-dl',
            '--directory', tmp_dir,
            '--quiet',
            url
        ]
        if proxy_str:
            cmd.extend(['--proxy', proxy_str])

        log.debug("Запуск gallery-dl: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )

            if result.returncode != 0:
                log.warning("gallery-dl завершился с ошибкой (код %d)\nstderr: %s",
                            result.returncode, result.stderr.strip())
                return False, None, None

            # Собираем все файлы
            files = []
            for root, _, filenames in os.walk(tmp_dir):
                for fname in filenames:
                    path = os.path.join(root, fname)
                    try:
                        with open(path, 'rb') as f:
                            data = f.read()
                        rel_path = os.path.relpath(path, tmp_dir)
                        files.append((rel_path, data))
                    except Exception as e:
                        log.warning("Не удалось прочитать файл %s: %s", path, e)

            if not files:
                log.warning("gallery-dl не скачал ни одного файла")
                return False, None, None

            if len(files) == 1:
                rel_path, data = files[0]
                ext = rel_path.rsplit('.', 1)[-1].lower() if '.' in rel_path else 'jpg'
                mime = f'image/{ext}' if ext in {'jpg', 'jpeg', 'png', 'webp', 'gif'} else 'video/mp4'
                buffer = io.BytesIO(data)
                log.info("gallery-dl успех: 1 файл (%s) ~%.2f MB", ext.upper(), len(data) / 1_048_576)
                return True, buffer, mime

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for fname, data in files:
                    zf.writestr(fname, data)

            zip_buffer.seek(0)
            zip_size = len(zip_buffer.getvalue())
            log.info("gallery-dl успех: zip из %d файлов ~%.2f MB", len(files), zip_size / 1_048_576)
            return True, zip_buffer, 'application/zip'

        except subprocess.TimeoutExpired:
            log.error("gallery-dl превышен таймаут (%d сек)", timeout)
            return False, None, None
        except Exception as e:
            log.error("gallery-dl исключение: %s", str(e), exc_info=True)
            return False, None, None


def download_tiktok_content(
    url: str,
    user_id: int = None,
    message_id: int = None,
    retries: int = COUNT_RETRIES
) -> Tuple[bool, Optional[io.BytesIO], Optional[str]]:
    """
    Возвращает: (успех, буфер или None, mime-тип или None)
    """
    for attempt in range(1, retries + 1):
        proxy = Proxy().get_proxy()
        proxy_str = f"socks5://{proxy}" if proxy else None

        log.info(
            "Попытка %d/%d | TikTok: %s | proxy=%s | msg=%s | uid=%s",
            attempt, retries, url, proxy_str, message_id, user_id
        )

        success, data, mime = _run_yt_dlp(url, proxy_str)
        if success:
            return True, io.BytesIO(data), mime

        success, buffer, mime = _run_gallery_dl(url, proxy_str)
        if success:
            return True, buffer, mime

        log.warning("Попытка %d не удалась | msg=%s | uid=%s",
                     attempt, message_id, user_id)

    log.error("Все попытки (%d) скачивания TikTok провалились: %s | msg=%s | uid=%s",
               retries, url, message_id, user_id)
    return False, None, None