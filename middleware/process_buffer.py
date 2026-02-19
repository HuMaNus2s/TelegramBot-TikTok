import zipfile
import io
import os
from typing import List, Tuple

from .is_zip import is_zip

from logger.logger import logger
import traceback

from config.config import IMAGE_EXTS_LOWER
from config.config import VIDEO_EXTS_LOWER

log = logger(__name__)                            

def process_buffer(buffer, video_ext: str = 'mp4') -> List[Tuple[bytes, str]]:
    """
    Обрабатывает буфер из RAM:
      - Если ZIP → извлекает фото (.jpg/.jpeg/.png/.webp/.gif) и видео (.mp4/.mov)
      - Иначе → считает одиночным видео (.mp4 по умолчанию)

    Args:
        buffer: bytes | io.BytesIO | file-like (с .read())
        video_ext: расширение для fallback-видео (по умолчанию 'mp4')

    Returns:
        List[(bytes, filename), ...] — список пар (данные, имя_файла)
    """
    if isinstance(buffer, bytes):
        buffer_bytes = buffer
    elif isinstance(buffer, io.BytesIO):
        buffer_bytes = buffer.getvalue()
    elif hasattr(buffer, 'read'):
        buffer_bytes = buffer.read()
    else:
        raise TypeError(f"Ожидался bytes / BytesIO / file-like, получен {type(buffer)}")

    result: List[Tuple[bytes, str]] = []

    if is_zip(buffer_bytes):
        try:
            with zipfile.ZipFile(io.BytesIO(buffer_bytes)) as z:
                extracted_count = 0
                for name in z.namelist():
                    if name.endswith('/'):
                        continue
                    base_name = os.path.basename(name)
                    if not base_name:
                        continue

                    lower_name = base_name.lower()
                    data = None

                    if lower_name.endswith(IMAGE_EXTS_LOWER):
                        data = z.read(name)
                        extracted_count += 1
                    elif lower_name.endswith(VIDEO_EXTS_LOWER):
                        data = z.read(name)
                        extracted_count += 1

                    if data:
                        result.append((data, base_name))

                log.info(f"Из ZIP извлечено {extracted_count} файлов (фото/видео)")

        except zipfile.BadZipFile:
            log.warning("Повреждённый ZIP → fallback на видео")
            result.append((buffer_bytes, f"damaged_zip_fallback.{video_ext}"))
        except Exception as e:
            log.error(f"Ошибка при распаковке ZIP: {e}\n{traceback.format_exc()}")
            result.append((buffer_bytes, f"zip_error_fallback.{video_ext}"))

    else:
        result.append((buffer_bytes, f"video.{video_ext}"))

    return result