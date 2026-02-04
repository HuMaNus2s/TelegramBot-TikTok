import yt_dlp
import subprocess
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from config.config import PROXY

def download_tiktok_content(link, output_folder="downloads"):
    os.makedirs(output_folder, exist_ok=True)
    
    proxy_str = f"socks5://{PROXY}" if PROXY else None
    
    # Сначала пробуем yt-dlp (лучше всего для видео + иногда звук из фото)
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
        'cookiesfrombrowser': ('chrome',),  # если есть куки в браузере — добавит, помогает с 403
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            if 'video' in info.get('formats', [{}])[0].get('vcodec', '') or info.get('ext') == 'mp4':
                print("Видео обнаружено → yt-dlp")
                ydl.download([link])
                return "Видео (или звук из фото) скачано yt-dlp"
    except Exception as e:
        print(f"yt-dlp: {e} → переходим к gallery-dl")
    
    # gallery-dl для фото/слайдшоу (запускаем как модуль — работает в venv)
    try:
        cmd = [
            sys.executable,
            "-m", "gallery_dl",
            "--proxy", proxy_str,
            "--directory", output_folder,
            link
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("gallery-dl stdout:\n", result.stdout)
        print("gallery-dl stderr:\n", result.stderr)
        if result.returncode == 0:
            return "Фото/слайдшоу скачано gallery-dl"
        else:
            return f"gallery-dl ошибка (код {result.returncode}): {result.stderr}"
    except FileNotFoundError:
        return "gallery-dl не найден — pip install gallery-dl"
    except Exception as e:
        return f"Ошибка gallery-dl: {e}"

# Тест
if __name__ == "__main__":
    url_photo = "https://vt.tiktok.com/ZSanrkr87/"
    url_video = "https://vt.tiktok.com/ZSan8UygT/"
    
    print(download_tiktok_content(url_video))
    print(download_tiktok_content(url_photo))