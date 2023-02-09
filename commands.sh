# Selenium Commnd-Line runner:  https://www.npmjs.com/package/selenium-side-runner
#                               https://www.selenium.dev/selenium-ide/docs/en/introduction/command-line-runner
#
#   Install using NPM:          npm install -g selenium-side-runner
#                               npm install -g chromedriver

# Simple execution (no proxy)
selenium-side-runner "ZeroBank.side"
selenium-side-runner -d -o logs "ZeroBank.side"     #logging with -o    can use YML config with -n

# How to use FAST Proxy:  https://youtu.be/4uliU_Z-qFo
# Using HAR files in WI/SSC:  https://youtu.be/MJ_aRM-wJQI

#   Microfocus Performance Engineering toolkit (contains local proxyrecorder; intercepts traffic like FAST, but saves to HAR file instead):
#       - Toolkit download:  https://marketplace.microfocus.com/appdelivery/content/loadrunner-developer
#       - Usage instructions:  https://admhelp.microfocus.com/lrd/en/2022-2022-r2/help/Content/DevWeb/DW-proxy_recorder.htm 


# Passing proxy settings - for use with either FAST or Proxyrecorder
selenium-side-runner --proxy-type=manual --proxy-options="http=localhost:8156 bypass=[https://*.net]" "ZeroBank.side"
selenium-side-runner -n "ZeroBank.side.yaml" "ZeroBank.side"

# Use PAC file for best flexibility (use javascript function w/RegEx to control capture down to url/host level)
#    //Example at:  http://cyoung.us/proxy-pac.js
#    function FindProxyForURL (url, host) {
#        if (shExpMatch(url, "*webappsecurity.com*")) return 'PROXY localhost:8156'
#        return 'DIRECT';
#    }
selenium-side-runner --proxy-type=pac --proxy-options="http://cyoung.us/proxy-pac.js" "ZeroBank.side"


# Using grid (haven't tested if proxy settings can be passed)
selenium-side-runner --server "http://localhost:4444/wd/hub" -c "browserName='internet explorer' version='11.0' platform='Windows 8.1'" "ZeroBank.side"




# http://localhost:64814/api/v2/scans/scan-summary-list?searchText=&startedOnStartDate=&startedOnEndDate=&scanStatusType=&orderBy=&orderByDirection=&offset=0&limit=100
# http://localhost:64814/api/v2/application-version-scan-settings/scan-settings-summary-list?searchText=&modifiedStartDate=&modifiedEndDate=&scanType=&orderBy=&orderByDirection=&offset=0&limit=5
# http://localhost:64814/api/v2/policies?includeCustomPolicies=true
# http://localhost:64814/api/v2/application-version-binary-files/upload-session
# http://localhost:64814/api/v2/application-version-binary-files/upload?applicationVersionId=10000&sessionId=3&offset=0
# http://localhost:64814/api/v2/application-version-scan-settings/scan-settings-summary-list?searchText=Hello+Settings+2
# http://localhost:64814/api/v2/applications
