from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # This sends the root URL (/) to the books app
    path("", include("books.urls")),
]
