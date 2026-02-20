import requests
from bs4 import BeautifulSoup

from logger.logger import logger
log = logger(__name__)

class ProxyMania:
    def __init__(self, url: str = "https://proxymania.su/free-proxy?type=SOCKS5&country=&speed=100"):
        from ..proxy import Proxy
        self.Proxy = Proxy
        self.url = url

    @property
    def get(self):
        try:
            req = requests.get(self.url, self.Proxy().get_headers)
            src = req.text

            soup = BeautifulSoup(src, 'lxml')
            table1 = soup.find('tbody', id='resultTable')
            proxy   = table1.find_all('td', class_='proxy-cell').get_text(strip=True)
            country = table1.find_all('td', class_='country-cell').get_text(strip=True)
            speed    = table1.find_all('td', class_='speed-fast').get_text(strip=True)

            log.info("PROXY: %s | COUNTRY: %s | PING: %s", proxy, country, speed)
        except Exception as e:
            log.error("PROXY ERROR: %s", e)
            return zip(None, None, None)

        return zip(proxy, country, speed)

    def ping(self):
        return self.Proxy().ping()