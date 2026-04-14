"""Page object models."""

from pages.base_page import BasePage
from pages.book_detail_page import BookDetailPage
from pages.login_page import LoginPage
from pages.reading_list_page import ReadingListPage
from pages.search_page import SearchPage

__all__ = [
    "BasePage",
    "BookDetailPage",
    "LoginPage",
    "ReadingListPage",
    "SearchPage",
]
