/**
 * dashboard.js
 * Инициализация интерактивных графиков Chart.js для аналитической панели показателей
 * маркетплейсов автозапчастей (ДРР, CPO, Расходы, Выручка, Сравнение Wildberries vs Ozon).
 */

document.addEventListener("DOMContentLoaded", function () {
    // -------------------------------------------------------------
    // 1. График: Динамика ДРР (%) и стоимости заказа CPO (₽) по дням
    // -------------------------------------------------------------
    const drrCtx = document.getElementById("drrTimelineChart");
    if (drrCtx && typeof timelineData !== "undefined" && timelineData.labels.length > 0) {
        new Chart(drrCtx, {
            type: "line",
            data: {
                labels: timelineData.labels,
                datasets: [
                    {
                        label: "ДРР (%)",
                        data: timelineData.drr,
                        borderColor: "#dc3545",
                        backgroundColor: "rgba(220, 53, 69, 0.12)",
                        fill: true,
                        tension: 0.35,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        yAxisID: "yDRR",
                    },
                    {
                        label: "CPO — Стоимость заказа (₽)",
                        data: timelineData.cpo,
                        borderColor: "#0d6efd",
                        backgroundColor: "transparent",
                        borderDash: [4, 4],
                        tension: 0.35,
                        borderWidth: 2,
                        pointRadius: 2,
                        pointHoverRadius: 5,
                        yAxisID: "yCPO",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "index",
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: "top",
                        labels: { boxWidth: 14, font: { size: 12 } },
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || "";
                                if (label) label += ": ";
                                if (context.datasetIndex === 0) {
                                    label += context.parsed.y + "%";
                                } else {
                                    label += context.parsed.y + " ₽";
                                }
                                return label;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } },
                    },
                    yDRR: {
                        type: "linear",
                        display: true,
                        position: "left",
                        title: { display: true, text: "ДРР (%)", font: { size: 12 } },
                        suggestedMin: 0,
                        suggestedMax: 25,
                    },
                    yCPO: {
                        type: "linear",
                        display: true,
                        position: "right",
                        title: { display: true, text: "CPO (₽)", font: { size: 12 } },
                        grid: { drawOnChartArea: false },
                    },
                },
            },
        });
    }

    // -------------------------------------------------------------
    // 2. График: Выручка по рекламным кабинетам (WB РФ vs WB РБ)
    // -------------------------------------------------------------
    const platformCtx = document.getElementById("platformPieChart");
    if (platformCtx && typeof platformData !== "undefined" && platformData.labels.length > 0) {
        new Chart(platformCtx, {
            type: "doughnut",
            data: {
                labels: platformData.labels,
                datasets: [
                    {
                        data: platformData.revenues,
                        backgroundColor: [
                            "#cb11ab", // Фирменный пурпурный WB РФ
                            "#7b1fa2", // Фирменный глубокий фиолетовый WB РБ
                        ],
                        borderWidth: 2,
                        hoverOffset: 6,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { boxWidth: 12, font: { size: 11 } },
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const val = context.raw || 0;
                                return ` ${context.label}: ${val.toLocaleString("ru-RU")} ₽`;
                            },
                        },
                    },
                },
                cutout: "60%",
            },
        });
    }

    // -------------------------------------------------------------
    // 3. График: Соотношение Расхода и Выручки по дням
    // -------------------------------------------------------------
    const revCostCtx = document.getElementById("revenueCostChart");
    if (revCostCtx && typeof timelineData !== "undefined" && timelineData.labels.length > 0) {
        new Chart(revCostCtx, {
            type: "bar",
            data: {
                labels: timelineData.labels,
                datasets: [
                    {
                        label: "Выручка (₽)",
                        data: timelineData.revenues,
                        backgroundColor: "rgba(25, 135, 84, 0.7)",
                        borderRadius: 4,
                        order: 2,
                    },
                    {
                        label: "Расход (₽)",
                        data: timelineData.costs,
                        backgroundColor: "rgba(220, 53, 69, 0.7)",
                        borderRadius: 4,
                        order: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: { position: "top", labels: { boxWidth: 12 } },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ` ${ctx.dataset.label}: ${ctx.raw.toLocaleString("ru-RU")} ₽`;
                            },
                        },
                    },
                },
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        ticks: {
                            callback: function (value) {
                                return value >= 1000 ? value / 1000 + "k ₽" : value + " ₽";
                            },
                        },
                    },
                },
            },
        });
    }
});
