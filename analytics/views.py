"""
Модуль представлений (Views) веб-приложения аналитики рекламных кампаний.
Предметная область: интернет-магазин автозапчастей (учет рекламных кабинетов Cabinet).
"""

import csv
import json
from datetime import date, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator

from .models import Cabinet, Campaign, DailyCampaignMetric
from .services import (
    filter_metrics_queryset,
    get_dashboard_summary,
    get_daily_timeline_data,
    get_platform_breakdown,
    get_campaigns_table_data,
    get_conversion_funnel,
)


class LoginUserView(View):
    """
    Представление авторизации пользователя (маркетолог / администратор).
    """
    template_name = "analytics/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = AuthenticationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Добро пожаловать в систему, {user.username}!")
            return redirect("dashboard")
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
            return render(request, self.template_name, {"form": form})


class LogoutUserView(View):
    """
    Представление выхода из системы.
    """
    def get(self, request):
        logout(request)
        messages.info(request, "Вы успешно вышли из системы.")
        return redirect("login")


class DashboardView(LoginRequiredMixin, View):
    """
    Главный аналитический дашборд показателей эффективности рекламы:
    - карточки ключевых KPI (ДРР, CPO, Выручка, Расход, Клики, Корзины, Заказы, CR);
    - воронка конверсий (Показы -> Переходы в карточку -> Корзины -> Заказы);
    - динамика показателей по дням (Chart.js);
    - распределение затрат и выручки между рекламными кабинетами;
    - сводная аналитическая таблица по кампаниям.
    """
    template_name = "analytics/dashboard.html"

    def get(self, request):
        today = date.today()
        default_date_from = (today - timedelta(days=30)).isoformat()
        default_date_to = today.isoformat()

        date_from = request.GET.get("date_from", default_date_from)
        date_to = request.GET.get("date_to", default_date_to)
        cabinet_id = request.GET.get("cabinet") or request.GET.get("platform", "")
        campaign_id = request.GET.get("campaign", "")

        filter_params = {
            "date_from": date_from,
            "date_to": date_to,
            "cabinet": cabinet_id,
            "campaign": campaign_id,
        }

        qs = filter_metrics_queryset(filter_params)

        summary = get_dashboard_summary(qs)
        funnel = get_conversion_funnel(summary)
        timeline = get_daily_timeline_data(qs)
        cabinet_breakdown = get_platform_breakdown(qs)
        campaigns_table = get_campaigns_table_data(qs)

        cabinets = Cabinet.objects.filter(is_active=True)
        campaigns = Campaign.objects.all()

        context = {
            "summary": summary,
            "funnel": funnel,
            "timeline_json": json.dumps(timeline, ensure_ascii=False),
            "platform_json": json.dumps(cabinet_breakdown, ensure_ascii=False),
            "campaigns_table": campaigns_table,
            "cabinets": cabinets,
            "campaigns": campaigns,
            "filters": filter_params,
        }

        return render(request, self.template_name, context)


class CampaignListView(LoginRequiredMixin, View):
    """
    Список рекламных кампаний интернет-магазина автозапчастей.
    """
    template_name = "analytics/campaigns.html"

    def get(self, request):
        campaigns = Campaign.objects.select_related("cabinet").all()
        cabinets = Cabinet.objects.all()

        status_filter = request.GET.get("status")
        cabinet_filter = request.GET.get("cabinet") or request.GET.get("platform")

        if status_filter:
            campaigns = campaigns.filter(status=status_filter)
        if cabinet_filter:
            campaigns = campaigns.filter(cabinet_id=cabinet_filter)

        context = {
            "campaigns": campaigns,
            "cabinets": cabinets,
            "platforms": cabinets,
            "selected_status": status_filter or "",
            "selected_cabinet": cabinet_filter or "",
            "selected_platform": cabinet_filter or "",
        }
        return render(request, self.template_name, context)


class CampaignDetailView(LoginRequiredMixin, View):
    """
    Детальная аналитика по выбранной рекламной кампании:
    суточная динамика, история метрик, расчетные показатели (ДРР, CPO, CR, CTR).
    """
    template_name = "analytics/campaign_detail.html"

    def get(self, request, campaign_id):
        campaign = get_object_or_404(
            Campaign.objects.select_related("cabinet"),
            id=campaign_id
        )

        metrics_qs = campaign.metrics.all().order_by("-date")

        summary = get_dashboard_summary(metrics_qs)
        funnel = get_conversion_funnel(summary)
        timeline = get_daily_timeline_data(metrics_qs)

        paginator = Paginator(metrics_qs, 20)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "campaign": campaign,
            "summary": summary,
            "funnel": funnel,
            "timeline_json": json.dumps(timeline, ensure_ascii=False),
            "page_obj": page_obj,
        }
        return render(request, self.template_name, context)


