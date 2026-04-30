from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bookingapp.test.page.BasePage import BasePage


class BookingPage(BasePage):
    """Trang thanh toán: /payment/<booking_id>"""
    URL = 'http://127.0.0.1:5000/payment/1'
    # ── Locators ─────────────────────────────────────────────────────────
    # Thông tin hóa đơn
    BOOKING_ID_TEXT  = (By.CSS_SELECTOR, '.payment-info .booking-id')
    PRODUCT_NAME     = (By.CSS_SELECTOR, '.payment-info .product-name')
    TOTAL_AMOUNT     = (By.CSS_SELECTOR, '.payment-info .total-amount')

    # Phương thức thanh toán
    PAYMENT_METHOD   = (By.ID,           'payment-method')

    # Nút thanh toán
    PAY_BTN          = (By.ID,           'btn-pay')
    PAY_SUCCESS_MSG  = (By.ID,           'btn-pay')      # nội dung thay đổi sau khi thành công

    # Trạng thái "Đã thanh toán"
    PAID_BADGE       = (By.CSS_SELECTOR, '.paid-badge, .payment-btn.disabled-btn')

    # Nút xem hóa đơn (từ trang chủ)
    VIEW_BILL_BTN    = (By.CSS_SELECTOR, '.view-bill-btn')

    def open_page(self, booking_id: int):
        self.open(f'{self.BASE_URL}/payment/{booking_id}')

    # ── Actions ──────────────────────────────────────────────────────────
    def select_payment_method(self, method: str = 'direct'):
        """Chọn phương thức thanh toán: 'direct' hoặc 'online'."""
        from selenium.webdriver.support.ui import Select
        select_el = self.wait_visible(*self.PAYMENT_METHOD)
        Select(select_el).select_by_value(method)

    def click_pay(self):
        self.click(*self.PAY_BTN)

    def confirm_alert(self):
        """Chấp nhận confirm dialog nếu có."""
        wait = WebDriverWait(self.driver, 5)
        try:
            alert = wait.until(EC.alert_is_present())
            alert.accept()
        except Exception:
            pass

    def pay(self, method: str = 'direct'):
        """Chọn phương thức + bấm thanh toán + confirm."""
        self.select_payment_method(method)
        self.click_pay()

    def get_pay_btn_text(self):
        return self.get_text(*self.PAY_BTN)

    def is_paid(self):
        """Kiểm tra trang này đã có trạng thái ĐÃ THANH TOÁN chưa."""
        try:
            el = self.find(*self.PAID_BADGE)
            return el.is_displayed()
        except Exception:
            return False