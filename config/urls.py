"""
URL configuration for autoparts_analytics project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("analytics.urls")),
]

# Кастомизация панели администратора Django
admin.site.site_header = "Панель администратора | Автозапчасти Аналитика"
admin.site.site_title = "Маркетинговая аналитика автозапчастей"
admin.site.index_title = "Управление рекламными кампаниями и справочниками"
