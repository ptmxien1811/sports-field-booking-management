from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    BASE_URL = 'http://127.0.0.1:5000'

    def __init__(self, driver):
        self.driver = driver
        self.wait   = WebDriverWait(driver, 10)

    # ── navigate ────────────────────────────────────────────────────────
    def open(self, url):
        self.driver.get(url)

    # ── find (raw) ──────────────────────────────────────────────────────
    def find(self, by, value):
        return self.driver.find_element(by, value)

    def finds(self, by, value):
        return self.driver.find_elements(by, value)

    # ── wait-based find ─────────────────────────────────────────────────
    def wait_visible(self, by, value):
        return self.wait.until(EC.visibility_of_element_located((by, value)))

    def wait_clickable(self, by, value):
        return self.wait.until(EC.element_to_be_clickable((by, value)))

    def wait_present(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def wait_all_present(self, by, value):
        return self.wait.until(EC.presence_of_all_elements_located((by, value)))

    # ── interaction helpers ─────────────────────────────────────────────
    def typing(self, by, value, text):
        e = self.wait_visible(by, value)
        e.clear()
        e.send_keys(text)

    def click(self, by, value):
        self.wait_clickable(by, value).click()

    def get_text(self, by, value):
        return self.wait_visible(by, value).text

    def scroll_to(self, pixel=0):
        self.driver.execute_script(f'window.scrollTo(0, {pixel})')