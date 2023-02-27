import fastproxy
from selenium.webdriver.common.by import By


fast = fastproxy.Settings("NzA2YWFmNTktYTE0Ny00ZjRmLTgwM2EtODhjMDE4ZTBjOWMy","e9b5e408-1b75-46aa-bb85-5f49624f56e0",8156,"Example Scan 8156","http://localhost:64814/api")
browser = fastproxy.Browser(fast) 
browser.get("http://zero.webappsecurity.com")
browser.find_element(By.XPATH, "//button[@id=\'signin_button\']").click()

