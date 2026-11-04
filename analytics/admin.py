"""
Настройка панели администратора Django для моделей аналитики.
Позволяет администратору управлять рекламными кабинетами (Cabinet),
кампаниями и просматривать / редактировать суточные метрики с расчётом ДРР и CPO.
"""

from django.contrib import admin
from .models import Cabinet, Campaign, DailyCampaignMetric


@admin.register(Cabinet)
class CabinetAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    prepopulated_fields = {"code": ("name",)}


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "cabinet", "target_drr", "daily_budget", "status", "start_date", "end_date")
    list_filter = ("status", "cabinet")
    search_fields = ("name",)
    date_hierarchy = "start_date"


@admin.register(DailyCampaignMetric)
class DailyCampaignMetricAdmin(admin.ModelAdmin):
    list_display = (
        "campaign",
        "date",
        "impressions",
        "clicks",
        "cost",
        "cart_additions",
        "orders_count",
        "revenue",
        "calc_drr",
        "calc_cpo",
        "calc_cr_order",
    )
    list_filter = ("date", "campaign__cabinet", "campaign")
    search_fields = ("campaign__name",)
    date_hierarchy = "date"

    @admin.display(description="ДРР (%)")
    def calc_drr(self, obj):
        return f"{obj.drr}%"

    @admin.display(description="CPO (руб.)")
    def calc_cpo(self, obj):
        return f"{obj.cpo} ₽"

    @admin.display(description="CR заказ (%)")
    def calc_cr_order(self, obj):
        return f"{obj.cr_order}%"
