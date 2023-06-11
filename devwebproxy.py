import subprocess
import time
import os
from threading import Thread, Event, Lock
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType

class Settings:
    def __init__(self, port: int=8156, file: str=None):
        self.port = port
        self.file = file if (file!=None) else f"ProxyRecorder.har"

DEFAULT_PROXY_IDLE_TIMEOUT = 10
DEFAULT_PROXY_TOTAL_TIMEOUT = 60


class Browser(webdriver.Chrome):                # returns Selenium webdriver object

    def __init__(self, settings: Settings, debug: bool=False, manualseleniumproxy: bool=False, **kwargs):
        def info(message, end=None):            # encapsulating print messages (easy switch to better logging)
            if debug: print(message, end=end)
        self.__info = info
        self.__settings = settings
        info(f"Browser.__init__()")

        # Proxy Start
        info(f"Start DEVWEB proxy ({settings.port})")
        def proxy():
            s = settings
            c = f"$DEVWEB_PATH/ProxyRecorder \"{s.file}\""
            return c
        c = proxy()              
        info(f"cmd: {c}")             
        p = subprocess.Popen(c, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
        # Idle (length since last stdout data) / Total (beginning of proxy startup) seconds
        self.proxyidletimeout = DEFAULT_PROXY_IDLE_TIMEOUT
        self.proxytotaltimeout = DEFAULT_PROXY_TOTAL_TIMEOUT
        z = Event()         # signals proxy is listening - handover to Selenium execution code
        y = Event()         # signals shutdown should occur
        self.__shutdown = y
        self.__proxyshutdown = None  
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
                        if "Proxy server listening at" in d: z.set()    # flag event when monitor sees "Listening"
                        s.append(d)             # copy to archive
                    q.clear()                   # clear data
                    l.release()
                if diff(b, self.proxytotaltimeout) : info("Total timeout"); break    # total runtime timeout
                if diff(c, self.proxyidletimeout) : info("Idle timeout"); break      # idle timeout
                if y.is_set() : info("Shutdown requested"); break                   # shutdown requested
                if poll() != None : break
                time.sleep(.5)
        b = Thread(target=background, daemon=False)
        b.start()
        while z.is_set()==False:    # holds code until event-flagged (proxy is ready to capture)
            time.sleep(1)
        info("DEVWEB is listening/ready for Selenium execution.")
        
        # Proxy Settings
        info("Setting proxy settings for [Browser] object")  
        def capabilities():
            c = DesiredCapabilities.CHROME.copy()
            if manualseleniumproxy: # set True for manual proxy, otherwise use selenium default
                p = Proxy()                                     
                p.proxy_type = ProxyType.MANUAL
                p.http_proxy = f"127.0.0.1:{settings.port}" # proxy is localhost:port matching the proxy port
                info(p.http_proxy)
                p.add_to_capabilities(c)
            c['acceptInsecureCerts'] = True
            return c
    
        # Update keyword args/give access to parent class members (webdriver.Chrome)
        kwargs.update(desired_capabilities=capabilities())
        info(f'webdriver.Chrome().__init__({kwargs})')
        super().__init__(**kwargs)

    def stopproxy(self):
        def info(): pass
        info = self.__info
        # stop proxy
        self.__shutdown.set()
        p = self.__process
        p.stdin.write(b"\n\n")
        p.stdin.close()

    def __del__(self):        
        def info(): pass
        info = self.__info
        info(f"Browser.__del__()")

        # stop proxy on garbage collection
        if self.__proxyshutdown is None: self.stopproxy()

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

        # print stdout archive list w/tabs (stdout history)
        s.insert(0, "Completed:\n")
        info("".join(s), end="")
