"""
Main URL Configuration for the Gutenberg Project.

This is the root URL configeration file for the Gutenberg Project Django application.
It routes requests to the appropriate applications within the project.

"""

from django.contrib import admin
from django.urls import path, include

#Main URL patterns for the entire project
urlpatterns = [
    #Django admin inteface
    path("admin/", admin.site.urls),
    # Root URL (/) routes to the books app
    #This makes the books app the main page of the website
    path("", include("books.urls")),
]
