from selenium.webdriver.common.by import By
from bookingapp.test.page.BasePage import BasePage


class CancelPage(BasePage):
    """
    Không có trang riêng – hành động HỦY SÂN được thực hiện
    trực tiếp trên trang chủ (tab 'Sân đã đặt') bằng POST form.
    """

    URL = 'http://127.0.0.1:5000/'

    # ── Locators ──────────────────────────────────────────────────────────
    TAB_BOOKED       = (By.CSS_SELECTOR, '.nav-tabs a[data-target="booked"]')
    BOOKED_CARDS     = (By.CSS_SELECTOR, '#booked .venue-card')

    SINGLE_CANCEL    = (By.CSS_SELECTOR, '#booked form[action*="cancel-booking"] .cancel-btn')
    GROUP_CANCEL     = (By.CSS_SELECTOR, '#booked form[action*="cancel-group"] .cancel-btn')

    FLASH_SUCCESS    = (By.CSS_SELECTOR, '.alert-success, .flash-list li.success')
    FLASH_DANGER     = (By.CSS_SELECTOR, '.alert-danger,  .flash-list li.danger')

    def open_home(self):
        self.open(self.BASE_URL + '/')

    def go_to_booked_tab(self):
        self.click(*self.TAB_BOOKED)

    # ── Actions ──────────────────────────────────────────────────────────
    def cancel_first_single_booking(self):
        self.go_to_booked_tab()
        self.click(*self.SINGLE_CANCEL)

    def cancel_first_group_booking(self):
        self.go_to_booked_tab()
        self.click(*self.GROUP_CANCEL)

    # ── Assertion helpers ─────────────────────────────────────────────────
    def get_flash_success(self):
        return self.get_text(*self.FLASH_SUCCESS)

    def get_flash_danger(self):
        return self.get_text(*self.FLASH_DANGER)

    def get_booked_count(self):
        self.go_to_booked_tab()
        return len(self.finds(*self.BOOKED_CARDS))