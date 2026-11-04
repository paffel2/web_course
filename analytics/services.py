"""
Сервисный слой аналитики рекламных кампаний автозапчастей.
Содержит бизнес-логику фильтрации, агрегации данных и расчёта
ключевых маркетинговых метрик (ДРР, CPO, CR, CTR, CPC, ROAS).
"""

from typing import Dict, Any, List
from django.db.models import Sum, QuerySet
from .models import DailyCampaignMetric


def calculate_metrics_dict(sums: Dict[str, Any]) -> Dict[str, Any]:
    """
    Расчёт производных аналитических показателей на основе словаря агрегатов.
    """
    impressions = sums.get("total_impressions") or 0
    clicks = sums.get("total_clicks") or 0
    cost = float(sums.get("total_cost") or 0.0)
    cart_additions = sums.get("total_cart_additions") or 0
    orders = sums.get("total_orders") or 0
    revenue = float(sums.get("total_revenue") or 0.0)

    ctr = round((clicks / impressions * 100), 2) if impressions > 0 else 0.0
    cpc = round(cost / clicks, 2) if clicks > 0 else 0.0
    cr_cart = round((cart_additions / clicks * 100), 2) if clicks > 0 else 0.0
    cr_order = round((orders / clicks * 100), 2) if clicks > 0 else 0.0
    cr_cart_to_order = round((orders / cart_additions * 100), 2) if cart_additions > 0 else 0.0
    cpo = round(cost / orders, 2) if orders > 0 else 0.0
    drr = round((cost / revenue * 100), 2) if revenue > 0 else 0.0
    roas = round(revenue / cost, 2) if cost > 0 else 0.0
    aov = round(revenue / orders, 2) if orders > 0 else 0.0
    profit = round(revenue - cost, 2)

    return {
        "impressions": impressions,
        "clicks": clicks,
        "cost": round(cost, 2),
        "cart_additions": cart_additions,
        "orders": orders,
        "revenue": round(revenue, 2),
        "ctr": ctr,
        "cpc": cpc,
        "cr_cart": cr_cart,
        "cr_order": cr_order,
        "cr_cart_to_order": cr_cart_to_order,
        "cpo": cpo,
        "drr": drr,
        "roas": roas,
        "aov": aov,
        "profit": profit,
    }


def filter_metrics_queryset(params: Dict[str, Any]) -> QuerySet:
    """
    Фильтрация записей DailyCampaignMetric по параметрам запроса:
    - date_from, date_to (период дат)
    - cabinet / platform (ID рекламного кабинета)
    - campaign (ID конкретной кампании)
    """
    qs = DailyCampaignMetric.objects.select_related(
        "campaign", "campaign__cabinet"
    )

    date_from = params.get("date_from")
    date_to = params.get("date_to")
    cabinet_id = params.get("cabinet") or params.get("platform")
    campaign_id = params.get("campaign")

    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    if cabinet_id:
        qs = qs.filter(campaign__cabinet_id=cabinet_id)
    if campaign_id:
        qs = qs.filter(campaign_id=campaign_id)

    return qs


def get_dashboard_summary(qs: QuerySet) -> Dict[str, Any]:
    """
    Получение общих агрегированных показателей за выбранный период.
    """
    sums = qs.aggregate(
        total_impressions=Sum("impressions"),
        total_clicks=Sum("clicks"),
        total_cost=Sum("cost"),
        total_cart_additions=Sum("cart_additions"),
        total_orders=Sum("orders_count"),
        total_revenue=Sum("revenue"),
    )
    return calculate_metrics_dict(sums)


def get_daily_timeline_data(qs: QuerySet) -> Dict[str, List[Any]]:
    """
    Формирование временного ряда по дням для построения графиков Chart.js:
    - даты, расходы, выручка, ДРР (%), CPO (руб.), число заказов.
    """
    daily_qs = (
        qs.values("date")
        .annotate(
            day_impressions=Sum("impressions"),
            day_clicks=Sum("clicks"),
            day_cost=Sum("cost"),
            day_cart=Sum("cart_additions"),
            day_orders=Sum("orders_count"),
            day_revenue=Sum("revenue"),
        )
        .order_by("date")
    )

    labels = []
    costs = []
    revenues = []
    drr_values = []
    cpo_values = []
    orders_values = []

    for item in daily_qs:
        d_str = item["date"].strftime("%d.%m")
        labels.append(d_str)

        day_cost = float(item["day_cost"] or 0)
        day_rev = float(item["day_revenue"] or 0)
        day_ord = item["day_orders"] or 0

        costs.append(round(day_cost, 2))
        revenues.append(round(day_rev, 2))
        orders_values.append(day_ord)

        d_drr = round((day_cost / day_rev * 100), 2) if day_rev > 0 else 0.0
        drr_values.append(d_drr)

        d_cpo = round(day_cost / day_ord, 2) if day_ord > 0 else 0.0
        cpo_values.append(d_cpo)

    return {
        "labels": labels,
        "costs": costs,
        "revenues": revenues,
        "drr": drr_values,
        "cpo": cpo_values,
        "orders": orders_values,
    }


