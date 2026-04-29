
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
