import fastproxy
from selenium.webdriver.common.by import By
import subprocess

# General workflow for capturing a Selenium execution:

    # 1. Start up fast with proxy port (Fast listener)
    # 2. Set Selenium to use same proxy port as Fast listener
    # 3. Execute Selenium code
    # 4. Stop Fast (implied)

# This could be a command to startup an "outer" FAST listener -- intended to be used a chained proxy for the code several lines below:
    # fast.exe -CIToken NzA2YWFmNTktYTE0Ny00ZjRmLTgwM2EtODhjMDE4ZTBjOWMy -CICDToken e9b5e408-1b75-46aa-bb85-5f49624f56e0 -u "http://localhost:64814/api" -p 8160 -n "Example Scan 8160"

port = 8159     # Fast listener port
# Settings class (data structure container) used to pass the FAST settings upon fastproxy.Browser() class init.
    # Note the "chained" proxy pointer on port 8160 -- This code will implement three hops through a proxy chain:  Browser -> FAST proxy on port 8159 -> Separate 8160 proxy listener created from above -> Internet
fast = fastproxy.Settings("NzA2YWFmNTktYTE0Ny00ZjRmLTgwM2EtODhjMDE4ZTBjOWMy","e9b5e408-1b75-46aa-bb85-5f49624f56e0",port,f"Example Scan {port}","http://localhost:64814/api", "127.0.0.1:8160")
browser = fastproxy.Browser(fast, debug=True) 

# This is the Selenium execution
browser.get("http://zero.webappsecurity.com")
browser.find_element(By.XPATH, "//button[@id=\'signin_button\']").click()

# # FAST proxy will automatically stop during class teardown: fastproxy.Browser().__del__() def.







# The "Registry" def's below are useful for reading, saving temporarily, adjusting, and then reverting the system proxy settings.

# The manual workflow (FAST proxy running on port 8085) might look something like:

        # Before starting fast Proxy
        # reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v AutoConfigURL /t REG_SZ /d "" /f
        # reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f
        # reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /t REG_SZ /d 127.0.0.1:8085 /f

        # After Exiting Fast proxy -- put these settings back
        # reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f
        # reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v AutoConfigURL /t REG_SZ /d "http://my.ProxyAutoConfig.com/" /f

# gets the current settings, returning them as a list of REG ADD/DEL command parameters
def readRegistry():
    k = f"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    o = []
    for v in ("AutoConfigURL","ProxyEnable","ProxyServer","ProxyOverride"):
        c = f"reg query \"{k}\" /v \"{v}\""
        r = subprocess.run(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="UTF-8")
        # splitting returns this: ['HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet', 'Settings', 'ProxyEnable', 'REG_DWORD', '0x0']
        # use ternary operator to create either an ADD or DELETE reg statement -- add slices off first two items.
        a = ['add',k]+r.stdout.split()[2:] if (r.returncode == 0) else ['delete',k,v]
        if len(a)==4 : a.append("")     # check for empty string in value (trim() would have excised it)
        o.append(a)
    print(o)
    return o

# writes the temporary desired settings, returns list of ADD/DEL params
def writeRegistry():
    k = f"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    v = [
            ["add",k,"AutoConfigURL","REG_SZ",""],
            ["add",k,"ProxyEnable","REG_DWORD","0x1"],
            ["add",k,"ProxyServer","REG_SZ","127.0.0.1:{port}"],
            ["delete",k,"ProxyOverride"]
        ]
    return revertRegistry(v)

# reverts the settings based upon a saved ADD/DEL param list
def revertRegistry(keys):
    for v in keys:
        if (len(v)>3) : 
            c = f"reg {v[0]} \"{v[1]}\" /v \"{v[2]}\" /t \"{v[3]}\" /d \"{v[4]}\" /f"
        else : 
            c = f"reg {v[0]} \"{v[1]}\" /v \"{v[2]}\" /f"
        print(c)
        r = subprocess.run(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="UTF-8")
    return keys


# These lines show how to read current settings, temporarily overwrite them for fast capture, 
    # read again to see changes, then revert them back to original when done.

# x = readRegistry()        # reads/saves current settings
# writeRegistry()           # write new overrides
# print("")
# y = readRegistry()        # read to see the changes
# revertRegistry(x)         # revert to original settings (saved into 'x' variable 4 lines up)

# reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v "SomethingThatDoesNotExist"
# reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v "AutoConfigURL"
