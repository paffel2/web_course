"""
Маршрутизация URL-адресов приложения аналитики.
"""

from django.urls import path
from .views import (
    DashboardView,
    CampaignListView,
    CampaignDetailView,
    UploadDataView,
    ExportReportView,
    APIDashboardDataView,
    LoginUserView,
    LogoutUserView,
)

urlpatterns = [
    # Главная страница - Дашборд аналитики
    path("", DashboardView.as_view(), name="dashboard"),

    # Управление кампаниями
    path("campaigns/", CampaignListView.as_view(), name="campaigns_list"),
    path("campaigns/<int:campaign_id>/", CampaignDetailView.as_view(), name="campaign_detail"),

    # Импорт и экспорт данных
    path("upload/", UploadDataView.as_view(), name="upload_data"),
    path("export/", ExportReportView.as_view(), name="export_report"),

    # REST / JSON API для асинхронного обновления графиков
    path("api/dashboard-data/", APIDashboardDataView.as_view(), name="api_dashboard_data"),

    # Аутентификация
    path("login/", LoginUserView.as_view(), name="login"),
    path("logout/", LogoutUserView.as_view(), name="logout"),
]

