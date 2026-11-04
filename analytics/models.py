"""
Модуль моделей базы данных приложения аналитики рекламных кампаний.
Предметная область: интернет-магазин автозапчастей на маркетплейсах.
Реализует учет эффективности рекламных кампаний в кабинетах (Cabinet).
"""

from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class Cabinet(models.Model):
    """
    Рекламный кабинет маркетплейса (канал привлечения покупателей).
    Примеры: Wildberries Россия, Wildberries Беларусь (или кабинеты Ozon).
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Рекламный кабинет",
        help_text="Например: Wildberries Россия, Ozon Performance"
    )
    code = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name="Символьный код",
        help_text="Идентификатор кабинета (wb_ads_ru, wb_ads_by, ozon_ads)"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание кабинета"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )

    class Meta:
        verbose_name = "Рекламный кабинет"
        verbose_name_plural = "Рекламные кабинеты"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Campaign(models.Model):
    """
    Рекламная кампания интернет-магазина автозапчастей.
    Связывает рекламный кабинет, плановый целевой ДРР и бюджет.
    """
    STATUS_CHOICES = [
        ("active", "Активна"),
        ("paused", "Приостановлена"),
        ("completed", "Завершена"),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name="Название рекламной кампании",
        help_text="Например: WB_Поиск_Тормозные_Колодки, Ozon_Трафареты_Масла"
    )
    cabinet = models.ForeignKey(
        Cabinet,
        on_delete=models.CASCADE,
        related_name="campaigns",
        verbose_name="Рекламный кабинет"
    )
    target_drr = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("15.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Целевой ДРР (%)",
        help_text="Плановый допустимый порог доли рекламных расходов для кампании, %"
    )
    daily_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Дневной бюджет (руб.)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        verbose_name="Статус кампании"
    )
    start_date = models.DateField(
        verbose_name="Дата запуска"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата завершения"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания записи"
    )

    class Meta:
        verbose_name = "Рекламная кампания"
        verbose_name_plural = "Рекламные кампании"
        ordering = ["-start_date", "name"]

    def __str__(self):
        return f"{self.name} [{self.cabinet.name}]"


class DailyCampaignMetric(models.Model):
    """
    Ежедневные агрегированные показатели эффективности рекламной кампании.
    Хранит исходные данные для расчета ключевых аналитических метрик:
    - показы, клики (переходы в карточку товара), затраты на рекламу;
    - добавления автозапчастей в корзину, оформленные заказы, выручка.
    """
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="metrics",
        verbose_name="Рекламная кампания"
    )
    date = models.DateField(
        verbose_name="Дата отчета"
    )
    impressions = models.PositiveIntegerField(
        default=0,
        verbose_name="Показы объявлений"
    )
    clicks = models.PositiveIntegerField(
        default=0,
        verbose_name="Число кликов (переходов)"
    )
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Расход на рекламу (руб.)"
    )
    cart_additions = models.PositiveIntegerField(
        default=0,
        verbose_name="Добавлений в корзину"
    )
    orders_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Оформленных заказов"
    )
    revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Выручка от заказов (руб.)"
    )

    class Meta:
        verbose_name = "Суточная метрика кампании"
        verbose_name_plural = "Суточные метрики кампаний"
        ordering = ["-date", "campaign"]
        unique_together = ("campaign", "date")

    def __str__(self):
        return f"{self.campaign.name} @ {self.date} (Заказов: {self.orders_count}, Расход: {self.cost} руб.)"

    # ========================================================
    # РАСЧЕТНЫЕ АНАЛИТИЧЕСКИЕ ПОКАЗАТЕЛИ (БИЗНЕС-ЛОГИКА)
    # ========================================================

    @property
    def ctr(self) -> float:
        """
        CTR (Click-Through Rate) — кликабельность объявлений (%).
        CTR = (Клики / Показы) * 100%
        """
        if self.impressions > 0:
            return round((self.clicks / self.impressions) * 100, 2)
        return 0.0

    @property
    def cpc(self) -> float:
        """
        CPC (Cost Per Click) — средняя стоимость клика/перехода (руб.).
        CPC = Расход / Клики
        """
        if self.clicks > 0:
            return round(float(self.cost) / self.clicks, 2)
        return 0.0

    @property
    def cr_cart(self) -> float:
        """
        CR в корзину — конверсия из перехода в карточку в добавление запчасти в корзину (%).
        CR_cart = (Добавления в корзину / Клики) * 100%
        """
        if self.clicks > 0:
            return round((self.cart_additions / self.clicks) * 100, 2)
        return 0.0

    @property
    def cr_order(self) -> float:
        """
        CR в заказ — конверсия из клика в оформленный заказ автозапчасти (%).
        CR_order = (Заказы / Клики) * 100%
        """
        if self.clicks > 0:
            return round((self.orders_count / self.clicks) * 100, 2)
        return 0.0

    @property
    def cr_cart_to_order(self) -> float:
        """
        Конверсия корзины — процент завершения заказа из добавленных в корзину (%).
        CR_cart_to_order = (Заказы / Добавления в корзину) * 100%
        """
        if self.cart_additions > 0:
            return round((self.orders_count / self.cart_additions) * 100, 2)
        return 0.0

    @property
    def cpo(self) -> float:
        """
        CPO (Cost Per Order) — стоимость привлечения одного заказа автозапчастей (руб.).
        CPO = Расход на рекламу / Число заказов
        """
        if self.orders_count > 0:
            return round(float(self.cost) / self.orders_count, 2)
        return 0.0

    @property
    def drr(self) -> float:
        """
        ДРР (Доля рекламных расходов) — отношение рекламных затрат к полученной выручке (%).
        ДРР = (Расход / Выручка) * 100%
        """
        if self.revenue > 0:
            return round((float(self.cost) / float(self.revenue)) * 100, 2)
        return 0.0

    @property
    def roas(self) -> float:
        """
        ROAS (Return On Ad Spend) — окупаемость расходов на рекламу.
        ROAS = Выручка / Расход
        """
        if self.cost > 0:
            return round(float(self.revenue) / float(self.cost), 2)
        return 0.0

    @property
    def aov(self) -> float:
        """
        AOV (Average Order Value) — средний чек заказа автозапчастей (руб.).
        AOV = Выручка / Заказы
        """
        if self.orders_count > 0:
            return round(float(self.revenue) / self.orders_count, 2)
        return 0.0
