from selenium.webdriver.common.by import By
from bookingapp.test.page.BasePage import BasePage


class HomePage(BasePage):
    URL = 'http://127.0.0.1:5000'

    # ── Locators ─────────────────────────────────────────────────────────
    # Top-bar
    WELCOME_TEXT   = (By.CSS_SELECTOR, '.top-bar .date-time')
    USERNAME_LABEL = (By.CSS_SELECTOR, '.top-bar .auth strong')
    LOGOUT_BTN     = (By.CSS_SELECTOR, '.top-bar .auth .btn-outline-danger')
    LOGIN_LINK     = (By.CSS_SELECTOR, '.top-bar .auth a[href*="login"]')

    # Search
    SEARCH_INPUT   = (By.ID,           'search-input')
    SEARCH_BTN     = (By.ID,           'search-btn')

    # Tab navigation
    TAB_VENUES    = (By.CSS_SELECTOR, '.nav-tabs a[data-target="venues"]')
    TAB_BOOKED    = (By.CSS_SELECTOR, '.nav-tabs a[data-target="booked"]')
    TAB_FAVORITES = (By.CSS_SELECTOR, '.nav-tabs a[data-target="favorites"]')

    # Venue cards (tab Danh sách sân)
    VENUE_CARDS    = (By.CSS_SELECTOR, '#venues .venue-card')
    VENUE_NAMES    = (By.CSS_SELECTOR, '#venues .venue-card h3')
    FIRST_BOOK_BTN = (By.CSS_SELECTOR, '#venues .venue-card:first-child .book-btn')
    FIRST_FAV_BTN  = (By.CSS_SELECTOR, '#venues .venue-card:first-child .fav-btn')

    # Booked list
    BOOKED_CARDS   = (By.CSS_SELECTOR, '#booked .venue-card')

    # Favorites list
    FAV_CARDS      = (By.CSS_SELECTOR, '#favorites .venue-card')

    def open_page(self):
        self.open(self.URL)

    # ── Actions ──────────────────────────────────────────────────────────
    def search(self, keyword):
        self.typing(*self.SEARCH_INPUT, keyword)
        self.click(*self.SEARCH_BTN)

    def click_tab_venues(self):
        self.click(*self.TAB_VENUES)

    def click_tab_booked(self):
        self.click(*self.TAB_BOOKED)

    def click_tab_favorites(self):
        self.click(*self.TAB_FAVORITES)

    def click_first_book_btn(self):
        """Bấm 'ĐẶT LỊCH' trên card đầu tiên → chuyển sang VenuePage."""
        self.click(*self.FIRST_BOOK_BTN)

    def toggle_first_favorite(self):
        """Bấm nút tim trên card đầu tiên."""
        self.click(*self.FIRST_FAV_BTN)

    def get_logged_in_username(self):
        return self.get_text(*self.USERNAME_LABEL)

    def logout(self):
        self.click(*self.LOGOUT_BTN)

    # ── Assertion helpers ─────────────────────────────────────────────────
    def get_venue_cards(self):
        return self.finds(*self.VENUE_CARDS)

    def get_venue_names(self):
        return [e.text for e in self.finds(*self.VENUE_NAMES)]

    def get_booked_cards(self):
        return self.finds(*self.BOOKED_CARDS)

    def get_fav_cards(self):
        return self.finds(*self.FAV_CARDS)