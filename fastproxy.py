import subprocess
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType

class Settings:
    """
    Settings class for instantiating the FAST Proxy Server.

    https://www.microfocus.com/documentation/fortify-ScanCentral-DAST/2220/SC_DAST_Help_22.2.0/index.htm#DynConfig/DynConf_FAST-W.htm?Highlight=fast

    Properties will map to the following command line (-switches) :

    .port (-p)    - Listening port.   
        Example:  -p 8085

    .name (-n)    - DAST Scan Name.   
        Example:  -n <fast_scan_name>
    
    .url (-u)     - DAST Url.
        Example:  -u http://<host|ip>:<port>/api/
    
    .proxy (-ps)  - External proxy server for traffic capture.   
        Example:  -ps <host|ip>:<port>
    
    .CICDToken    - Guid scan settings DAST token.
    
    .CIToken      - Base64 Authentication DAST token.
    """
    def __init__(self, CIToken: str, CICDToken: str, port: int, name: str, url: str, proxy: str=None):
        self.CIToken = CIToken
        self.CICDToken = CICDToken
        self.port = port
        self.name = name
        self.url = url
        self.proxy = proxy

class Browser(webdriver.Chrome):                        # returns Selenium webdriver object
    def __init__(self, settings: Settings, debug: bool=False):
        self.debug = debug
        if self.debug: print(f"Browser.__init__()")
        self.settings = settings

        self.InternetSettingsRegKey = "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        self.InternetSettings = self.__readRegistry()
        self.__writeRegistry(settings.port)

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
        self.__revertRegistry(self.InternetSettings)

    def __startFast(self):
        s = self.settings
        if self.debug: print(f"Browser.__startFast({s.port})")
        c = f"fast.exe -CIToken {s.CIToken} -CICDToken {s.CICDToken} -u \"{s.url}\" -p {s.port} -n \"{s.name}\""
        if s.proxy is not None: c+=f" -ps \"{s.proxy}\""
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

    def __readRegistry(self):
        k = self.InternetSettingsRegKey
        o = []
        for v in ("AutoConfigURL","ProxyEnable","ProxyServer","ProxyOverride"):
            c = f"reg query \"{k}\" /v \"{v}\""
            r = subprocess.run(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="UTF-8")
            # splitting returns this: ['HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet', 'Settings', 'ProxyEnable', 'REG_DWORD', '0x0']
            # use ternary operator to create either an ADD or DELETE reg statement -- add slices off first two items.
            a = ['add',k]+r.stdout.split()[2:] if (r.returncode == 0) else ['delete',k,v]
            if len(a)==4 : a.append("")     # check for empty string in value (trim() would have excised it)
            o.append(a)
        if self.debug: print(f"Read Internet Settings: {o}")
        return o

    def __writeRegistry(self, port):
        k = self.InternetSettingsRegKey
        v = [
                ["add",k,"AutoConfigURL","REG_SZ",""],
                ["add",k,"ProxyEnable","REG_DWORD","0x1"],
                ["add",k,"ProxyServer","REG_SZ",f"127.0.0.1:{port}"],
                ["delete",k,"ProxyOverride"]
            ]
        return self.__revertRegistry(v)
    

    def __revertRegistry(self, keys):
        if self.debug: print(f"Set Internet Settings: {keys}")
        for v in keys:
            if (len(v)>3) : 
                c = f"reg {v[0]} \"{v[1]}\" /v \"{v[2]}\" /t \"{v[3]}\" /d \"{v[4]}\" /f"
            else : 
                c = f"reg {v[0]} \"{v[1]}\" /v \"{v[2]}\" /f"
            if self.debug: print(c)
            r = subprocess.run(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="UTF-8")
        return keys
    