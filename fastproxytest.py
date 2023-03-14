from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType

class Settings:
    def __init__(self, CIToken: str, CICDToken: str, name: str, port: int, url: str, proxy: str=None):
        self.CIToken = CIToken
        self.CICDToken = CICDToken
        self.port = port
        self.name = name
        self.url = url
        self.proxy = proxy

class Browser(webdriver.Chrome):
    def __init__(self, settings: Settings, debug: bool=False, **kwargs):
        print(f"Browser.__init__()")
        p = Proxy()                                     
        p.proxy_type = ProxyType.MANUAL
        p.http_proxy = f"127.0.0.1:{settings.port}"
        c = DesiredCapabilities.CHROME.copy()
        # p.add_to_capabilities(c)                      # comment this line for speed when testing
        c['acceptInsecureCerts'] = True
        kwargs.update(desired_capabilities=c)
        print(f'webdriver.Chrome().__init__({kwargs})')
        super().__init__(**kwargs)

    def __del__(self):
        print(f"Browser.__del__()")
        return