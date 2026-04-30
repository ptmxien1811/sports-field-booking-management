from selenium.webdriver.common.by import By
from bookingapp.test.page.BasePage import BasePage


class VenuePage(BasePage):
    """Trang chi tiết sân: /venue/<id>"""
    URL = 'http://127.0.0.1:5000/venue/1'

    # ── Locators ─────────────────────────────────────────────────────────
    VENUE_TITLE   = (By.CSS_SELECTOR, '.vd-title')
    VENUE_ADDRESS = (By.CSS_SELECTOR, '.vd-addr')
    VENUE_PRICE   = (By.CSS_SELECTOR, '.vd-price')
    AVAIL_TEXT    = (By.ID,           'availText')

    MONTH_LABEL   = (By.ID,           'monthLabel')
    DAYS_GRID     = (By.ID,           'daysGrid')
    NEXT_MONTH    = (By.CSS_SELECTOR, '.nav-btn:last-child')
    PREV_MONTH    = (By.CSS_SELECTOR, '.nav-btn:first-child')

    MORNING_SLOTS   = (By.CSS_SELECTOR, '#morning .slot:not(.booked):not(.past)')
    AFTERNOON_SLOTS = (By.CSS_SELECTOR, '#afternoon .slot:not(.booked):not(.past)')
    EVENING_SLOTS   = (By.CSS_SELECTOR, '#evening .slot:not(.booked):not(.past)')
    ALL_AVAIL_SLOTS = (By.CSS_SELECTOR, '.slot:not(.booked):not(.past)')

    BOOKING_SUMMARY  = (By.ID,           'bookingSummary')
    TOTAL_PRICE_TEXT = (By.ID,           'totalPriceText')
    SLOT_TAGS        = (By.CSS_SELECTOR, '.vd-slot-tag')

    BOOK_BTN    = (By.ID,           'bookBtn')
    BOOK_MSG    = (By.ID,           'bookMsg')
    LOCKED_BTN  = (By.CSS_SELECTOR, '.vd-book-btn--locked')

    DAILY_LIMIT = (By.ID, 'dailyLimitInfo')

    REVIEW_BTN     = (By.CSS_SELECTOR, '.vd-review-btn')
    REVIEW_FORM    = (By.ID,           'reviewForm')
    STAR_OPTS      = (By.CSS_SELECTOR, '.star-opt')
    REVIEW_CONTENT = (By.ID,           'reviewContent')
    SUBMIT_REVIEW  = (By.CSS_SELECTOR, '#reviewForm button')
    REVIEW_MSG     = (By.ID,           'reviewMsg')
    REVIEW_LIST    = (By.ID,           'reviewList')
    REVIEW_CARDS   = (By.CSS_SELECTOR, '#reviewList .vd-review-card')

    def open_page(self, venue_id: int):
        self.open(f'{self.BASE_URL}/venue/{venue_id}')

    # ── Calendar ──────────────────────────────────────────────────────────
    def go_next_month(self):
        self.click(*self.NEXT_MONTH)

    def go_prev_month(self):
        self.click(*self.PREV_MONTH)

    def select_day(self, day_number: int):
        self.wait_all_present(*self.DAYS_GRID)
        grid = self.find(*self.DAYS_GRID)
        day_divs = grid.find_elements(By.CSS_SELECTOR, '.day:not(.past):not(.other)')
        for d in day_divs:
            if d.text.strip() == str(day_number):
                d.click()
                return
        raise ValueError(f'Không tìm thấy ngày {day_number} trong calendar')

    # ── Slots ─────────────────────────────────────────────────────────────
    def get_available_slots(self):
        return self.finds(*self.ALL_AVAIL_SLOTS)

    def select_slot(self, index: int = 0):
        slots = self.get_available_slots()
        if not slots:
            raise ValueError('Không có slot trống nào để chọn')
        slots[index].click()
        return slots[index].text.strip()

    def select_multiple_slots(self, count: int = 2):
        slots = self.get_available_slots()
        selected_labels = []
        for i in range(min(count, len(slots))):
            slots[i].click()
            selected_labels.append(slots[i].text.strip())
        return selected_labels

    # ── Booking ───────────────────────────────────────────────────────────
    def click_book_btn(self):
        self.click(*self.BOOK_BTN)

    def get_book_msg(self):
        return self.get_text(*self.BOOK_MSG)

    def get_total_price_text(self):
        return self.get_text(*self.TOTAL_PRICE_TEXT)

    def is_summary_visible(self):
        try:
            el = self.find(*self.BOOKING_SUMMARY)
            return el.is_displayed()
        except Exception:
            return False

    def remove_slot_tag(self, label: str):
        tags = self.finds(*self.SLOT_TAGS)
        for tag in tags:
            if label in tag.text:
                tag.find_element(By.CSS_SELECTOR, '.remove-slot').click()
                return
        raise ValueError(f'Không tìm thấy slot tag: {label}')

    # ── Reviews ───────────────────────────────────────────────────────────
    def open_review_form(self):
        self.click(*self.REVIEW_BTN)

    def set_star_rating(self, stars: int = 5):
        star_els = self.finds(*self.STAR_OPTS)
        star_els[stars - 1].click()

    def write_review(self, content: str):
        self.typing(*self.REVIEW_CONTENT, content)

    def submit_review(self):
        self.click(*self.SUBMIT_REVIEW)

    def get_review_msg(self):
        return self.get_text(*self.REVIEW_MSG)

    def get_review_count(self):
        return len(self.finds(*self.REVIEW_CARDS))