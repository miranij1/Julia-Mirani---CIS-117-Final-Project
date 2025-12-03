from django.contrib import admin
from django.urls import path, include  # include is important!

urlpatterns = [
    path("admin/", admin.site.urls),
    path("books/", include("books.urls")),  # send /books/ to the books app
]
