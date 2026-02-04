import yt_dlp
import subprocess
import os
import sys
from logger.logger import log

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from config.config import PROXY

def download_tiktok_content(link, output_folder="downloads"):
    os.makedirs(output_folder, exist_ok=True)
    
    proxy_str = f"socks5://{PROXY}" if PROXY else None

    ydl_opts = {
        'outtmpl': f'{output_folder}/%(uploader)s_%(title)s.%(ext)s',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'proxy': proxy_str,
        'noplaylist': True,
        'quiet': False,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'referer': 'https://www.tiktok.com/',
        'cookiesfrombrowser': ('chrome',),
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            if 'video' in info.get('formats', [{}])[0].get('vcodec', '') or info.get('ext') == 'mp4':
                log.info("Видео обнаружено → yt-dlp")
                ydl.download([link])
                return "Видео (или звук из фото) скачано yt-dlp"
    except Exception as e:
        log.info(f"yt-dlp: {e} → переходим к gallery-dl")
    try:
        cmd = [
            sys.executable,
            "-m", "gallery_dl",
            "--proxy", proxy_str,
            "--directory", output_folder,
            link
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        log.info("gallery-dl stdout:\n", result.stdout)
        log.info("gallery-dl stderr:\n", result.stderr)
        if result.returncode == 0:
            return "Фото/слайдшоу скачано gallery-dl"
        else:
            return f"gallery-dl ошибка (код {result.returncode}): {result.stderr}"
    except FileNotFoundError:
        return "gallery-dl не найден — pip install gallery-dl"
    except Exception as e:
        return f"Ошибка gallery-dl: {e}"