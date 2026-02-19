import subprocess
from typing import Optional, Tuple

from logger.logger import logger
from config.config import COUNT_RETRIES

log = logger(__name__)

def _run_yt_dlp(url: str, proxy_str: Optional[str], timeout: int = 35) -> Tuple[bool, Optional[bytes], str]:
    """Попытка скачать через yt-dlp в память"""
    cmd = [
        'yt-dlp',
        '-o', '-',
        '--no-part',
        '--quiet',
        '--no-warnings',
        '--merge-output-format', 'mp4',
        url
    ]
    if proxy_str:
        cmd.extend(['--proxy', proxy_str])

    log.debug("START yt-dlp: %s", " ".join(cmd))

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False
        )
        stdout, stderr = process.communicate(timeout=timeout)

        if process.returncode == 1:
            log.warning("yt-dlp didn't work, so we're using  gallery-dl")
            return False, None, ""

        if process.returncode != 0:
            log.warning("yt-dlp ERROR (code %d): %s", process.returncode, stderr.decode(errors='replace').strip())
            return False, None, ""

        size_mb = len(stdout) / 1_048_576
        if len(stdout) < 50_000:
            log.warning("yt-dlp returned file is too small: %.1f KB", len(stdout) / 1024)
            return False, None, ""

        log.info("yt-dlp DONE: %.2f MB", size_mb)
        return True, stdout, 'mp4'

    except subprocess.TimeoutExpired:
        log.error("yt-dlp TIMEOUT (%ds)", timeout)
        process.kill()
        return False, None, ""
    except Exception as e:
        log.error("yt-dlp ERROR: %s", str(e), exc_info=True)
        return False, None, ""