def get_platform_breakdown(qs: QuerySet) -> Dict[str, Any]:
    """
    Распределение ключевых показателей по рекламным кабинетам (Cabinet).
    """
    breakdown_qs = (
        qs.values("campaign__cabinet__name")
        .annotate(
            total_impressions=Sum("impressions"),
            total_clicks=Sum("clicks"),
            total_cost=Sum("cost"),
            total_cart_additions=Sum("cart_additions"),
            total_orders=Sum("orders_count"),
            total_revenue=Sum("revenue"),
        )
        .order_by("-total_revenue")
    )

    names = []
    costs = []
    revenues = []
    orders = []
    drrs = []

    for item in breakdown_qs:
        name = item["campaign__cabinet__name"] or "Без кабинета"
        cost = float(item["total_cost"] or 0)
        rev = float(item["total_revenue"] or 0)
        ord_cnt = item["total_orders"] or 0
        drr = round((cost / rev * 100), 2) if rev > 0 else 0.0

        names.append(name)
        costs.append(round(cost, 2))
        revenues.append(round(rev, 2))
        orders.append(ord_cnt)
        drrs.append(drr)

    return {
        "labels": names,
        "costs": costs,
        "revenues": revenues,
        "orders": orders,
        "drrs": drrs,
    }


def get_campaigns_table_data(qs: QuerySet) -> List[Dict[str, Any]]:
    """
    Сводная таблица по каждой рекламной кампании за выбранный период
    с расчетом показателей эффективности и индикатором рентабельности по ее целевому ДРР.
    """
    camp_qs = (
        qs.values(
            "campaign__id",
            "campaign__name",
            "campaign__cabinet__name",
            "campaign__target_drr",
            "campaign__status",
        )
        .annotate(
            total_impressions=Sum("impressions"),
            total_clicks=Sum("clicks"),
            total_cost=Sum("cost"),
            total_cart_additions=Sum("cart_additions"),
            total_orders=Sum("orders_count"),
            total_revenue=Sum("revenue"),
        )
        .order_by("-total_revenue")
    )

    table_rows = []
    for row in camp_qs:
        m = calculate_metrics_dict(row)
        target_drr = float(row["campaign__target_drr"] or 15.0)
        cab_name = row["campaign__cabinet__name"] or "Без кабинета"

        # Оценка эффективности рекламной кампании по ее целевому ДРР
        if m["revenue"] == 0 and m["cost"] > 0:
            status_badge = "critical"
            status_text = "Убыточная (0 выручки)"
        elif m["drr"] <= target_drr:
            status_badge = "success"
            status_text = f"Эффективно (ДРР {m['drr']}% ≤ {target_drr}%)"
        elif m["drr"] <= target_drr * 1.25:
            status_badge = "warning"
            status_text = f"Внимание (ДРР {m['drr']}% > {target_drr}%)"
        else:
            status_badge = "danger"
            status_text = f"Неэффективно (ДРР {m['drr']}% >> {target_drr}%)"

        table_rows.append({
            "id": row["campaign__id"],
            "name": row["campaign__name"],
            "cabinet": cab_name,
            "target_drr": target_drr,
            "status": row["campaign__status"],
            "status_badge": status_badge,
            "status_text": status_text,
            "metrics": m,
        })

    return table_rows


def get_conversion_funnel(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Формирование этапов маркетинговой воронки для автозапчастей:
    Показы объявлений -> Переходы в карточку товара -> Добавления в корзину -> Заказы.
    """
    impressions = summary.get("impressions", 0)
    clicks = summary.get("clicks", 0)
    cart = summary.get("cart_additions", 0)
    orders = summary.get("orders", 0)

    funnel = [
        {
            "stage": "1. Показы рекламы",
            "count": impressions,
            "conv_prev": 100.0,
            "conv_total": 100.0,
            "metric_name": "Охват в поиске/каталоге",
            "badge_color": "bg-primary",
        },
        {
            "stage": "2. Переходы в карточку (Клики)",
            "count": clicks,
            "conv_prev": round((clicks / impressions * 100), 2) if impressions > 0 else 0.0,
            "conv_total": round((clicks / impressions * 100), 2) if impressions > 0 else 0.0,
            "metric_name": "CTR",
            "badge_color": "bg-info",
        },
        {
            "stage": "3. Добавления в корзину",
            "count": cart,
            "conv_prev": round((cart / clicks * 100), 2) if clicks > 0 else 0.0,
            "conv_total": round((cart / impressions * 100), 4) if impressions > 0 else 0.0,
            "metric_name": "CR в корзину",
            "badge_color": "bg-warning text-dark",
        },
        {
            "stage": "4. Оформленные заказы",
            "count": orders,
            "conv_prev": round((orders / cart * 100), 2) if cart > 0 else 0.0,
            "conv_total": round((orders / clicks * 100), 2) if clicks > 0 else 0.0,
            "metric_name": "CR в заказ",
            "badge_color": "bg-success",
        },
    ]
    return funnel
