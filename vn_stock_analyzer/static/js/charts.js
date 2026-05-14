/**
 * charts.js — All Chart.js rendering functions.
 *
 * Color spec follows README.md exactly.
 * All charts are destroyed before re-creating (prevents canvas reuse errors).
 */

'use strict';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CHART_COLORS = {
  close:   '#0d6efd',
  ma20:    '#ffc107',
  ma50:    '#fd7e14',
  ma200:   '#dc3545',
  bbUpper: '#6f42c1',
  bbLower: '#6f42c1',
  macd:    '#0d6efd',
  signal:  '#dc3545',
  hist:    '#198754',
  volume:  'rgba(13,110,253,0.35)',
};

// Up to 5 tickers in comparison
const TICKER_COLORS = [
  { border: '#0d6efd', bg: 'rgba(13,110,253,0.12)'  },
  { border: '#dc3545', bg: 'rgba(220,53,69,0.12)'   },
  { border: '#198754', bg: 'rgba(25,135,84,0.12)'   },
  { border: '#fd7e14', bg: 'rgba(253,126,20,0.12)'  },
  { border: '#6f42c1', bg: 'rgba(111,66,193,0.12)'  },
];

const BASE_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
    tooltip: {
      callbacks: {
        label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString('vi-VN')}`,
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { maxTicksLimit: 8, font: { size: 10 } },
    },
    y: {
      grid: { color: '#f0f2f7' },
      ticks: {
        font: { size: 10 },
        callback: (v) => v.toLocaleString('vi-VN'),
      },
    },
  },
};

// Registry: canvasId → Chart instance (for cleanup)
const _charts = {};

function _destroy(id) {
  if (_charts[id]) { _charts[id].destroy(); delete _charts[id]; }
}

// Thin date labels (only show every Nth label)
function _thinLabels(labels, max = 8) {
  const step = Math.ceil(labels.length / max);
  return labels.map((l, i) => (i % step === 0 ? l : ''));
}

// ---------------------------------------------------------------------------
// 1. Price chart (Tổng quan) — close price only
// ---------------------------------------------------------------------------

function drawPriceChart(canvasId, records) {
  _destroy(canvasId);
  const labels = records.map(r => r.date);
  const closes = records.map(r => r.close);

  const ctx = document.getElementById(canvasId).getContext('2d');
  _charts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Giá đóng cửa (nghìn ₫)',
        data: closes,
        borderColor: CHART_COLORS.close,
        backgroundColor: 'rgba(13,110,253,0.06)',
        borderWidth: 1.8,
        pointRadius: 0,
        fill: true,
        tension: 0.3,
      }],
    },
    options: {
      ...BASE_OPTIONS,
      plugins: {
        ...BASE_OPTIONS.plugins,
        tooltip: {
          callbacks: {
            label: (ctx) => ` Giá: ${ctx.parsed.y.toLocaleString('vi-VN')} nghìn ₫`,
          },
        },
      },
    },
  });
}

// ---------------------------------------------------------------------------
// 2. Volume chart (Tổng quan)
// ---------------------------------------------------------------------------

function drawVolumeChart(canvasId, records) {
  _destroy(canvasId);
  const labels = records.map(r => r.date);
  const vols   = records.map(r => r.volume);

  const ctx = document.getElementById(canvasId).getContext('2d');
  _charts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Khối lượng',
        data: vols,
        backgroundColor: CHART_COLORS.volume,
        borderWidth: 0,
        borderRadius: 1,
      }],
    },
    options: {
      ...BASE_OPTIONS,
      plugins: {
        ...BASE_OPTIONS.plugins,
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` KL: ${ctx.parsed.y.toLocaleString('vi-VN')}`,
          },
        },
      },
    },
  });
}

// ---------------------------------------------------------------------------
// 3. MA chart (Kỹ thuật) — close + MA20 + MA50 + MA200
// ---------------------------------------------------------------------------

function drawMaChart(canvasId, records, kyThuat) {
  _destroy(canvasId);
  const labels = records.map(r => r.date);
  const closes = records.map(r => r.close);
  const n = closes.length;

  // Build rolling MA arrays from price history
  function rollingMA(arr, period) {
    return arr.map((_, i) => {
      if (i < period - 1) return null;
      const slice = arr.slice(i - period + 1, i + 1);
      return slice.reduce((a, b) => a + b, 0) / period;
    });
  }

  const ma20  = rollingMA(closes, 20);
  const ma50  = rollingMA(closes, 50);
  const ma200 = rollingMA(closes, 200);

  // Bollinger bands (upper/lower) from kyThuat latest values — draw as horizontal reference if needed
  const ctx = document.getElementById(canvasId).getContext('2d');
  _charts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Giá đóng cửa',
          data: closes,
          borderColor: CHART_COLORS.close,
          borderWidth: 1.8,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          order: 1,
        },
        {
          label: 'MA20',
          data: ma20,
          borderColor: CHART_COLORS.ma20,
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          borderDash: [],
          order: 2,
        },
        {
          label: 'MA50',
          data: ma50,
          borderColor: CHART_COLORS.ma50,
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          order: 3,
        },
        {
          label: 'MA200',
          data: ma200,
          borderColor: CHART_COLORS.ma200,
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          borderDash: [4, 3],
          order: 4,
        },
      ],
    },
    options: {
      ...BASE_OPTIONS,
      plugins: {
        ...BASE_OPTIONS.plugins,
        tooltip: {
          callbacks: {
            label: (ctx) => {
              if (ctx.parsed.y === null) return null;
              return ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}`;
            },
          },
        },
      },
    },
  });
}