class UploadDataView(LoginRequiredMixin, View):
    """
    Загрузка и импорт суточных показателей рекламных кампаний из файла CSV.
    """
    template_name = "analytics/upload.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        csv_file = request.FILES.get("file")
        if not csv_file:
            messages.error(request, "Файл не выбран. Пожалуйста, прикрепите CSV файл.")
            return render(request, self.template_name)

        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Ошибка: поддерживается только формат CSV.")
            return render(request, self.template_name)

        try:
            file_data = csv_file.read().decode("utf-8-sig")
            reader = csv.DictReader(file_data.splitlines(), delimiter=";")

            if not reader.fieldnames or len(reader.fieldnames) == 1:
                reader = csv.DictReader(file_data.splitlines(), delimiter=",")

            created_count = 0
            updated_count = 0

            for row in reader:
                camp_name = row.get("campaign_name", "").strip()
                if not camp_name:
                    continue

                campaign = Campaign.objects.filter(name=camp_name).first()
                if not campaign:
                    default_cabinet = Cabinet.objects.first()
                    campaign = Campaign.objects.create(
                        name=camp_name,
                        cabinet=default_cabinet,
                        target_drr=Decimal("15.00"),
                        daily_budget=Decimal("1500.00"),
                        start_date=row.get("date", date.today().isoformat()),
                        status="active"
                    )

                metric_date = row.get("date", "").strip()
                impressions = int(row.get("impressions", 0) or 0)
                clicks = int(row.get("clicks", 0) or 0)
                cost = Decimal(str(row.get("cost", 0)).replace(",", ".").strip() or "0")
                cart_additions = int(row.get("cart_additions", 0) or 0)
                orders_count = int(row.get("orders_count", 0) or 0)
                revenue = Decimal(str(row.get("revenue", 0)).replace(",", ".").strip() or "0")

                obj, created = DailyCampaignMetric.objects.update_or_create(
                    campaign=campaign,
                    date=metric_date,
                    defaults={
                        "impressions": impressions,
                        "clicks": clicks,
                        "cost": cost,
                        "cart_additions": cart_additions,
                        "orders_count": orders_count,
                        "revenue": revenue,
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            messages.success(
                request,
                f"Импорт успешно завершен! Создано записей: {created_count}, обновлено: {updated_count}."
            )
            return redirect("dashboard")

        except Exception as e:
            messages.error(request, f"Ошибка при обработке файла: {str(e)}")
            return render(request, self.template_name)


class ExportReportView(LoginRequiredMixin, View):
    """
    Экспорт аналитического отчета по рекламным кампаниям в CSV.
    """
    def get(self, request):
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        cabinet_id = request.GET.get("cabinet") or request.GET.get("platform")
        campaign_id = request.GET.get("campaign")

        filter_params = {
            "date_from": date_from,
            "date_to": date_to,
            "cabinet": cabinet_id,
            "platform": cabinet_id,
            "campaign": campaign_id,
        }

        qs = filter_metrics_queryset(filter_params)
        campaigns_table = get_campaigns_table_data(qs)

        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="advertising_cabinets_report.csv"'

        writer = csv.writer(response, delimiter=";")
        writer.writerow([
            "ID",
            "Название кампании",
            "Рекламный кабинет",
            "Статус",
            "Показы",
            "Клики (переходы)",
            "CTR (%)",
            "Расход (руб.)",
            "CPC (руб.)",
            "Добавлений в корзину",
            "CR в корзину (%)",
            "Заказов",
            "CR в заказ (%)",
            "CPO / Стоимость заказа (руб.)",
            "Выручка (руб.)",
            "ДРР (%)",
            "Целевой ДРР (%)",
            "ROAS",
            "Статус эффективности",
        ])

        for row in campaigns_table:
            m = row["metrics"]
            writer.writerow([
                row["id"],
                row["name"],
                row["cabinet"],
                row["status"],
                m["impressions"],
                m["clicks"],
                m["ctr"],
                m["cost"],
                m["cpc"],
                m["cart_additions"],
                m["cr_cart"],
                m["orders"],
                m["cr_order"],
                m["cpo"],
                m["revenue"],
                m["drr"],
                row["target_drr"],
                m["roas"],
                row["status_text"],
            ])

        return response


class APIDashboardDataView(LoginRequiredMixin, View):
    """
    JSON API эндпоинт для асинхронного обновления данных дашборда через AJAX.
    """
    def get(self, request):
        qs = filter_metrics_queryset(request.GET)
        summary = get_dashboard_summary(qs)
        timeline = get_daily_timeline_data(qs)
        cabinet_breakdown = get_platform_breakdown(qs)

        return JsonResponse({
            "summary": summary,
            "timeline": timeline,
            "platform_breakdown": cabinet_breakdown,
            "cabinet_breakdown": cabinet_breakdown,
        })
