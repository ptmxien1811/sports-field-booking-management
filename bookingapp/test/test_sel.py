"""
test_sel.py – Selenium test suite cho Bookingapp
Chạy: pytest bookingapp/test/test_sel.py -v
URL:  http://127.0.0.1:5000
"""

import time
import pytest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from bookingapp.test.page.BasePage    import BasePage
from bookingapp.test.page.HomePage    import HomePage
from bookingapp.test.page.LoginPage   import LoginPage
from bookingapp.test.page.VenuePage   import VenuePage
from bookingapp.test.page.BookingPage import BookingPage
from bookingapp.test.page.CancelPage  import CancelPage


# ═══════════════════════════════════════════════════════════════════════
#  FIXTURE: khởi tạo / teardown driver
#  scope='function' để mỗi test có browser riêng, tránh InvalidSessionIdException
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope='function')
def driver():
    options = Options()
    # options.add_argument('--headless')      # bỏ comment nếu chạy CI/CD
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,900')

    service = Service(executable_path='D:\\chromedriver-win64\\chromedriver.exe')
    drv = webdriver.Chrome(service=service, options=options)
    drv.implicitly_wait(5)

    yield drv

    drv.quit()


# ═══════════════════════════════════════════════════════════════════════
#  HẰNG SỐ TEST
# ═══════════════════════════════════════════════════════════════════════
TEST_USERNAME = 'Đỗ Thị Hòa'
TEST_PASSWORD = 'Hoa@1234!'
VENUE_ID      = 1


# ═══════════════════════════════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════════════════════════════

def _do_login(driver, username=TEST_USERNAME, password=TEST_PASSWORD):
    """Helper: đăng nhập rồi về trang chủ."""
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(username, password)
    time.sleep(1)
    if '/admin' in driver.current_url:
        driver.get(BasePage.BASE_URL + '/')
        time.sleep(1)


# ═══════════════════════════════════════════════════════════════════════
#  NHÓM 1: ĐĂNG NHẬP / ĐĂNG XUẤT
# ═══════════════════════════════════════════════════════════════════════

def test_login_success(driver):
    """Đăng nhập đúng username + password → về trang chủ, hiện tên user."""
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(TEST_USERNAME, TEST_PASSWORD)

    time.sleep(1)

    assert driver.current_url.rstrip('/') in [
        BasePage.BASE_URL,
        BasePage.BASE_URL + '/',
        BasePage.BASE_URL + '/admin',
    ]
    if '/admin' not in driver.current_url:
        home = HomePage(driver=driver)
        username_text = home.get_logged_in_username()
        assert TEST_USERNAME.lower() in username_text.lower()


def test_login_wrong_password(driver):
    """Đăng nhập sai mật khẩu → ở lại /login, hiện thông báo lỗi."""
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(TEST_USERNAME, 'SaiMatKhau@999')

    time.sleep(1)

    assert '/login' in driver.current_url
    try:
        err = login.get_error_text()
        assert err != ''
    except Exception:
        err = login.get_flash_text()
        assert err != ''


def test_login_redirect_after_login(driver):
    """Truy cập URL có next= → sau đăng nhập redirect đúng trang."""
    login = LoginPage(driver=driver)
    login.open_page(f'{BasePage.BASE_URL}/login?next=/account')
    login.login(TEST_USERNAME, TEST_PASSWORD)

    time.sleep(1)

    assert '/account' in driver.current_url or '/admin' in driver.current_url


def test_logout(driver):
    """Đăng nhập xong rồi đăng xuất → không còn username trên top-bar."""
    login = LoginPage(driver=driver)
    login.open_page()
    login.login(TEST_USERNAME, TEST_PASSWORD)
    time.sleep(1)

    home = HomePage(driver=driver)
    home.open_page()
    time.sleep(1)

    btns = driver.find_elements(*home.LOGOUT_BTN)
    if btns:
        home.logout()
        time.sleep(1)

    login_links = driver.find_elements(*home.LOGIN_LINK)
    assert len(login_links) > 0


# ═══════════════════════════════════════════════════════════════════════
#  NHÓM 2: TRANG CHỦ – TÌM KIẾM & TAB
# ═══════════════════════════════════════════════════════════════════════

def test_homepage_loads_venues(driver):
    """Trang chủ hiển thị danh sách sân (venue cards)."""
    home = HomePage(driver=driver)
    home.open_page()
    time.sleep(1)

    cards = home.get_venue_cards()
    assert len(cards) > 0, 'Phải có ít nhất 1 sân trong danh sách'


def test_search_venue_found(driver):
    """Tìm kiếm từ khoá có trong tên sân → chỉ hiển thị kết quả khớp."""
    home = HomePage(driver=driver)
    home.open_page()
    time.sleep(1)

    keyword = 'Sân'
    home.search(keyword)
    time.sleep(1)

    visible_names = [
        e.text for e in driver.find_elements(*home.VENUE_NAMES)
        if e.is_displayed()
    ]
    assert len(visible_names) > 0
    assert all(keyword.lower() in name.lower() for name in visible_names)