// ---------------------------------------------------------------------------
// 4. RSI chart (Kỹ thuật) — simulated from price rolling std
//    We only have a single RSI value from the API; chart shows a flat reference.
//    In a real integration, module2 would return the full RSI series.
// ---------------------------------------------------------------------------

function drawRsiChart(canvasId, records, rsiValue) {
  _destroy(canvasId);

  // Simulate RSI series from returns (rough approximation for demo)
  const closes = records.map(r => r.close);
  const rsiSeries = _simulateRsi(closes, 14);
  const labels = records.slice(14).map(r => r.date);

  const ctx = document.getElementById(canvasId).getContext('2d');
  _charts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'RSI (14)',
          data: rsiSeries,
          borderColor: '#6f42c1',
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.3,
        },
        {
          label: 'Quá mua (70)',
          data: labels.map(() => 70),
          borderColor: CHART_COLORS.ma200,
          borderWidth: 1,
          borderDash: [5, 3],
          pointRadius: 0,
          fill: false,
        },
        {
          label: 'Quá bán (30)',
          data: labels.map(() => 30),
          borderColor: CHART_COLORS.hist,
          borderWidth: 1,
          borderDash: [5, 3],
          pointRadius: 0,
          fill: false,
        },
      ],
    },
    options: {
      ...BASE_OPTIONS,
      plugins: {
        ...BASE_OPTIONS.plugins,
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}`,
          },
        },
      },
      scales: {
        ...BASE_OPTIONS.scales,
        y: { ...BASE_OPTIONS.scales.y, min: 0, max: 100, ticks: { callback: v => v } },
      },
    },
  });
}

// Simple RSI simulation from price series
function _simulateRsi(closes, period = 14) {
  const rsi = [];
  for (let i = period; i < closes.length; i++) {
    let gains = 0, losses = 0;
    for (let j = i - period + 1; j <= i; j++) {
      const diff = closes[j] - closes[j - 1];
      if (diff > 0) gains += diff;
      else losses -= diff;
    }
    const rs = losses === 0 ? 100 : gains / losses;
    rsi.push(Math.round((100 - 100 / (1 + rs)) * 10) / 10);
  }
  return rsi;
}

// ---------------------------------------------------------------------------
// 5. MACD chart (Kỹ thuật)
// ---------------------------------------------------------------------------

function drawMacdChart(canvasId, records) {
  _destroy(canvasId);
  const closes = records.map(r => r.close);
  const { macdLine, signalLine, histogram, labels } = _computeMacd(closes, records);

  const ctx = document.getElementById(canvasId).getContext('2d');
  _charts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          type: 'bar',
          label: 'Histogram',
          data: histogram,
          backgroundColor: histogram.map(v => v >= 0
            ? 'rgba(25,135,84,0.6)'
            : 'rgba(220,53,69,0.6)'),
          borderWidth: 0,
          borderRadius: 1,
          order: 3,
        },
        {
          type: 'line',
          label: 'MACD',
          data: macdLine,
          borderColor: CHART_COLORS.macd,
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.3,
          order: 1,
        },
        {
          type: 'line',
          label: 'Signal',
          data: signalLine,
          borderColor: CHART_COLORS.signal,
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.3,
          order: 2,
        },
      ],
    },
    options: {
      ...BASE_OPTIONS,
      plugins: {
        ...BASE_OPTIONS.plugins,
        tooltip: {
          callbacks: {
            label: (ctx) => {
              if (ctx.parsed.y === null) return null;
              return ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(4)}`;
            },
          },
        },
      },
      scales: {
        ...BASE_OPTIONS.scales,
        y: { ...BASE_OPTIONS.scales.y, ticks: { callback: v => v.toFixed(2) } },
      },
    },
  });
}

