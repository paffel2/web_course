"""
Management-команда Django для генерации реалистичных данных аналитики
по рекламным кампаниям интернет-магазина автозапчастей в кабинетах WB РФ и WB РБ.
"""

import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from analytics.models import Cabinet, Campaign, DailyCampaignMetric


class Command(BaseCommand):
    help = "Наполняет базу данных реалистичными данными аналитики рекламных кабинетов WB РФ и WB РБ"

    def handle(self, *args, **options):
        self.stdout.write("Создание тестовых учетных записей...")

        # 1. Создание суперпользователя и маркетолога
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@admin.com", "admin")
            self.stdout.write(self.style.SUCCESS("Создан администратор: admin / admin"))

        if not User.objects.filter(username="marketer").exists():
            marketer = User.objects.create_user("marketer", "marketer@autoparts.ru", "marketer123")
            marketer.is_staff = True
            marketer.save()
            self.stdout.write(self.style.SUCCESS("Создан маркетолог: marketer / marketer123"))

        # 2. Создание ровно двух рекламных кабинетов: WB РФ и WB РБ
        self.stdout.write("Создание рекламных кабинетов: WB РФ и WB РБ...")
        cabinets_data = [
            (
                "WB РФ",
                "wb_rf",
                "Рекламный кабинет маркетплейса Wildberries (Российская Федерация)"
            ),
            (
                "WB РБ",
                "wb_rb",
                "Рекламный кабинет маркетплейса Wildberries (Республика Беларусь)"
            ),
        ]

        cabinet_objs = {}
        for name, code, desc in cabinets_data:
            # Ищем по коду или по старому коду, если база уже была создана
            old_code = "wb_ads_ru" if code == "wb_rf" else "wb_ads_by"
            obj = Cabinet.objects.filter(code__in=[code, old_code]).first()
            if obj:
                obj.name = name
                obj.code = code
                obj.description = desc
                obj.is_active = True
                obj.save()
            else:
                obj = Cabinet.objects.create(
                    name=name,
                    code=code,
                    description=desc,
                    is_active=True
                )
            cabinet_objs[code] = obj

        # 3. Создание рекламных кампаний автозапчастей по кабинетам WB РФ и WB РБ
        self.stdout.write("Создание рекламных кампаний автозапчастей...")
        today = date.today()
        start_date = today - timedelta(days=60)

        campaigns_data = [
            {
                "name": "WB_РФ_Поиск_Тормозные_Колодки_Brembo",
                "cabinet": cabinet_objs["wb_rf"],
                "target_drr": Decimal("13.00"),
                "budget": Decimal("4500.00"),
                "status": "active",
                "avg_aov": 7800,
                "base_cpc": 28.0,
                "base_cr_cart": 0.16,
                "base_cr_order": 0.48,
            },
            {
                "name": "WB_РБ_Поиск_Моторные_Масла_Синтетика",
                "cabinet": cabinet_objs["wb_rb"],
                "target_drr": Decimal("10.00"),
                "budget": Decimal("6000.00"),
                "status": "active",
                "avg_aov": 5200,
                "base_cpc": 16.5,
                "base_cr_cart": 0.20,
                "base_cr_order": 0.52,
            },
            {
                "name": "WB_РФ_Каталог_Амортизаторы_KYB_Sachs",
                "cabinet": cabinet_objs["wb_rf"],
                "target_drr": Decimal("16.00"),
                "budget": Decimal("7500.00"),
                "status": "active",
                "avg_aov": 16500,
                "base_cpc": 42.0,
                "base_cr_cart": 0.12,
                "base_cr_order": 0.40,
            },
            {
                "name": "WB_РБ_Каталог_Фильтры_ТО_MANN_Filtron",
                "cabinet": cabinet_objs["wb_rb"],
                "target_drr": Decimal("11.00"),
                "budget": Decimal("3500.00"),
                "status": "active",
                "avg_aov": 3600,
                "base_cpc": 13.5,
                "base_cr_cart": 0.17,
                "base_cr_order": 0.45,
            },
            {
                "name": "WB_РФ_Автосвет_LED_Лампы_и_Фары",
                "cabinet": cabinet_objs["wb_rf"],
                "target_drr": Decimal("17.00"),
                "budget": Decimal("4800.00"),
                "status": "active",
                "avg_aov": 11400,
                "base_cpc": 24.0,
                "base_cr_cart": 0.15,
                "base_cr_order": 0.44,
            },
            {
                "name": "WB_РБ_Поиск_Свечи_Зажигания_NGK",
                "cabinet": cabinet_objs["wb_rb"],
                "target_drr": Decimal("14.00"),
                "budget": Decimal("2800.00"),
                "status": "active",
                "avg_aov": 4500,
                "base_cpc": 19.0,
                "base_cr_cart": 0.14,
                "base_cr_order": 0.38,
            },
        ]

        # 4. Генерация суточных данных за 60 дней
        self.stdout.write("Генерация ежедневных аналитических показателей за 60 дней...")
        random.seed(42)

        total_metrics_count = 0
        for cdata in campaigns_data:
            camp, _ = Campaign.objects.get_or_create(
                name=cdata["name"],
                defaults={
                    "cabinet": cdata["cabinet"],
                    "target_drr": cdata["target_drr"],
                    "daily_budget": cdata["budget"],
                    "status": cdata["status"],
                    "start_date": start_date,
                }
            )

            # Если кампания уже существовала, убеждаемся что привязан актуальный кабинет
            if camp.cabinet != cdata["cabinet"]:
                camp.cabinet = cdata["cabinet"]
                camp.save()

            for day_idx in range(61):
                cur_date = start_date + timedelta(days=day_idx)
                day_factor = 1.25 if cur_date.weekday() in (5, 6) else 1.0
                rand_factor = random.uniform(0.85, 1.18)

                impressions = int(random.randint(3000, 11000) * day_factor * rand_factor)
                ctr = random.uniform(0.030, 0.062)
                clicks = max(10, int(impressions * ctr))

                cpc = cdata["base_cpc"] * random.uniform(0.92, 1.10)
                cost = Decimal(round(clicks * cpc, 2))

                cr_cart = cdata["base_cr_cart"] * random.uniform(0.85, 1.15)
                cart_additions = max(2, int(clicks * cr_cart))

                cr_order = cdata["base_cr_order"] * random.uniform(0.82, 1.18)
                orders_count = max(1, int(cart_additions * cr_order))

                total_rev = Decimal("0.00")
                for _ in range(orders_count):
                    single_order = cdata["avg_aov"] * random.uniform(0.75, 1.35)
                    total_rev += Decimal(round(single_order, 2))

                DailyCampaignMetric.objects.update_or_create(
                    campaign=camp,
                    date=cur_date,
                    defaults={
                        "impressions": impressions,
                        "clicks": clicks,
                        "cost": cost,
                        "cart_additions": cart_additions,
                        "orders_count": orders_count,
                        "revenue": total_rev,
                    }
                )
                total_metrics_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Успешно создано {len(campaigns_data)} кампаний и {total_metrics_count} суточных записей аналитики (кабинеты WB РФ и WB РБ)!"
        ))
