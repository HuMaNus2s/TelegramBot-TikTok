from middleware.download import download_tiktok_content
from logger.logger import log

if __name__ == "__main__":
    url_photo = "https://vt.tiktok.com/ZSanrkr87/"
    url_video = "https://vt.tiktok.com/ZSan8UygT/"
    
    log.info(download_tiktok_content(url_video))
    log.info(download_tiktok_content(url_photo))