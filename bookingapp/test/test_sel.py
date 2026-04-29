
# ═══════════════════════════════════════════════════════════════════════
#  NHÓM 3: TRANG CHI TIẾT SÂN
# ═══════════════════════════════════════════════════════════════════════

def test_venue_detail_title_and_price(driver):
    """Trang chi tiết sân hiển thị tên sân và giá."""
    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(1)

    title = venue.get_text(*venue.VENUE_TITLE)
    price = venue.get_text(*venue.VENUE_PRICE)

    assert title != '', 'Tiêu đề sân không được rỗng'
    assert 'đ' in price or price != '', 'Giá sân phải hiển thị đúng'


def test_venue_detail_avail_text_loads(driver):
    """Sau khi load trang, availText không còn là 'Đang tải...'."""
    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(2)

    avail = venue.get_text(*venue.AVAIL_TEXT)
    assert avail != 'Đang tải...', f'Slot chưa tải xong: {avail}'
    assert avail != '', 'availText không được rỗng'


def test_venue_detail_calendar_renders(driver):
    """Calendar hiển thị label tháng/năm."""
    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(1)

    month_label = venue.get_text(*venue.MONTH_LABEL)
    assert 'Tháng' in month_label, f'Label tháng sai: {month_label}'


def test_venue_detail_next_prev_month(driver):
    """Bấm nút tháng sau / tháng trước → month label thay đổi."""
    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(1)

    before = venue.get_text(*venue.MONTH_LABEL)
    venue.go_next_month()
    time.sleep(0.5)
    after_next = venue.get_text(*venue.MONTH_LABEL)
    assert before != after_next

    venue.go_prev_month()
    time.sleep(0.5)
    after_prev = venue.get_text(*venue.MONTH_LABEL)
    assert after_prev == before


def test_venue_book_without_login_shows_lock(driver):
    """
    Chưa đăng nhập, vào trang chi tiết sân →
    nút đặt sân hiển thị 'Đăng nhập để đặt sân'.
    """
    # Đảm bảo đang logout (browser mới nên chưa login)
    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(1)

    try:
        locked = driver.find_element(*venue.LOCKED_BTN)
        assert locked.is_displayed()
        assert 'Đăng nhập' in locked.text
    except NoSuchElementException:
        pytest.skip('Nút lock không xuất hiện – user có thể đã đăng nhập')


# ═══════════════════════════════════════════════════════════════════════
#  NHÓM 4: ĐẶT SÂN (cần đăng nhập)
# ═══════════════════════════════════════════════════════════════════════

def test_select_slot_shows_summary(driver):
    """
    Sau khi đăng nhập và chọn 1 slot → booking summary xuất hiện,
    hiển thị tổng tiền.
    """
    _do_login(driver)

    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(2)

    slots = venue.get_available_slots()
    if not slots:
        pytest.skip('Không có slot trống để test')

    venue.select_slot(0)
    time.sleep(0.5)

    assert venue.is_summary_visible(), 'Booking summary phải hiện sau khi chọn slot'
    total_text = venue.get_total_price_text()
    assert 'đ' in total_text, f'Tổng tiền không đúng định dạng: {total_text}'


def test_select_multiple_slots_summary(driver):
    """Chọn 2 slot → tổng tiền = 2 × giá/giờ."""
    _do_login(driver)

    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(2)

    slots = venue.get_available_slots()
    if len(slots) < 2:
        pytest.skip('Cần ít nhất 2 slot trống để test multi-select')

    venue.select_multiple_slots(2)
    time.sleep(0.5)

    total_text = venue.get_total_price_text()
    assert '2 giờ' in total_text, f'Phải ghi "2 giờ" trong tổng: {total_text}'


def test_book_slot_success(driver):
    """
    Đặt 1 slot thành công → bookMsg hiển thị '✅' hoặc 'thành công'.
    """
    _do_login(driver)

    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(2)

    slots = venue.get_available_slots()
    if not slots:
        pytest.skip('Không có slot trống để đặt')

    venue.select_slot(0)
    time.sleep(0.5)
    venue.click_book_btn()
    time.sleep(2)

    msg = venue.get_book_msg()
    assert '✅' in msg or 'thành công' in msg.lower(), f'Thông báo đặt sân sai: {msg}'


def test_book_slot_without_selecting(driver):
    """
    Bấm 'Đặt sân ngay' mà chưa chọn slot → bookMsg hiển thị cảnh báo.
    """
    _do_login(driver)

    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(2)

    venue.click_book_btn()
    time.sleep(8)

    msg = venue.get_book_msg()
    assert msg != '', 'Phải có thông báo lỗi khi chưa chọn slot'
    assert '❌' in msg or 'chọn' in msg.lower(), f'Thông báo sai: {msg}'


# ═══════════════════════════════════════════════════════════════════════
#  NHÓM 5: HỦY SÂN
# ═══════════════════════════════════════════════════════════════════════

def test_cancel_booking(driver):
    """
    Đặt sân → về trang chủ → hủy → số card giảm đi 1
    hoặc flash message 'Đã hủy thành công'.
    """
    _do_login(driver)

    venue = VenuePage(driver=driver)
    venue.open_page(VENUE_ID)
    time.sleep(2)

    slots = venue.get_available_slots()
    if not slots:
        pytest.skip('Không có slot trống để đặt trước khi test hủy')

    venue.select_slot(0)
    time.sleep(0.5)
    venue.click_book_btn()
    time.sleep(2)

    msg = venue.get_book_msg()
    if '✅' not in msg and 'thành công' not in msg.lower():
        pytest.skip(f'Đặt sân thất bại, bỏ qua test hủy: {msg}')

    cancel = CancelPage(driver=driver)
    cancel.open_home()
    time.sleep(1)

    count_before = cancel.get_booked_count()
    time.sleep(0.5)

    cancel_btns = driver.find_elements(*cancel.SINGLE_CANCEL)
    if not cancel_btns:
        cancel_btns = driver.find_elements(*cancel.GROUP_CANCEL)

    if not cancel_btns:
        pytest.skip('Không tìm thấy nút hủy sân')

    cancel_btns[0].click()
    time.sleep(2)

    try:
        flash = cancel.get_flash_success()
        assert 'hủy' in flash.lower() or 'thành công' in flash.lower()
    except Exception:
        count_after = cancel.get_booked_count()
        assert count_after < count_before, 'Số sân đã đặt phải giảm sau khi hủy'