// Compute EMA, MACD, Signal, Histogram from price array
function _ema(arr, period) {
  const k = 2 / (period + 1);
  const result = [];
  let prev = null;
  for (const v of arr) {
    if (prev === null) { prev = v; result.push(v); continue; }
    prev = v * k + prev * (1 - k);
    result.push(prev);
  }
  return result;
}

function _computeMacd(closes, records, fast = 12, slow = 26, sig = 9) {
  const ema12 = _ema(closes, fast);
  const ema26 = _ema(closes, slow);
  const macdFull = ema12.map((v, i) => v - ema26[i]);
  const signalFull = _ema(macdFull, sig);
  const histFull = macdFull.map((v, i) => v - signalFull[i]);

  const start = slow + sig - 2;
  return {
    labels:     records.slice(start).map(r => r.date),
    macdLine:   macdFull.slice(start),
    signalLine: signalFull.slice(start),
    histogram:  histFull.slice(start),
  };
}

// ---------------------------------------------------------------------------
// 6. Comparison chart — normalized % change from first value
// ---------------------------------------------------------------------------

function drawCompareChart(canvasId, giaData) {
  _destroy(canvasId);
  const tickers = Object.keys(giaData);
  if (tickers.length === 0) return;

  // Align all series to same date range (use longest as base)
  const longest = tickers.reduce((a, b) =>
    giaData[a].length >= giaData[b].length ? a : b);
  const labels = giaData[longest].map(r => r.date);

  const datasets = tickers.map((ma, idx) => {
    const records = giaData[ma];
    const base = records[0]?.close || 1;
    const data = records.map(r => +((r.close / base - 1) * 100).toFixed(2));
    const c = TICKER_COLORS[idx % TICKER_COLORS.length];
    return {
      label: ma,
      data,
      borderColor: c.border,
      backgroundColor: c.bg,
      borderWidth: 2,
      pointRadius: 0,
      fill: false,
      tension: 0.3,
    };
  });

  const ctx = document.getElementById(canvasId).getContext('2d');
  _charts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      ...BASE_OPTIONS,
      plugins: {
        ...BASE_OPTIONS.plugins,
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y > 0 ? '+' : ''}${ctx.parsed.y}%`,
          },
        },
      },
      scales: {
        ...BASE_OPTIONS.scales,
        y: {
          ...BASE_OPTIONS.scales.y,
          ticks: { callback: v => (v > 0 ? '+' : '') + v + '%' },
        },
      },
    },
  });
}
