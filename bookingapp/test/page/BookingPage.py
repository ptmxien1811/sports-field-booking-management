from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bookingapp.test.page.BasePage import BasePage


class BookingPage(BasePage):
    """Trang thanh toán: /payment/<booking_id>"""
    URL = 'http://127.0.0.1:5000/payment/1'

    # ── Locators ─────────────────────────────────────────────────────────
    BOOKING_ID_TEXT  = (By.CSS_SELECTOR, '.payment-info .booking-id')
    PRODUCT_NAME     = (By.CSS_SELECTOR, '.payment-info .product-name')
    TOTAL_AMOUNT     = (By.CSS_SELECTOR, '.payment-info .total-amount')

    PAYMENT_METHOD   = (By.ID,           'payment-method')

    PAY_BTN          = (By.ID,           'btn-pay')
    PAY_SUCCESS_MSG  = (By.ID,           'btn-pay')

    PAID_BADGE       = (By.CSS_SELECTOR, '.paid-badge, .payment-btn.disabled-btn')

    VIEW_BILL_BTN    = (By.CSS_SELECTOR, '.view-bill-btn')

    def open_page(self, booking_id: int):
        self.open(f'{self.BASE_URL}/payment/{booking_id}')

    # ── Actions ──────────────────────────────────────────────────────────
    def select_payment_method(self, method: str = 'direct'):
        from selenium.webdriver.support.ui import Select
        select_el = self.wait_visible(*self.PAYMENT_METHOD)
        Select(select_el).select_by_value(method)

    def click_pay(self):
        self.click(*self.PAY_BTN)

    def confirm_alert(self):
        wait = WebDriverWait(self.driver, 5)
        try:
            alert = wait.until(EC.alert_is_present())
            alert.accept()
        except Exception:
            pass

    def pay(self, method: str = 'direct'):
        self.select_payment_method(method)
        self.click_pay()

    def get_pay_btn_text(self):
        return self.get_text(*self.PAY_BTN)

    def is_paid(self):
        try:
            el = self.find(*self.PAID_BADGE)
            return el.is_displayed()
        except Exception:
            return False