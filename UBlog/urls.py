# UBlog/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Single source of truth for app routes
    path('', include('main_app.urls')),
]
