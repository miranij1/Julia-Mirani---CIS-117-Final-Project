from django.urls import path
from .views import book_search_view

urlpatterns = [
    path("", book_search_view, name="book_search"),
]
