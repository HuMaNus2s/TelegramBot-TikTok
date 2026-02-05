import io
import subprocess
import tempfile
import os
import zipfile
from typing import Optional, Tuple
from config.config import PROXY
from logger.logger import log


def download_tiktok_content(url: str, user_id: int = None, message_id: int = None) -> Tuple[bool, Optional[io.BytesIO], Optional[str]]:
    proxy_str = f"socks5://{PROXY}" if PROXY else None
    log.info("Download TikTok: %s | proxy=%s | message_id=%s | uid=%s", url, proxy_str, message_id, user_id)

    buffer = io.BytesIO()

    try:
        cmd = ['yt-dlp', '-o', '-', '--no-part', '--quiet', '--no-warnings', '--merge-output-format', 'mp4', url]
        if proxy_str:
            cmd += ['--proxy', proxy_str]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        video_bytes, stderr = process.communicate(timeout=180)

        if process.returncode == 0 and len(video_bytes) > 100_000:
            buffer = io.BytesIO(video_bytes)
            log.info("yt-dlp DONE: %.1f MB", len(video_bytes) / 1_048_576)
            return True, buffer, 'mp4'
        else:
            pass
    except subprocess.TimeoutExpired:
        log.error("yt-dlp timeout")
    except Exception as e:
        log.warning("yt-dlp ERROR: %s", str(e))
    with tempfile.TemporaryDirectory() as tmp_dir:
        cmd = [
            'gallery-dl',
            '--proxy', proxy_str if proxy_str else '',
            '--directory', tmp_dir,
            '--quiet',
            url
        ]
        if not proxy_str:
            cmd.remove('--proxy')
            cmd.remove('')

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if result.returncode == 0:
                files = []
                for root, _, filenames in os.walk(tmp_dir):
                    for fname in filenames:
                        path = os.path.join(root, fname)
                        with open(path, 'rb') as f:
                            data = f.read()
                        rel_path = os.path.relpath(path, tmp_dir)
                        files.append((rel_path, data))

                if len(files) == 1:
                    _, data = files[0]
                    buffer = io.BytesIO(data)
                    ext = files[0][0].rsplit('.', 1)[-1].lower() if '.' in files[0][0] else 'jpg'
                    mime = f'image/{ext}' if ext in {'jpg', 'jpeg', 'png', 'webp'} else 'application/octet-stream'
                    log.info("gallery-dl DONE: 1 file ~%.1f MB", len(data) / 1_048_576)
                    return True, buffer, mime
                elif len(files) > 1:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for fname, data in files:
                            zf.writestr(fname, data)
                    zip_buffer.seek(0)
                    log.info("gallery-dl DONE: zip %d files ~%.1f MB", len(files), zip_buffer.tell() / 1_048_576)
                    return True, zip_buffer, 'application/zip'
        except subprocess.TimeoutExpired:
            log.error("gallery-dl timeout")
        except Exception as e:
            log.error("gallery-dl ERROR: %s", str(e))

    log.error("Complete download failure")
    return False, None, None
