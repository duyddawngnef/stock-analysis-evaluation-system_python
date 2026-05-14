/**
 * main.js — Page-level initialization logic.
 *
 * Three entry points called from page templates:
 *   initKetQua(ma_cp)  — analysis results page
 *   initSoSanh(preFill) — comparison page
 * (trang_chu.html is self-contained — search handled inline)
 */

'use strict';

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

/** Map signal string → CSS class suffix */
const SIGNAL_CLASS = {
  'MUA MẠNH': 'mua-manh',
  'MUA':       'mua',
  'GIỮ':       'giu',
  'BÁN':       'ban',
};

const SIGNAL_BADGE_CLASS = {
  'MUA MẠNH': 'badge-mua-manh',
  'MUA':       'badge-mua',
  'GIỮ':       'badge-giu',
  'BÁN':       'badge-ban',
};

const RANK_CLASS = { 'TỐT': 'badge-tot', 'KHÁ': 'badge-kha', 'YẾU': 'badge-yeu' };

const SIGNAL_ICON = {
  'MUA MẠNH': 'trending_up',
  'MUA':       'thumb_up',
  'GIỮ':       'pause_circle',
  'BÁN':       'trending_down',
};

/** Format number in vi-VN locale */
function fmtNum(v, digits = 2) {
  if (v == null || isNaN(v)) return '—';
  return (+v).toLocaleString('vi-VN', { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function fmtInt(v) {
  if (v == null) return '—';
  return (+v).toLocaleString('vi-VN');
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function setHTML(id, val) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = val;
}

function hideLoading(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}

// ---------------------------------------------------------------------------
// initKetQua — analysis results page
// ---------------------------------------------------------------------------

async function initKetQua(ma_cp) {
  try {
    // Kick off all API calls in parallel
    const [info, prices, tech, fund] = await Promise.all([
      API.thongTin(ma_cp),
      API.giaLichSu(ma_cp),
      API.kyThuat(ma_cp),
      API.coBan(ma_cp),
    ]);

    _renderHeader(info, tech);
    _renderTongQuan(info, prices);
    _renderKyThuat(prices, tech);
    _renderCoBan(fund);

  } catch (err) {
    console.error('initKetQua error:', err);
    _showPageError(err.error || 'Không tải được dữ liệu cổ phiếu');
  }
}

// --- Header ---

function _renderHeader(info, tech) {
  setText('hdrTicker',  info.ma);
  setText('hdrCompany', info.ten_cong_ty);

  // Meta pills
  const metaEl = document.getElementById('hdrMeta');
  if (metaEl) {
    metaEl.innerHTML = `
      <span class="meta-pill">
        <span class="material-icons">storefront</span>${info.san}
      </span>
      <span class="meta-pill">
        <span class="material-icons">category</span>${info.nganh}
      </span>
    `;
  }

  // Price
  const priceEl = document.getElementById('hdrPrice');
  if (priceEl) priceEl.textContent = fmtNum(info.gia_hien_tai, 1) + ' nghìn';

  // Change
  const changeEl = document.getElementById('hdrChange');
  if (changeEl) {
    const pct = info.thay_doi_phan_tram;
    const sign = pct > 0 ? '+' : '';
    const cls = pct > 0 ? 'positive' : pct < 0 ? 'negative' : 'neutral';
    changeEl.textContent = `${sign}${fmtNum(pct)}%`;
    changeEl.className = `price-change ${cls}`;
  }

  // Signal badge
  const sigEl = document.getElementById('hdrSignal');
  if (sigEl && tech) {
    sigEl.textContent = tech.tin_hieu || '';
    sigEl.className = `badge badge-signal ${SIGNAL_BADGE_CLASS[tech.tin_hieu] || ''}`;
  }

  // Excel export
  const btnExcel = document.getElementById('btnXuatExcel');
  if (btnExcel) {
    btnExcel.addEventListener('click', async () => {
      btnExcel.disabled = true;
      btnExcel.innerHTML = '<span class="material-icons">hourglass_top</span> Đang xuất…';
      try {
        const res = await fetch(`/api/xuat-excel/${info.ma}`);
        if (res.ok) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = `${info.ma}_phan_tich.xlsx`; a.click();
        } else {
          const j = await res.json();
          alert(j.error || 'Xuất Excel thất bại');
        }
      } finally {
        btnExcel.disabled = false;
        btnExcel.innerHTML = '<span class="material-icons">download</span> Xuất Excel';
      }
    });
  }
}

// --- Tab 1: Tổng quan ---

function _renderTongQuan(info, prices) {
  // Metric cards
  const last = prices[prices.length - 1];
  setText('metricGia',   last ? fmtNum(last.close, 1) + ' nghìn ₫' : '—');
  setText('metricNgay',  last ? last.date : '—');
  setText('metricKL',    fmtInt(info.khoi_luong));
  setText('metricVH',    fmtInt(info.von_hoa));
  setText('metricNganh', info.nganh);
  setText('metricSan',   info.san);

  // Charts
  hideLoading('priceChartLoading');
  drawPriceChart('priceChart', prices);
  drawVolumeChart('volumeChart', prices);
}

// --- Tab 2: Kỹ thuật ---

function _renderKyThuat(prices, tech) {
  // Signal panel
  const sigWrap = document.getElementById('signalIconWrap');
  const sigIcon = document.getElementById('signalIcon');
  const sigVal  = document.getElementById('signalValue');
  const sigExp  = document.getElementById('signalExplain');

  const cls = SIGNAL_CLASS[tech.tin_hieu] || 'giu';
  if (sigWrap) sigWrap.className = `signal-icon-wrap ${cls}`;
  if (sigIcon) sigIcon.textContent = SIGNAL_ICON[tech.tin_hieu] || 'help';
  if (sigVal)  sigVal.textContent = tech.tin_hieu || '—';
  if (sigExp)  sigExp.textContent = tech.giai_thich || '';

  // RSI gauge
  const rsiVal = tech.rsi;
  setText('rsiValue', rsiVal != null ? rsiVal.toFixed(1) : '—');
  const needle = document.getElementById('rsiNeedle');
  if (needle && rsiVal != null) {
    needle.style.left = rsiVal + '%';
  }

  // Indicator rows
  const maData = tech.ma || {};
  const lastClose = prices[prices.length - 1]?.close ?? 0;

  const indTable = document.getElementById('indicatorsTable');
  if (indTable) {
    const rows = [
      { name: 'MA20',      color: '#ffc107', val: maData.MA20,  isMa: true },
      { name: 'MA50',      color: '#fd7e14', val: maData.MA50,  isMa: true },
      { name: 'MA200',     color: '#dc3545', val: maData.MA200, isMa: true },
      { name: 'MACD',      color: '#0d6efd', val: tech.macd?.macd },
      { name: 'Signal',    color: '#dc3545', val: tech.macd?.signal },
      { name: 'Histogram', color: '#198754', val: tech.macd?.histogram },
    ];

    indTable.innerHTML = rows.map(r => {
      let extra = '';
      if (r.isMa && r.val != null) {
        const abv = lastClose > r.val;
        extra = `<span class="ms-2 badge ${abv ? 'badge-mua' : 'badge-ban'}" style="font-size:0.7rem;">
          ${abv ? '↑ Trên' : '↓ Dưới'}</span>`;
      }
      return `
      <div class="indicator-row">
        <span class="indicator-name">
          <span class="dot" style="background:${r.color};"></span>
          ${r.name}
        </span>
        <span class="indicator-value">${r.val != null ? fmtNum(r.val, 4) : '—'}${extra}</span>
      </div>`;
    }).join('');
  }

  // Charts
  hideLoading('maChartLoading');
  drawMaChart('maChart', prices, tech);
  drawRsiChart('rsiChart', prices, tech.rsi);
  drawMacdChart('macdChart', prices);

  // Bollinger
  const bb = tech.bollinger || {};
  setText('bbUpper',  bb.upper  != null ? fmtNum(bb.upper,  2)  : '—');
  setText('bbMiddle', bb.middle != null ? fmtNum(bb.middle, 2)  : '—');
  setText('bbLower',  bb.lower  != null ? fmtNum(bb.lower,  2)  : '—');
}

// --- Tab 3: Cơ bản ---

function _renderCoBan(fund) {
  const chiSo    = fund.chi_so    || {};
  const chamDiem = fund.cham_diem || {};

  // Score bars
  const metricMap = {
    ROE: { format: v => v.toFixed(1) + '%', unit: '%' },
    ROA: { format: v => v.toFixed(1) + '%', unit: '%' },
    EPS: { format: v => fmtInt(v) + ' ₫',  unit: '₫' },
    PE:  { format: v => v.toFixed(1) + 'x', unit: 'x' },
    PB:  { format: v => v.toFixed(2) + 'x', unit: 'x' },
    DE:  { format: v => v.toFixed(2),         unit: '' },
  };

  for (const [key, cfg] of Object.entries(metricMap)) {
    const val   = chiSo[key];
    const score = chamDiem[key];

    setText(`chiSo${key}`, val != null ? cfg.format(val) : '—');
    setText(`pts${key}`,   score != null ? score + '/2' : '—');

    const bar = document.getElementById(`bar${key}`);
    if (bar && score != null) {
      bar.className = `score-bar-fill score-${score}`;
    }
  }

  // Donut & total
  const tong = chamDiem.tong ?? 0;
  const phanLoai = chamDiem.phan_loai || '—';

  setText('scoreTong', tong);
  const arcEl = document.getElementById('scoreDonutArc');
  if (arcEl) {
    const pct = (tong / 12) * 100;
    arcEl.setAttribute('stroke-dasharray', `${pct} ${100 - pct}`);
    const color = phanLoai === 'TỐT' ? '#198754' : phanLoai === 'KHÁ' ? '#fd7e14' : '#dc3545';
    arcEl.setAttribute('stroke', color);
  }

  const plEl = document.getElementById('scorePhanLoai');
  if (plEl) {
    plEl.textContent = phanLoai;
    plEl.className = `badge badge-signal ${RANK_CLASS[phanLoai] || ''}`;
  }
}

// --- Error display ---

function _showPageError(msg) {
  const container = document.querySelector('.container');
  if (!container) return;
  const div = document.createElement('div');
  div.className = 'alert alert-danger mt-3';
  div.innerHTML = `<span class="material-icons">error_outline</span><div>${msg}</div>`;
  container.prepend(div);
}

// ---------------------------------------------------------------------------
// initSoSanh — comparison page
// ---------------------------------------------------------------------------

function initSoSanh(preFill = []) {
  const input    = document.getElementById('tickerInput');
  const tagsWrap = document.getElementById('tickerTags');
  const btnSS    = document.getElementById('btnSoSanh');
  const btnClr   = document.getElementById('btnClear');
  const countEl  = document.getElementById('tagCount');

  let tickers = [];
  const MAX = 5;

  function _addTicker(ma) {
    ma = ma.trim().toUpperCase();
    if (!ma || tickers.includes(ma) || tickers.length >= MAX) return;
    tickers.push(ma);
    _renderTags();
    _updateCount();
  }

  window._addTicker = _addTicker; // expose for group buttons

  function _removeTicker(ma) {
    tickers = tickers.filter(t => t !== ma);
    _renderTags();
    _updateCount();
  }

  function _renderTags() {
    tagsWrap.innerHTML = tickers.map(ma => `
      <span class="ticker-tag" data-ma="${ma}">
        ${ma}
        <button type="button" class="btn-remove" aria-label="Xóa ${ma}"
                onclick="document.dispatchEvent(new CustomEvent('removeTicker', { detail: '${ma}' }))">
          <span class="material-icons">close</span>
        </button>
      </span>
    `).join('');
    btnSS.disabled = tickers.length < 2;
  }

  function _updateCount() {
    countEl.textContent = `${tickers.length} / ${MAX} mã`;
    if (tickers.length >= MAX) {
      input.disabled = true;
      input.placeholder = 'Đã đủ 5 mã';
    } else {
      input.disabled = false;
      input.placeholder = 'Nhập mã…';
    }
  }

  // Events
  document.addEventListener('removeTicker', e => _removeTicker(e.detail));

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      _addTicker(input.value);
      input.value = '';
    }
    // Backspace on empty input removes last tag
    if (e.key === 'Backspace' && input.value === '' && tickers.length > 0) {
      _removeTicker(tickers[tickers.length - 1]);
    }
  });

  input.addEventListener('input', () => {
    input.value = input.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
  });

  input.addEventListener('blur', () => {
    if (input.value.trim()) { _addTicker(input.value); input.value = ''; }
  });

  btnClr.addEventListener('click', () => {
    tickers = [];
    _renderTags();
    _updateCount();
    _hideResults();
  });

  btnSS.addEventListener('click', () => _runCompare());

  // Pre-fill from URL
  preFill.forEach(ma => _addTicker(ma));

  // Auto-run if pre-filled with ≥2 tickers
  if (tickers.length >= 2) _runCompare();

  // --- Run comparison ---
  async function _runCompare() {
    if (tickers.length < 2) return;

    const resultsWrap = document.getElementById('compareResults');
    const loading     = document.getElementById('compareLoading');
    const errEl       = document.getElementById('compareError');
    const chartWrap   = document.getElementById('compareChartWrap');
    const fundWrap    = document.getElementById('compareTableWrap');
    const techWrap    = document.getElementById('compareTechWrap');

    resultsWrap.classList.remove('d-none');
    loading.classList.remove('d-none');
    [chartWrap, fundWrap, techWrap, errEl].forEach(el => el.classList.add('d-none'));

    try {
      const data = await API.soSanh(tickers);
      loading.classList.add('d-none');

      // Chart
      chartWrap.classList.remove('d-none');
      drawCompareChart('compareChart', data.gia);

      // Tables
      const summary = data.tom_tat || {};
      _renderFundTable(summary, tickers);
      fundWrap.classList.remove('d-none');

      _renderTechTable(summary, tickers);
      techWrap.classList.remove('d-none');

    } catch (err) {
      loading.classList.add('d-none');
      errEl.classList.remove('d-none');
      setText('compareErrorMsg', err.error || 'Không tải được dữ liệu');
    }
  }

  function _hideResults() {
    document.getElementById('compareResults').classList.add('d-none');
  }

  function _renderFundTable(summary, tickers) {
    const head = document.getElementById('compareFundHead');
    const body = document.getElementById('compareFundBody');

    // Header row
    head.innerHTML = '<th style="min-width:120px;">Chỉ số</th>' +
      tickers.map(ma => `<th class="text-center">${ma}</th>`).join('');

    const rows = ['ROE', 'ROA', 'EPS', 'PE', 'PB', 'DE', 'Điểm', 'Xếp loại'];
    const getVal = (ma, key) => {
      const s = summary[ma];
      if (!s || !s.co_ban) return null;
      if (key === 'Điểm')   return s.co_ban.tong;
      if (key === 'Xếp loại') return s.co_ban.phan_loai;
      return s.co_ban[key];
    };

    body.innerHTML = rows.map(row => {
      const cells = tickers.map(ma => {
        const v = getVal(ma, row);
        if (row === 'Xếp loại') {
          return `<td class="text-center"><span class="badge badge-signal ${RANK_CLASS[v] || ''}">${v ?? '—'}</span></td>`;
        }
        if (v == null) return '<td class="text-center">—</td>';
        const fmt = row === 'EPS' ? fmtInt(v) + ' ₫'
                  : row === 'Điểm' ? v + '/12'
                  : typeof v === 'number' ? v.toFixed(2)
                  : v;
        return `<td class="text-center">${fmt}</td>`;
      }).join('');
      return `<tr><td class="fw-semibold">${row}</td>${cells}</tr>`;
    }).join('');
  }

  function _renderTechTable(summary, tickers) {
    const head = document.getElementById('compareTechHead');
    const body = document.getElementById('compareTechBody');

    head.innerHTML = '<th style="min-width:120px;">Chỉ báo</th>' +
      tickers.map(ma => `<th class="text-center">${ma}</th>`).join('');

    const rows = [
      { key: 'gia_hien_tai', label: 'Giá hiện tại', fmt: v => fmtNum(v, 1) + ' nghìn' },
      { key: 'tin_hieu',     label: 'Tín hiệu',
        render: (ma) => {
          const v = summary[ma]?.ky_thuat?.tin_hieu;
          return `<span class="badge badge-signal ${SIGNAL_BADGE_CLASS[v] || ''}">${v ?? '—'}</span>`;
        }
      },
      { key: 'rsi',  label: 'RSI',  fmt: v => v?.toFixed(1) },
      { key: 'ma20', label: 'MA20', fmt: v => fmtNum(v, 2) },
      { key: 'ma50', label: 'MA50', fmt: v => fmtNum(v, 2) },
    ];

    body.innerHTML = rows.map(r => {
      const cells = tickers.map(ma => {
        if (r.render) return `<td class="text-center">${r.render(ma)}</td>`;
        const src = r.key === 'gia_hien_tai'
          ? summary[ma]?.info?.[r.key]
          : summary[ma]?.ky_thuat?.[r.key];
        return `<td class="text-center">${src != null ? r.fmt(src) : '—'}</td>`;
      }).join('');
      return `<tr><td class="fw-semibold">${r.label}</td>${cells}</tr>`;
    }).join('');
  }
}
