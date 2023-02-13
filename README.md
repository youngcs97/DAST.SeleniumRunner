# DAST.SeleniumRunner
Demonstrates how to perform DAST (Dynamic Application Security Testing) scanning with OpenText Fortify products (Fortify-on-Demand, WebInspect, or ScanCentral) using Selenium scripts (or other functional testing tools) as a workflow base.

Selenium (https://github.com/SeleniumHQ/) is one of the most popular Functional Testing/Browser Automation tools.
Many QA teams work with the Selenium IDE and .SIDE files (the IDE file extension for saving projects).
Why not harness those scripts as the basis for Security (DAST) testing.

This project shows how to use the Selenium Side Runner (execution platform for native SIDE files) and a man-in-middle proxy to capture a user workflow and feed it into Fortify for DAST scanning.

The concepts:

- The project contains an example SIDE file:  Zerobank.side
- This SIDE file connects to http://zero.webappsecurity.com (Fortify's example website -- contains many security flaws to demonstrate DAST findings)
- Once connected, it logs into the fictitious Online Banking app, and then clicks the "Account Summary," verifying the presence of various DOM elements on the page.

- Fortify family products ship with a man-in-middle proxy server that captures traffic for use in a workflow-driven scan (executable name:  Fast.exe)
- The app.MultithreadedFast.js and .py files spool up two simultaneous instances of FAST proxy, execute the Zerobank.side file pointing at the FAST listener ports, then shutdown the FAST proxy once the Selenium script has fully executed.
- This in turn will kick off a DAST scan using REST API's in SSC/Scan Central

Although this example specifically uses SSC/ScanCentral, the concepts could apply to any of the Fortify products:

1.  Fortify-on-Demand (the SaaS version of Fortify DAST)
2.  SSC/Scan Central (the offCloud server version of Fortify DAST)
3.  WebInspect (the "desktop"-style standalone version of Fortify DAST)

Likewise, these proxy capture concepts also apply to nearly any Functional or Performance testing platform, not just Selenium.  You could perform a similar proxy capture from Gatling, JMeter, Unified Functional Test, Puppeteer, Tosca, or any other popular testing framework.

Beyond the MultithreadedFast files, there is also an app.FilteredSearch.js and .py to show how to leverage the SSC API's.  All three flavors of the Fortify DAST family have built-in REST API's for performing common automation tasks--if you can do it in the GUI, it can be mimicked via the API.

Enjoy! (and please hit me up with questions).


See "commands.sh" for hints on how to install pre-requisites.  I also encourage an NPM and/or Python update before you begin (node_modules was not checked in).





