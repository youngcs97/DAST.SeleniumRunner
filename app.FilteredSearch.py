import json
import requests

# Fetch config from config.json
def config():
    with open('config.json') as f:
        return json.load(f)
        
# Fetch scanSettings through REST
def scanSettings(url, token, query):
    with requests.get(f"{url}/application-version-scan-settings/scan-settings-summary-list?searchText={query}",headers={"Content-Type": "application/json","Authorization": f"FortifyToken {token}"}) as r:
        return json.loads(r.text)

# Get scanSettings by Name (case-insensitive: note the .upper())
def scanSettingsByName(url, token, name):
    s = scanSettings(url, token, name)
    i = list(filter(lambda x: (x["name"].upper()==name.upper()), s["items"]))
    s["items"]=i
    s["filteredItems"]=len(i)
    return s

c = config()
s = scanSettingsByName(c["url"], c["token"], "Hello Settings 2")
print(f"{s}")
