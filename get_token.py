from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")
    options.add_argument("--quiet")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--enable-unsafe-swiftshader")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_auth_token(url):
    driver = get_driver()
    try:
        driver.get(url)
        
        # انتظر تحميل الصفحة بالكامل
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # احصل على السجلات
        logs = driver.get_log("performance")

        for log in logs:
            log_entry = log["message"]
            if "Authorization" in log_entry:
                try:
                    log_data = json.loads(log_entry)
                    headers = (
                        log_data.get("message", {})
                        .get("params", {})
                        .get("request", {})
                        .get("headers", {})
                    )
                    auth_token = headers.get("Authorization")
                    
                    if auth_token:
                        return auth_token.replace("Bearer ", "")

                except Exception as e:
                    print(f"Error parsing log entry: {e}")
                    return False

        print("No Authorization Token Found in the Logs.")
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False
    
    finally:
        driver.quit()