"""
URL Configeration for the Books app.

This module defines the URL patterns for the books application.
It maps URL paths to their corresponding view functions.

"""

from django.urls import path
from .views import book_search_view

urlpatterns = [
    path("", book_search_view, name="book_search"),
]
