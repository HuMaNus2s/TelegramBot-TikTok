import io
import subprocess
import tempfile
import os
import zipfile
from typing import Optional, Tuple

from logger.logger import logger
from config.config import COUNT_RETRIES
from config.config import IMAGE_EXTS_LOWER

log = logger(__name__)

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

        log.debug("START gallery-dl: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )

            if result.returncode != 0:
                log.warning("gallery-dl ERROR (code %d)\nstderr: %s",
                            result.returncode, result.stderr.strip())
                return False, None, None

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
                        log.warning("Couldn't read the file %s: %s", path, e)

            if not files:
                log.warning("gallery-dl NOT DOWNLOAD")
                return False, None, None

            if len(files) == 1:
                rel_path, data = files[0]
                ext = rel_path.rsplit('.', 1)[-1].lower() if '.' in rel_path else 'jpg'
                mime = f'image/{ext}' if ext in IMAGE_EXTS_LOWER else 'video/mp4'
                buffer = io.BytesIO(data)
                log.info("gallery-dl DONE: 1 file (%s) ~%.2f MB", ext.upper(), len(data) / 1_048_576)
                return True, buffer, mime

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for fname, data in files:
                    zf.writestr(fname, data)

            zip_buffer.seek(0)
            zip_size = len(zip_buffer.getvalue())
            log.info("gallery-dl DONE: ZIP from %d files ~%.2f MB", len(files), zip_size / 1_048_576)
            return True, zip_buffer, 'application/zip'

        except subprocess.TimeoutExpired:
            log.error("gallery-dl TIMEOUT (%ds)", timeout)
            return False, None, None
        except Exception as e:
            log.error("gallery-dl ERROR: %s", str(e), exc_info=True)
            return False, None, None