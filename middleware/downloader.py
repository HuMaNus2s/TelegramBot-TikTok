import io
from typing import Optional, Tuple
import time

from middleware.proxy import Proxy
from logger.logger import logger
from .download.dl_gallery import _run_gallery_dl
from .download.yt_dlp import _run_yt_dlp

from config.config import COUNT_RETRIES

log = logger(__name__)

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
            "Attempt %d/%d | TikTok: %s | proxy=%s | msg=%s | uid=%s",
            attempt, retries, url, proxy_str, message_id, user_id
        )
        start = time.perf_counter()
        success, data, mime = _run_yt_dlp(url, proxy_str)
        end = time.perf_counter()
        if success:
            time_result = end - start
            return True, io.BytesIO(data), mime, time_result

        start = time.perf_counter()
        success, buffer, mime = _run_gallery_dl(url, proxy_str)
        end = time.perf_counter()
        if success:
            time_result = end - start
            return True, buffer, mime, time_result

        log.warning("Attempt %d failed | msg=%s | uid=%s",
                     attempt, message_id, user_id)

    log.error("All attempt (%d) download TikTok failed: %s | msg=%s | uid=%s",
               retries, url, message_id, user_id)
    return False, None, None, 0