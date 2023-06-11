import devwebproxy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
import subprocess


# Devweb/LoadRunnerDeveloper (Proxy Capture) can be downloaded from here:  https://www.microfocus.com/marketplace/appdelivery/content/LoadRunner-Developer
# the startup commands are in .vscode/tasks.json

# set the Selenium proxy capture wrapper
settings = devwebproxy.Settings(port=8156, file="ZeroBank.Proxy.har")
browser = devwebproxy.Browser(settings=settings, debug=True, manualseleniumproxy=True) 


# This is the Selenium execution to capture (simulates Logon)
browser.get("http://zero.webappsecurity.com/logout.html")
browser.get("http://zero.webappsecurity.com/")
WebDriverWait(browser, 5).until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, ".disclaimer")))
browser.find_element(By.XPATH, "//button[@id=\'signin_button\']").click()
browser.find_element(By.ID, "user_login").send_keys("username")
browser.find_element(By.ID, "user_password").send_keys("password")
browser.find_element(By.ID, "user_remember_me").click()
browser.find_element(By.NAME, "submit").click()
browser.get("http://zero.webappsecurity.com/bank/account-summary.html")
WebDriverWait(browser, 5).until(expected_conditions.visibility_of_element_located((By.CSS_SELECTOR, ".disclaimer")))



# proxy will automatically stop during class teardown: devwebproxy.Browser().__del__() def.