from selenium.webdriver.common.by import By
from bookingapp.test.page.BasePage import BasePage


class LoginPage(BasePage):
    URL = 'http://127.0.0.1:5000/login'

    # ── Locators ─────────────────────────────────────────────────────────
    # Tab "Tài khoản" (username/password) luôn active mặc định
    USERNAME_INPUT = (By.ID,   'login-username')
    PASSWORD_INPUT = (By.ID,   'pwd-u')
    SUBMIT_BTN     = (By.CSS_SELECTOR, '#tab-username .btn-submit')

    # Đăng nhập bằng Email
    EMAIL_INPUT      = (By.ID,  'login-email')
    EMAIL_PWD_INPUT  = (By.ID,  'pwd-e')
    EMAIL_SUBMIT_BTN = (By.CSS_SELECTOR, '#tab-email .btn-submit')
    TAB_EMAIL_BTN    = (By.CSS_SELECTOR, '.tab-btn[data-tab="tab-email"]')

    # Error / flash message
    ERROR_BOX    = (By.CSS_SELECTOR, '.error-box')
    FLASH_MSG    = (By.CSS_SELECTOR, '.flash-list li')

    def open_page(self, url=None):
        self.open(url or self.URL)

    # ── Actions ──────────────────────────────────────────────────────────
    def login(self, username, password):
        """Đăng nhập bằng username (tab mặc định)."""
        self.typing(*self.USERNAME_INPUT, username)
        self.typing(*self.PASSWORD_INPUT, password)
        self.click(*self.SUBMIT_BTN)

    def login_with_email(self, email, password):
        """Chuyển sang tab Email rồi đăng nhập."""
        self.click(*self.TAB_EMAIL_BTN)
        self.typing(*self.EMAIL_INPUT, email)
        self.typing(*self.EMAIL_PWD_INPUT, password)
        self.click(*self.EMAIL_SUBMIT_BTN)

    # ── Assertions helpers ────────────────────────────────────────────────
    def get_error_text(self):
        return self.get_text(*self.ERROR_BOX)

    def get_flash_text(self):
        return self.get_text(*self.FLASH_MSG)