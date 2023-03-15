import subprocess
import time
import os
from threading import Thread, Event, Lock
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
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

    .openssl      - Use OpenSSL ciphers for DAST API.            
        Example:  -openssl
    """
    def __init__(self, CIToken: str, CICDToken: str, name: str = None, port: int=8085, url: str="http://localhost:64814/api", proxy: str=None, openssl: bool=False):
        self.CIToken = CIToken
        self.CICDToken = CICDToken
        self.port = port
        self.name = name if (name!=None) else f"fast_scan_on_port_{port}"
        self.url = url
        self.proxy = proxy
        self.openssl = openssl

DEFAULT_FAST_IDLE_TIMEOUT = 10
DEFAULT_FAST_TOTAL_TIMEOUT = 60
INTERNET_SETTINGS_REG_KEY = "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings"


class Browser(webdriver.Chrome):                # returns Selenium webdriver object

    def __init__(self, settings: Settings, debug: bool=False, manualseleniumproxy: bool=False, **kwargs):
        def info(message, end=None):            # encapsulating print messages (easy switch to better logging)
            if debug: print(message, end=end)
        self.__info = info
        self.__settings = settings
        info(f"Browser.__init__()")

        # Read RegKeys
        info(f"Reading current Internet Settings")
        def readRegistry():
            k = INTERNET_SETTINGS_REG_KEY
            o = []
            for v in ("AutoConfigURL","ProxyEnable","ProxyServer","ProxyOverride"):
                c = f"reg query \"{k}\" /v \"{v}\""
                r = subprocess.run(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="ignore")
                # splitting returns this: ['HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet', 'Settings', 'ProxyEnable', 'REG_DWORD', '0x0']
                # use ternary operator to create either an ADD or DELETE reg statement -- add slices off first two items.
                a = ['add',k]+r.stdout.split()[2:] if (r.returncode == 0) else ['delete',k,v]
                if len(a)==4 : a.append("")     # check for empty string in value (trim() would have excised it)
                o.append(a)
            return o
        self.__previousInternetSettings = readRegistry()

        # Write RegKeys
        def writeRegistry(keys):
            # info(f"Set Internet Settings: {keys}")
            for v in keys:
                # Examples:
                #   reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v "ProxyServer" /t "REG_SZ" /d "127.0.0.1:8159" /f
                #   reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v "ProxyOverride" /f
                if (len(v)>3) : 
                    c = f"reg {v[0]} \"{v[1]}\" /v \"{v[2]}\" /t \"{v[3]}\" /d \"{v[4]}\" /f"
                else : 
                    c = f"reg {v[0]} \"{v[1]}\" /v \"{v[2]}\" /f"
                # info(c)
                r = subprocess.run(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="ignore")
            return keys
        self.__writeRegistry = writeRegistry
        info("Setting temporary Internet Settings")
        def setFastRegistry():                  # temp FAST settings
            k = INTERNET_SETTINGS_REG_KEY
            v = [
                    ["add",k,"AutoConfigURL","REG_SZ",""],
                    ["add",k,"ProxyEnable","REG_DWORD","0x1"],
                    ["add",k,"ProxyServer","REG_SZ",f"127.0.0.1:{settings.port}"],
                    ["delete",k,"ProxyOverride"]
                ]
            return writeRegistry(v)
        self.__fastInternetSettings = setFastRegistry()
        
        # FAST Proxy Start
        info(f"Start FAST proxy ({settings.port})")
        def fast():
            s = settings
            c = f"fast.exe -CIToken {s.CIToken} -CICDToken {s.CICDToken} -u \"{s.url}\" -p {s.port} -n \"{s.name}\""
            if s.proxy is not None: c+=f" -ps \"{s.proxy}\""
            if s.openssl: c+=f" -openssl"
            return c
        c = fast()              
        info(f"cmd: {c}")             
        p = subprocess.Popen(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.__process = p
        info(f"pid: {p.pid}")

        # Output storage/concurrency
        l = Lock()          # lock used for multi-threaded sharing
        q = []              
        self.__queue = q    # temporary holder for stdout reads
        s = []
        self.__save = s     # this will act as a full archive - periodic copy q into save.

        # stdout reader thread
        # daemonic so that it can survive through garbage collection
        #   be cafeful using self.properties so not to interfere w/collection
        o = p.stdout
        self.__read = None
        def readerthread():
            def read():         
                d = os.read(o.fileno(), 65536)
                if len(d) > 0 : 
                    l.acquire()     # Lock against other threads
                    d = d.decode("utf-8")
                    info(d, end="")
                    q.append(d)
                    l.release()
                if d == b"":
                    o.close()
                return d
            def reader():
                while read()!=b"":
                    time.sleep(.5)
            self.__read = read        # saving this def for future use @end
            r = Thread(target=reader, daemon=True)
            r.start()
            return r
        self.__readerthread = readerthread()

        # Checker for process still running - returns None(still alive) or returncode
        def poll():
            x = p.poll()
            if x != None:
                try: self.__readerthread.join(timeout=10) 
                except: pass
            return x

        # Main background 
        # Idle/Total timeouts control timed thread shutdown (allowing garbage collection)
        # Idle (length since last stdout data) Total (beginning if FAST startup) seconds
        self.fastidletimeout = DEFAULT_FAST_IDLE_TIMEOUT
        self.fasttotaltimeout = DEFAULT_FAST_TOTAL_TIMEOUT
        z = Event()         # signals FAST is listening - handover to Selenium execution code
        y = Event()         # signals shutdown should occur
        self.__shutdown = y
        self.__fastshutdown = None  # results of "fast.exe -s" run()
        def background():
            def diff(v,t):  # check timeout exceeded
                return False if (t==None) else (time.perf_counter()-v > t)
            b = time.perf_counter() # birth time
            c = b                   # time of last data
            while True:
                if len(q):                      # data in queue
                    c = time.perf_counter()     # update data-timestamp
                    l.acquire()                 # lock for clearing
                    for d in q:
                        if "Listening" in d: z.set()    # flag event when monitor sees "Listening"
                        s.append(d)             # copy to archive
                    q.clear()                   # clear data
                    l.release()
                if diff(b, self.fasttotaltimeout) : info("Total timeout"); break    # total runtime timeout
                if diff(c, self.fastidletimeout) : info("Idle timeout"); break      # idle timeout
                if y.is_set() : info("Shutdown requested"); break                   # shutdown requested
                if poll() != None : break
                time.sleep(.5)
        b = Thread(target=background, daemon=False)
        b.start()
        while z.is_set()==False:    # holds code until event-flagged (FAST is ready to capture)
            time.sleep(1)
        info("FAST is listening/ready for Selenium execution.")
        
        # Proxy Settings
        info("Setting proxy settings for [Browser] object")  
        def capabilities():
            c = DesiredCapabilities.CHROME.copy()
            if manualseleniumproxy: # set True for manual proxy, otherwise use selenium default
                p = Proxy()                                     
                p.proxy_type = ProxyType.MANUAL
                p.http_proxy = f"127.0.0.1:{settings.port}" # proxy is localhost:port matching the FAST proxy port
                p.add_to_capabilities(c)
            c['acceptInsecureCerts'] = True
            return c
    
        # Update keyword args/give access to parent class members (webdriver.Chrome)
        kwargs.update(desired_capabilities=capabilities())
        print(f'webdriver.Chrome().__init__({kwargs})')
        super().__init__(**kwargs)

    def stopfast(self):
        def info(): pass
        info = self.__info
        # stop FAST proxy
        self.__shutdown.set()
        p = self.__settings.port
        info(f"Stop FAST ({p})")
        c = f"fast.exe -p {p} -s"
        info(f"cmd: {c}") 
        r = subprocess.run(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="ignore")
        info(f"FAST stop returned: {r.returncode}")
        self.__fastshutdown = r

    def __del__(self):        
        def info(): pass
        info = self.__info
        info(f"Browser.__del__()")

        # stop fast on garbage collection
        if self.__fastshutdown is None: self.stopfast()

        # loop until the process completes
        while True:
            try:
                self.__read()
            except: pass
            if self.__process.poll()!=None: break
            time.sleep(.5)
        
        # copy remaining data to archive list
        q=self.__queue
        s=self.__save
        if len(q):
            for d in q:
                s.append(d)     
            q.clear()
            
        # revert registry
        self.__writeRegistry(self.__previousInternetSettings)

        # print stdout archive list w/tabs (stdout history)
        s.insert(0, "Completed:\n")
        info("".join(s), end="")
