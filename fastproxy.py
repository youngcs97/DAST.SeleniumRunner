import subprocess
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType

class Settings:
    def __init__(self, CIToken: str, CICDToken: str, port: int, name: str, url: str):
        self.CIToken = CIToken
        self.CICDToken = CICDToken
        self.port = port
        self.name = name
        self.url = url

class Browser(webdriver.Chrome):                        # returns Selenium webdriver object
    def __init__(self, settings: Settings, debug: bool=True):
        self.debug = debug
        if self.debug: print(f"Browser.__init__()")
        self.settings = settings
        self.fast = self.__startFast()                  # starts the FAST proxy
        p = Proxy()                                     # sets the proxy
        p.proxy_type = ProxyType.MANUAL
        p.http_proxy = f"127.0.0.1:{settings.port}"     # proxy is localhost:port matching the FAST proxy port
        c = webdriver.DesiredCapabilities.CHROME
        p.add_to_capabilities(c)
        o = webdriver.ChromeOptions()
        o.add_argument('ignore-certificate-errors')
        if self.debug: print('webdriver.Chrome().__init__()')
        super(Browser, self).__init__(desired_capabilities=c,options=o)
        
    def __del__(self):
        if self.debug: print(f"Browser.__del__()")
        self.__stopFast()                               # stop the FAST proxy on destroy
        o = self.fast.stdout
        for i in range(50):                             # loop through 50 lines (or until a scanId is assigned) and then kill
            l = (o.readline()).decode("utf-8")
            if len(l) > 0:
                if self.debug: print(f"{l}", end="")
                if "Assigned scanId" in l:
                    break
        self.fast.kill()                                # I got lazy with the 50 lines or kill -- might have to be more elaborate, but works for small capture.

    def __startFast(self):
        s = self.settings
        if self.debug: print(f"Browser.__startFast({s.port})")
        c = f"fast.exe -CIToken {s.CIToken} -CICDToken {s.CICDToken} -u \"{s.url}\" -p {s.port} -n \"{s.name}\""
        if self.debug: print(f"{c}")
        #c = ("ping 127.0.0.1", "seq=0")
        p = subprocess.Popen(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        o = p.stdout
        for i in range(10):                             # loops for 10 line reads or until it encounters the word "Listening"
            l = (o.readline()).decode("utf-8")
            if len(l) > 0:
                if self.debug: print(f"{l}", end="")
                if "Listening" in l:
                    break                               # indicats proxy is ready & listening - releases so Selenium code may run.
        return p

    def __stopFast(self):
        p = self.settings.port
        if self.debug: print(f"Browser.__stopFast({p})")
        c = f"fast.exe -p {p} -s"
        if self.debug: print(f"{c}")
        p = subprocess.run(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return p