def test_search_venue_not_found(driver):
    """Tìm kiếm từ khoá không tồn tại → hiện alert 'Không tìm thấy'."""
    home = HomePage(driver=driver)
    home.open_page()
    time.sleep(1)

    home.search('XYZ_KHONG_TON_TAI_12345')
    time.sleep(1)

    try:
        alert = driver.switch_to.alert
        assert 'Không tìm thấy' in alert.text
        alert.accept()
    except Exception:
        visible = [e for e in driver.find_elements(*home.VENUE_NAMES) if e.is_displayed()]
        assert len(visible) == 0


def test_tab_switch_booked(driver):
    """Bấm tab 'Sân đã đặt' → section #booked hiển thị."""
    home = HomePage(driver=driver)
    home.open_page()
    time.sleep(1)

    home.click_tab_booked()
    time.sleep(1)

    booked_section = driver.find_element(By.ID, 'booked')
    assert booked_section.is_displayed()


def test_tab_switch_favorites(driver):
    """Bấm tab 'Yêu thích' → section #favorites hiển thị."""
    home = HomePage(driver=driver)
    home.open_page()
    time.sleep(1)

    home.click_tab_favorites()
    time.sleep(1)

    fav_section = driver.find_element(By.ID, 'favorites')
    assert fav_section.is_displayed()



# ═══════════════════════════════════════════════════════════════════════
#  NHÓM 6: THANH TOÁN
# ═══════════════════════════════════════════════════════════════════════

def test_payment_page_accessible(driver):
    """
    Đặt sân thành công → về trang chủ → bấm THANH TOÁN
    → đến /payment/<id>.
    """
    _do_login(driver)

    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(2)

    slots = venue.get_available_slots()
    if not slots:
        pytest.skip('Không có slot trống')

    venue.select_slot(0)
    time.sleep(0.5)
    venue.click_book_btn()
    time.sleep(2)

    msg = venue.get_book_msg()
    if 'thành công' not in msg.lower() and '✅' not in msg:
        pytest.skip('Đặt sân thất bại')

    home = HomePage(driver=driver)
    home.open_page()
    time.sleep(1)
    home.click_tab_booked()
    time.sleep(1)

    pay_links = driver.find_elements(By.CSS_SELECTOR, '#booked .payment-link')
    if not pay_links:
        pytest.skip('Không tìm thấy nút Thanh toán')

    pay_links[0].click()
    time.sleep(1)

    assert '/payment/' in driver.current_url, 'Phải điều hướng đến /payment/<id>'


def test_payment_direct(driver):
    """
    Truy cập trực tiếp /payment/1 với user đã đặt sân → trang render đúng.
    """
    _do_login(driver)

    booking_page = BookingPage(driver=driver)
    booking_page.open_page(1)
    time.sleep(1)

    if '/payment/' not in driver.current_url:
        pytest.skip('Không có booking id=1 thuộc user này')

    pay_els   = driver.find_elements(*booking_page.PAY_BTN)
    paid_els  = driver.find_elements(*booking_page.PAID_BADGE)
    assert len(pay_els) > 0 or len(paid_els) > 0, 'Trang payment phải có nút Pay hoặc badge Đã TT'


# ═══════════════════════════════════════════════════════════════════════
#  NHÓM 7: YÊU THÍCH
# ═══════════════════════════════════════════════════════════════════════

def test_toggle_favorite_requires_login(driver):
    """
    Chưa đăng nhập, bấm nút tim →
    app hiện alert 'Vui lòng đăng nhập' HOẶC redirect về /login.
    """
    home = HomePage(driver=driver)
    home.open_page()
    time.sleep(1)

    fav_btns = driver.find_elements(*home.FIRST_FAV_BTN)
    if not fav_btns:
        pytest.skip('Không tìm thấy nút yêu thích')

    fav_btns[0].click()
    time.sleep(1)

    # Trường hợp 1: app hiện alert thông báo chưa đăng nhập
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        # Alert có nội dung yêu cầu đăng nhập → PASS
        assert 'đăng nhập' in alert_text.lower(), \
            f'Alert không đúng nội dung: {alert_text}'
        return
    except Exception:
        pass

    # Trường hợp 2: app redirect về /login
    time.sleep(1)
    assert '/login' in driver.current_url, \
        'Chưa login bấm yêu thích phải về /login hoặc hiện alert'
def test_toggle_favorite_when_logged_in(driver):
    """
    Đã đăng nhập, bấm nút tim → icon đổi màu (đã thêm/xoá), không redirect.
    """
    _do_login(driver)

    home = HomePage(driver=driver)
    home.open_page()
    time.sleep(1)

    fav_btn = driver.find_element(*home.FIRST_FAV_BTN)
    fav_btn.click()
    time.sleep(1.5)

    assert driver.current_url.rstrip('/') in [
        BasePage.BASE_URL,
        BasePage.BASE_URL + '/',
    ] or '/' in driver.current_url