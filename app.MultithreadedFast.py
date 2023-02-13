import asyncio      # https://docs.python.org/3/library/asyncio.html#module-asyncio
import json
import time
import requests
from codetiming import Timer
from functools import partial

_ = dict()  # dictionary containing tasks and pids for each listener port (fast, selenium, & stop commands) -- using underscore for shorthand


name, settings = "Example Scan", "#FindMe"
token, url, cicd = "", "", ""

# Fetch config from config.json
async def config():
    with open('config.json') as f:
        return json.load(f)
        

# Fetch scan settings through REST
async def scanSettings(url, token, query):
    with requests.get(f"{url}/application-version-scan-settings/scan-settings-summary-list?searchText={query}",headers={"Content-Type": "application/json","Authorization": f"FortifyToken {token}"}) as r:
        #print(r.text)
        return json.loads(r.text)


# Starts the fast proxy listening on a port
async def fast(p):
    print(f"fast({p})")
    f = "fastproc"
    cmd = "ping 127.0.0.1"
    cmd = f"fast.exe -CIToken {token} -CICDToken {cicd} -u http://localhost:64814/api -p {p} -n \"{name} port {p}\""
    _[p][f] = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    o = _[p][f].stdout
    for i in range(50):
        l = (await o.readline()).decode("utf-8")
        if len(l) > 0:
            print(f"{p}: {l}", end="")
            if "Listening" in l: startSelenium(p)
    
    o,e = await _[p][f].communicate()
    print(f'[{cmd!r} exited with {_[p][f].returncode}]')

# Creates Task to startup FAST proxy
async def startFast(port):
    p,f = port, "fast"
    print(f"startFast({p})")
    if (p in _)==False:
        _[p] = dict()
        _[p][f] = asyncio.create_task(fast(p),name=f"{f} {p}")
        _[p][f].add_done_callback(partial(doneFast,p=p))

# Callback to clean tasks
def doneFast(t, p):     #t=task, p=port
    print(f"doneFast({t},{p})")
    _.pop(p)


# Executes the Selenium SIDE runner
async def selenium(p):
    print(f"selenium({p})")
    f = "workproc"
    cmd = f"selenium-side-runner --proxy-type=manual --proxy-options=\"http=localhost:{p} bypass=[https://*.net]\" \"ZeroBank.side\""
    #cmd = "ping 127.0.0.1"
    _[p][f] = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)    
    o, e = await _[p][f].communicate()
    print(f'[{cmd!r} exited with {_[p][f].returncode}]')
    if o:
        print(f'[stdout]\n{o.decode()}')
    await stopFast(p)

# Wraps the Selenium task
def startSelenium(port):
    p,f = port, "work"
    print(f"startSelenium({p})")
    if (f in _[p]):
        print("Selenium already started")
    else:
        _[p][f] = asyncio.create_task(selenium(p),name=f"{f} {p}")
        _[p][f].add_done_callback(partial(doneSelenium,p=p))

def doneSelenium(t, p):     #callback t=task, p=port
    print(f"doneSelenium({t},{p})")
    _[p].pop("workproc")    # process
    _[p].pop("work")        # task


# Stops the FAST proxy
async def stop(p):
    print(f"stop({p})")
    f = "stopproc"
    cmd = f"fast.exe -p {p} -s"
    _[p][f] = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)    
    o, e = await _[p][f].communicate()
    print(f'[{cmd!r} exited with {_[p][f].returncode}]')
    if o:
        print(f'[stdout]\n{o.decode()}')
        
async def stopFast(port):
    p,f = port, "stop"
    print(f"stopFast({p})")
    _[p][f] = asyncio.create_task(stop(p),name=f"{f} {p}")
    _[p][f].add_done_callback(partial(doneStop,p=p))

def doneStop(t, p):     #callback t=task, p=port
    print(f"doneStop({t},{p})")
    _[p].pop("stopproc")    # process
    _[p].pop("stop")        # task



async def main():
    timer = Timer(text=f"main() elapsed time: {{:.4f}}")
    timer.start()
    print(f"main() started at {time.strftime('%X')}")
    
    c = await config()
    global token, url
    token, url = c["token"], c["url"]

    s = await scanSettings(url, token, settings)
    global cicd
    cicd = s["items"][0]["cicdToken"]
    print(f"Using cicdToken = '{cicd}'")
    
    for i in range(8156, 8158):
        await startFast(i)

    while len(_.keys()) > 0:
        await asyncio.sleep(1)
    print(*_.keys())
    print(f"main() finished at {time.strftime('%X')}")
    timer.stop()


asyncio.run(main())


