import subprocess
import requests

from logger.logger import logger
from config.config import BLACKLIST_COUNTRY
from config.config import TIKTOK_DOMAIN

from middleware.proxy.parsers.proxymania import ProxyMania

log = logger(__name__)

class Proxy:
    def __init__(self, 
                 ip: str = None, port: int = None, 
                 country: str = None, ping: int = None, 
                 _st_accept: str = "text/html", 
                 _st_user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15"):
        self.ip = ip
        self.port = port
        self.country = country
        self.ping = ping

        self._st_accept = _st_accept
        self._st_useragent = _st_user_agent
        self.headers = {
           "Accept": self._st_accept,
           "User-Agent": self._st_useragent
        }

    def get(self): return self.ip, self.port, self.country, self.ping, self.headers

    @property
    def get_ip(self) -> str: return self.ip

    @property
    def get_port(self) -> int: return self.port

    @property
    def get_country(self) -> str: return self.country

    @property
    def get_ping(self) -> int: return self.ping

    @property
    def get_headers(self) -> str: return self.headers
    @property
    def get_proxy(self): return f"{self.ip}:{self.port}"

    def ping(self, url: str | None = None) -> bool:
        target = url if url else self.url
        
        try:
            res = requests.head(target, headers=self.Proxy().get_headers, timeout=5)
            return res.status_code == 200
        except (requests.RequestException, TimeoutError):
            return False

    # If required using server API
    def toJSON(self): return { 
        "ip": self.ip, 
        "port": self.port, 
        "country": self.country, 
        "last_ping": self.ping
    }

class ProxySOCKS5(Proxy):
    def __init__(self):
        pass
    
    def get_proxies(self) -> Proxy:
        proxies = []

        if ProxyMania.ping():
            for proxy, country, speed in ProxyMania.get:
                if country in BLACKLIST_COUNTRY:
                    continue
                try:    
                    proxy_ip, proxy_port = proxy.split(":")
                    proxies.append(Proxy(proxy_ip, proxy_port, country, speed[:-2]))
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
                log.error(f"CHECK {proxy}: {e}")

        if good_proxies:
            return good_proxies[0].get_proxy()
        return None

    
def test() :
    ProxyMania().ping()

