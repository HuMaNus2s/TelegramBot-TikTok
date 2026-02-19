import requests
from bs4 import BeautifulSoup
import subprocess

from logger.logger import logger
from config.config import BLACKLIST_COUNTRY
from config.config import TIKTOK_DOMAIN

log = logger(__name__)

class ProxySOCKS5:
    def __init__(self, ip: str, port: int, country: str, ping: int,):
        self.ip = ip
        self.port = port
        self.country = country
        self.ping = ping

    def get(self): return self.ip, self.port, self.country, self.ping
    def get_ip(self) -> str: return self.ip
    def get_port(self) -> int: return self.port
    def get_country(self) -> str: return self.country
    def get_ping(self) -> int: return self.ping
    def get_proxy(self): return f"{self.ip}:{self.port}"

    # If required using server API
    def toJSON(self): return { 
        "ip": self.ip, 
        "port": self.port, 
        "country": self.country, 
        "last_ping": self.ping
    }

class Proxy(ProxySOCKS5):
    def __init__(self):
        pass
    
    def get_proxies(self) -> ProxySOCKS5:
        st_accept = "text/html"
        st_useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15"
        headers = {
           "Accept": st_accept,
           "User-Agent": st_useragent
        }

        proxies = []
        req = requests.get("https://proxymania.su/free-proxy?type=SOCKS5&country=&speed=100", headers)
        
        src = req.text
        soup = BeautifulSoup(src, 'lxml')

        table1 = soup.find('tbody', id='resultTable')

        fast_cells    = table1.find_all('td', class_='speed-fast')
        proxy_cells   = table1.find_all('td', class_='proxy-cell')
        country_cells = table1.find_all('td', class_='country-cell')

        for proxy_td, country_td, speed_td in zip(proxy_cells, country_cells, fast_cells):
            country = country_td.get_text(strip=True)
            if country in BLACKLIST_COUNTRY:
                continue
            
            proxy = proxy_td.get_text(strip=True)
            speed = speed_td.get_text(strip=True)

            try:    
                proxy_ip, proxy_port = proxy.split(":")
                proxies.append(ProxySOCKS5(proxy_ip, proxy_port, country, speed[:-2]))
            except ValueError as e:
                log.error(e)
        return proxies
    
    def get_proxy(self):
        proxies = self.get_proxies()
        good_proxies = []
        for p in proxies:
            proxy = p.get_proxy()
            cmd = [
                'ping',
                '--proxy', proxy,
                TIKTOK_DOMAIN
                ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                if result.returncode == 1:
                    good_proxies.append(p)
            except Exception as e:
                log.error(f"Ошибка проверки {proxy}: {e}")

        if good_proxies:
            return good_proxies[0].get_proxy()
        return None





