import zipfile
import io
from .is_zip import is_zip

from logger.logger import logger

log = logger(__name__)

async def process_buffer(buffer, ext: str = 'mp4') -> list[tuple[bytes, str]]:
    """
    buffer: bytes | io.BytesIO
    return: [(bytes, filename), ...]
    """
    if isinstance(buffer, io.BytesIO):
        buffer_bytes = buffer.getvalue()
    elif isinstance(buffer, bytes):
        buffer_bytes = buffer
    else:
        raise TypeError(f"Expected bytes or BytesIO, received {type(buffer)}")

    result = []

    if await is_zip(buffer_bytes):
        try:
            with zipfile.ZipFile(io.BytesIO(buffer_bytes)) as z:
                for name in z.namelist():
                    name_lower = name.lower()
                    if name_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        data = z.read(name)
                        result.append((data, name.strip('/\\')))
                    elif name_lower.endswith(('.mp4', '.mov', '.avi')):
                        data = z.read(name)
                        result.append((data, name.strip('/\\')))

        except zipfile.BadZipFile:
            log.warning("Damaged ZIP -> fallback on video")
            result.append((buffer_bytes, f"fallback_video.{ext}"))
        except Exception as e:
            log.error(f"ZIP ERROR: {e}")
            result.append((buffer_bytes, f"error_fallback.{ext}"))

    else:
        video_name = f"video.{ext}"
        result.append((buffer_bytes, video_name))

    return result