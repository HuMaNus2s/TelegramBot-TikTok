import yt_dlp
import os

def download_tiktok_photos(url, output_folder="downloads"):
    os.makedirs(output_folder, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': f'{output_folder}/%(title)s_%(id)s.%(ext)s',
        'quiet': False,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            print("Скачано:", info.get('title', 'Без названия'))
            if 'entries' in info:
                for entry in info['entries']:
                    print("Файл:", entry.get('filepath'))
        except Exception as e:
            print("Ошибка:", e)

url = "https://vt.tiktok.com/ZSan8UygT/"
download_tiktok_photos(url)