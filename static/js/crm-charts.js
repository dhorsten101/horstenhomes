(() => {
  "use strict";

  function theme() {
    const rootStyles = getComputedStyle(document.documentElement);
    const cssColor = (name, fallback) => (rootStyles.getPropertyValue(name).trim() || fallback);
    return {
      primary: cssColor("--bs-primary", "#4963e6"),
      danger: cssColor("--bs-danger", "#ff5ac8"),
      secondary: cssColor("--bs-secondary", "#45cbb7"),
      warning: cssColor("--bs-warning", "#f5b942"),
      muted: cssColor("--bs-secondary-color", "#6c757d"),
      grid: "rgba(117, 115, 115, 0.16)",
    };
  }

  const fmt = new Intl.NumberFormat(undefined, { style: "currency", currency: "ZAR", maximumFractionDigits: 0 });

  function fmtShort(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return "";
    const abs = Math.abs(n);
    if (abs >= 1_000_000) return `R ${(n / 1_000_000).toFixed(1)} mil`;
    if (abs >= 1_000) return `R ${(n / 1_000).toFixed(1)}k`.replace(".0k", "k");
    return fmt.format(n);
  }

  function isDailyLabels(labels) {
    return labels.length > 0 && /^\d{4}-\d{2}-\d{2}$/.test(String(labels[0]));
  }

  function formatAxisLabel(label, daily) {
    if (!daily) return label;
    const d = new Date(`${label}T00:00:00`);
    if (Number.isNaN(d.getTime())) return label;
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  function isDashboardChart(canvas) {
    return Boolean(canvas && canvas.closest(".crm-dashboard"));
  }

  function barDatasetOptions(colors, dashboard) {
    return {
      backgroundColor: `${colors.secondary}40`,
      hoverBackgroundColor: `${colors.secondary}66`,
      borderColor: colors.secondary,
      borderWidth: 1.5,
      borderRadius: dashboard ? 6 : 8,
      borderSkipped: false,
      maxBarThickness: dashboard ? 52 : 28,
      categoryPercentage: dashboard ? 0.72 : 0.8,
      barPercentage: dashboard ? 0.88 : 0.9,
    };
  }

  function baseScales(colors, daily, labels, dashboard) {
    return {
      x: {
        grid: { display: false },
        border: { display: false },
        ticks: {
          color: colors.muted,
          font: { size: daily ? 11 : 12, weight: "500", family: "system-ui, sans-serif" },
          maxRotation: daily ? 45 : 0,
          minRotation: 0,
          autoSkip: true,
          maxTicksLimit: dashboard ? 8 : (daily ? 10 : 12),
          callback(_val, index) {
            const raw = labels[index];
            return formatAxisLabel(String(raw ?? ""), daily);
          },
        },
      },
      y: {
        beginAtZero: true,
        grace: "5%",
        grid: { color: colors.grid, drawBorder: false },
        border: { display: false },
        ticks: {
          color: colors.muted,
          font: { size: 11, family: "system-ui, sans-serif" },
          padding: 10,
          maxTicksLimit: 5,
          callback: (value) => fmtShort(Number(value)),
        },
      },
    };
  }

  function baseTooltip() {
    return {
      backgroundColor: "rgba(8, 16, 31, 0.94)",
      titleColor: "#fff",
      bodyColor: "rgba(255, 255, 255, 0.92)",
      padding: 14,
      cornerRadius: 10,
      boxWidth: 10,
      boxHeight: 10,
      boxPadding: 4,
    };
  }

  function isYearlyLabels(labels) {
    return labels.length > 0 && /^\d{4}$/.test(String(labels[0]));
  }

  const PREDICTION_YEARS = 15;

  function linearProject(values, yearsAhead) {
    const n = values.length;
    if (n === 0) return Array.from({ length: yearsAhead }, () => 0);
    if (n === 1) {
      const last = values[0];
      return Array.from({ length: yearsAhead }, () => last);
    }

    let sumX = 0;
    let sumY = 0;
    let sumXY = 0;
    let sumXX = 0;
    for (let i = 0; i < n; i += 1) {
      sumX += i;
      sumY += values[i];
      sumXY += i * values[i];
      sumXX += i * i;
    }
    const denom = n * sumXX - sumX * sumX;
    const slope = denom === 0 ? 0 : (n * sumXY - sumX * sumY) / denom;
    const intercept = (sumY - slope * sumX) / n;

    return Array.from({ length: yearsAhead }, (_, idx) => intercept + slope * (n - 1 + idx + 1));
  }

  function buildYearlyProjection(payload, yearsAhead = PREDICTION_YEARS) {
    const labels = payload.labels || [];
    const lastYear = parseInt(String(labels[labels.length - 1]), 10);
    if (!Number.isFinite(lastYear)) return null;

    const inv = [...(payload.invoices || []), ...linearProject(payload.invoices || [], yearsAhead)];
    const exp = [...(payload.expenses || []), ...linearProject(payload.expenses || [], yearsAhead)];
    const futureLabels = Array.from({ length: yearsAhead }, (_, idx) => String(lastYear + idx + 1));

    return {
      labels: [...labels, ...futureLabels],
      invoices: inv,
      expenses: exp,
      profit: inv.map((value, idx) => value - exp[idx]),
      historicalLength: labels.length,
    };
  }

  function cumulativeDataset(label, data, colors, colorKey, historicalLength, predict) {
    const color = colors[colorKey];
    const isProfit = colorKey === "primary";
    return {
      label,
      data,
      borderColor: color,
      backgroundColor: `${color}${isProfit ? "20" : "12"}`,
      borderWidth: isProfit ? 3 : 2.5,
      pointRadius: 0,
      pointHoverRadius: 5,
      pointBackgroundColor: color,
      tension: 0.35,
      fill: isProfit,
      segment: predict
        ? {
            borderDash: (ctx) => (ctx.p0DataIndex >= historicalLength - 1 ? [6, 4] : undefined),
          }
        : undefined,
    };
  }

  function renderCumulativeChart(canvas, payload, options = {}) {
    if (!canvas || typeof Chart === "undefined") return null;
    const baseLabels = payload.labels || [];
    const predict = Boolean(options.predict) && isYearlyLabels(baseLabels);
    const chartPayload = predict ? buildYearlyProjection(payload) : payload;
    if (!chartPayload) return null;

    const labels = chartPayload.labels || [];
    const inv = chartPayload.invoices || [];
    const exp = chartPayload.expenses || [];
    const profit = chartPayload.profit || inv.map((v, i) => v - (exp[i] || 0));
    if (!labels.length) return null;

    const colors = theme();
    const daily = isDailyLabels(labels);
    const dashboard = isDashboardChart(canvas);
    const historicalLength = predict ? chartPayload.historicalLength : labels.length;

    return new Chart(canvas.getContext("2d"), {
      type: "line",
      data: {
        labels,
        datasets: [
          cumulativeDataset("Money in", inv, colors, "secondary", historicalLength, predict),
          cumulativeDataset("Money out", exp, colors, "danger", historicalLength, predict),
          cumulativeDataset("Profit", profit, colors, "primary", historicalLength, predict),
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: 8, right: 8, bottom: 0, left: 4 } },
        interaction: { mode: "index", intersect: false },
        animation: { duration: 500, easing: "easeOutQuart" },
        plugins: {
          legend: { display: false },
          tooltip: {
            ...baseTooltip(),
            callbacks: {
              title: (items) => {
                if (!items[0]) return "";
                const title = formatAxisLabel(items[0].label, daily);
                if (predict && items[0].dataIndex >= historicalLength) {
                  return `${title} (projected)`;
                }
                return title;
              },
              label: (ctx) => {
                const v = ctx.parsed.y;
                const n = typeof v === "number" && !Number.isNaN(v) ? v : 0;
                const suffix = predict && ctx.dataIndex >= historicalLength ? " (projected)" : "";
                return `${ctx.dataset.label}: ${fmt.format(n)}${suffix}`;
              },
            },
          },
        },
        scales: baseScales(colors, daily, labels, dashboard),
      },
    });
  }

  function renderMonthlyBarChart(canvas, payload) {
    if (!canvas || typeof Chart === "undefined") return null;
    const labels = payload.labels || [];
    const inv = payload.invoices || [];
    const exp = payload.expenses || [];
    const net = payload.net || inv.map((v, i) => v - (exp[i] || 0));
    if (!labels.length) return null;

    const colors = theme();
    const profitPoints = net.map((v) => (v >= 0 ? colors.primary : colors.warning));
    const dashboard = isDashboardChart(canvas);
    const inBar = barDatasetOptions(colors, dashboard);

    return new Chart(canvas.getContext("2d"), {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            type: "bar",
            label: "Money in",
            data: inv,
            ...inBar,
            order: 2,
          },
          {
            type: "bar",
            label: "Money out",
            data: exp,
            ...inBar,
            backgroundColor: `${colors.danger}36`,
            hoverBackgroundColor: `${colors.danger}59`,
            borderColor: colors.danger,
            order: 3,
          },
          {
            type: "line",
            label: "Profit kept",
            data: net,
            borderColor: colors.primary,
            backgroundColor: `${colors.primary}18`,
            pointBackgroundColor: profitPoints,
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
            pointRadius: dashboard ? 5 : 4,
            pointHoverRadius: dashboard ? 7 : 6,
            borderWidth: dashboard ? 3 : 2.5,
            tension: 0.35,
            fill: false,
            order: 1,
            segment: {
              borderColor: (ctx) => {
                const v = net[ctx.p1DataIndex];
                return typeof v === "number" && v < 0 ? colors.warning : colors.primary;
              },
            },
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: 12, right: 8, bottom: 0, left: 4 } },
        interaction: { mode: "index", intersect: false },
        animation: { duration: 500, easing: "easeOutQuart" },
        plugins: {
          legend: { display: false },
          tooltip: {
            ...baseTooltip(),
            callbacks: {
              title: (items) => (items[0] ? items[0].label : ""),
              label: (ctx) => {
                const v = ctx.parsed.y;
                const n = typeof v === "number" && !Number.isNaN(v) ? v : 0;
                return `${ctx.dataset.label}: ${fmt.format(n)}`;
              },
            },
          },
        },
        scales: baseScales(colors, false, labels, dashboard),
      },
    });
  }

  function initFromJson(dataId, canvasId, renderer) {
    const dataEl = document.getElementById(dataId);
    const canvas = document.getElementById(canvasId);
    if (!dataEl || !canvas) return null;
    let payload;
    try {
      payload = JSON.parse(dataEl.textContent || "{}");
    } catch (e) {
      return null;
    }

    let chart = renderer(canvas, payload, { predict: false });
    const toggle = document.getElementById(`${canvasId}-predict`);
    if (!toggle || !chart) return chart;

    toggle.addEventListener("change", () => {
      if (chart) chart.destroy();
      chart = renderer(canvas, payload, { predict: toggle.checked });
    });
    return chart;
  }

  window.CrmCharts = {
    renderCumulativeChart,
    renderMonthlyBarChart,
    initCumulativeFromJson: (dataId, canvasId) => initFromJson(dataId, canvasId, renderCumulativeChart),
    initMonthlyBarFromJson: (dataId, canvasId) => initFromJson(dataId, canvasId, renderMonthlyBarChart),
  };
})();
