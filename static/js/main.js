/**
 * main.js — Page-level initialization logic.
 *
 * Three entry points called from page templates:
 *   initKetQua(ma_cp)  — analysis results page
 *   initSoSanh(preFill) — comparison page
 * (trang_chu.html is self-contained — search handled inline)
 */

'use strict';

// Read a CSS variable for theme-aware colors (shared with charts.js)
function cssVar(name, fallback) {
  if (typeof getComputedStyle === 'undefined') return fallback;
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

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
  // Bind Excel button sớm — dùng data-ma có sẵn từ template (không cần đợi API)
  _bindExcelButton(ma_cp);

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

  // Excel button đã được bind từ _bindExcelButton() — không cần bind lại ở đây
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

// Module-level state: lưu full data để re-render khi đổi khoảng thời gian
let _kyThuatState = null;

/**
 * Lọc mảng prices theo khoảng thời gian.
 * @param {Array}  records  - Full price records [{date, close, ...}]
 * @param {string} period   - '1T'|'3T'|'6T'|'1N'|'3N'|'ALL'
 * @returns {Array} filtered records
 */
function _filterByPeriod(records, period) {
  if (!records || records.length === 0 || period === 'ALL') return records;

  const monthsMap = { '1T': 1, '3T': 3, '6T': 6, '1N': 12, '3N': 36 };
  const months = monthsMap[period];
  if (!months) return records;

  // Tính ngày bắt đầu tính từ ngày cuối cùng trong data
  const lastDate  = new Date(records[records.length - 1].date);
  const startDate = new Date(lastDate);
  startDate.setMonth(startDate.getMonth() - months);

  return records.filter(r => new Date(r.date) >= startDate);
}

/**
 * Bind sự kiện click cho các nút period và re-render 4 biểu đồ kỹ thuật.
 * Gọi sau khi _renderKyThuat đã chạy lần đầu (state đã được lưu).
 */
function _bindPeriodBtns() {
  const bar = document.getElementById('periodBtns');
  if (!bar) return;

  bar.addEventListener('click', (e) => {
    const btn = e.target.closest('.period-btn');
    if (!btn || !_kyThuatState) return;

    // Update active state
    bar.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    btn.classList.add('loading');

    const period = btn.dataset.period;

    // Nhỏ delay để active class render trước
    requestAnimationFrame(() => {
      const filtered = _filterByPeriod(_kyThuatState.prices, period);

      // Truyền full prices (để tính MA200/MA50 chính xác dù đang xem khung ngắn)
      drawMaChart('maChart', filtered, _kyThuatState.tech, _kyThuatState.prices);
      drawRsiChart('rsiChart', filtered, _kyThuatState.tech);
      drawMacdChart('macdChart', filtered, _kyThuatState.tech);
      drawBollingerChart('bollingerChart', filtered, _kyThuatState.tech);

      btn.classList.remove('loading');
    });
  });
}

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

  // Lưu full data vào state để period buttons dùng lại
  _kyThuatState = { prices, tech };

  // Xác định period mặc định (nút đang active, mặc định 1N)
  const activePeriod = document.querySelector('#periodBtns .period-btn.active')?.dataset?.period || '1N';
  const filteredPrices = _filterByPeriod(prices, activePeriod);

  // Charts — dùng filtered data ngay từ lần đầu
  hideLoading('maChartLoading');
  // Truyền full prices (để tính MA200/MA50/MA20 chính xác dù đang xem khung ngắn)
  drawMaChart('maChart', filteredPrices, tech, prices);
  drawRsiChart('rsiChart', filteredPrices, tech);
  drawMacdChart('macdChart', filteredPrices, tech);
  hideLoading('bollingerChartLoading');
  drawBollingerChart('bollingerChart', filteredPrices, tech);

  // Bollinger scalar values (cards bên dưới biểu đồ)
  const bb = tech.bollinger || {};
  setText('bbUpper',  bb.upper  != null ? fmtNum(bb.upper,  2)  : '—');
  setText('bbMiddle', bb.middle != null ? fmtNum(bb.middle, 2)  : '—');
  setText('bbLower',  bb.lower  != null ? fmtNum(bb.lower,  2)  : '—');

  // Bind period buttons (chỉ cần bind 1 lần, dùng flag trên DOM element)
  const periodBar = document.getElementById('periodBtns');
  if (periodBar && !periodBar.dataset.bound) {
    _bindPeriodBtns();
    periodBar.dataset.bound = '1';
  }
}


// --- Tab 3: Cơ bản ---

function _renderCoBan(fund) {
  const chiSo    = fund.chi_so    || {};
  const chamDiem = fund.cham_diem || {};

  // Format map
  const metricMap = {
    ROE: { format: v => v.toFixed(1) + '%' },
    ROA: { format: v => v.toFixed(1) + '%' },
    EPS: { format: v => fmtInt(v) + ' ₫'  },
    PE:  { format: v => v.toFixed(1) + 'x' },
    PB:  { format: v => v.toFixed(2) + 'x' },
    DE:  { format: v => v.toFixed(2)        },
  };

  const STAR_LABELS = { 2: '⭐⭐ Tốt', 1: '⭐ Khá', 0: '✗ Yếu' };
  const STAR_CLASS  = { 2: 's2', 1: 's1', 0: 's0' };

  // Ring arc circumference: r=14, C = 2π*14 ≈ 87.96
  const RING_CIRC = 87.96;

  for (const [key, cfg] of Object.entries(metricMap)) {
    const val   = chiSo[key];
    const score = chamDiem[key];
    const fmtVal = val != null ? cfg.format(val) : '—';

    // ── Hero bars (chiSoXXX, barXXX, ptsXXX)  ── same IDs as before
    setText(`chiSo${key}`, fmtVal);
    setText(`pts${key}`, score != null ? `${score}/2` : '—');
    const bar = document.getElementById(`bar${key}`);
    if (bar && score != null) {
      bar.className = `fund-bar-fill score-${score}`;
      // Also set legacy score-bar-fill class for backward compat
      bar.classList.add('score-bar-fill');
    }

    // ── KPI card value ──
    setText(`kpi${key}`, fmtVal);

    // ── KPI ring arc (score 0/1/2 → 0/50/100% of circumference) ──
    const arc = document.getElementById(`arc${key}`);
    if (arc && score != null) {
      const filled = (score / 2) * RING_CIRC;
      // Animate after paint
      requestAnimationFrame(() => {
        setTimeout(() => {
          arc.setAttribute('stroke-dasharray', `${filled.toFixed(1)} ${(RING_CIRC - filled).toFixed(1)}`);
        }, 120);
      });
    }

    // ── KPI star badge ──
    const starEl = document.getElementById(`kpiStar${key}`);
    if (starEl && score != null) {
      starEl.textContent = STAR_LABELS[score] ?? '—';
      starEl.className = `fund-kpi-star ${STAR_CLASS[score] ?? ''}`;
    }
  }

  // ── Donut & total ──
  const tong     = chamDiem.tong ?? 0;
  const phanLoai = chamDiem.phan_loai || '—';

  setText('scoreTong', tong);

  const arcEl = document.getElementById('scoreDonutArc');
  if (arcEl) {
    const color = phanLoai === 'TỐT'
      ? '#10b981'
      : phanLoai === 'KHÁ'
      ? '#f59e0b'
      : '#ef4444';
    arcEl.setAttribute('stroke', color);
    // Animate stroke-dasharray
    requestAnimationFrame(() => {
      setTimeout(() => {
        const pct = (tong / 12) * 100;
        arcEl.setAttribute('stroke-dasharray', `${pct.toFixed(1)} ${(100 - pct).toFixed(1)}`);
      }, 80);
    });
  }

  const plEl = document.getElementById('scorePhanLoai');
  if (plEl) {
    plEl.textContent = phanLoai;
    plEl.className   = `badge badge-signal fund-grade-badge ${RANK_CLASS[phanLoai] || ''}`;
  }
}


// ---------------------------------------------------------------------------
// Fund metric explanation modal
// ---------------------------------------------------------------------------

// Lưu data hiện tại để modal có thể đọc
let _currentFundData = {};

const FUND_EXPLAIN = {
  ROE: {
    title: 'ROE — Tỷ suất sinh lợi vốn CSH',
    full: 'Return on Equity',
    icon: 'percent',
    color: '#10b981',
    meaning: 'Đo lường mỗi đồng vốn cổ đông tạo ra bao nhiêu đồng lợi nhuận sau thuế. ROE cao cho thấy ban lãnh đạo sử dụng vốn hiệu quả, tạo ra giá trị tốt cho cổ đông.',
    formula: 'ROE = Lợi nhuận sau thuế ÷ Vốn chủ sở hữu × 100%',
    tiers: [
      { pts: 2, label: '≥ 20%',    desc: 'Xuất sắc — Tạo giá trị rất tốt cho cổ đông', color: '#10b981', bg: 'rgba(16,185,129,.08)' },
      { pts: 1, label: '15 – 20%', desc: 'Khá — Hiệu quả trên mức trung bình',          color: '#f59e0b', bg: 'rgba(245,158,11,.08)' },
      { pts: 0, label: '< 15%',    desc: 'Yếu — Cần cải thiện sinh lời vốn cổ đông',    color: '#ef4444', bg: 'rgba(239,68,68,.06)' },
    ],
    interpret: (val, score) => {
      if (val == null) return { text: 'Không có dữ liệu để đánh giá.', color: '#6b7280', bg: 'rgba(107,114,128,.06)' };
      if (score === 2) return { text: `ROE ${val.toFixed(1)}% — Rất tốt! Công ty tạo ra lợi nhuận cao từ vốn cổ đông, phản ánh năng lực kinh doanh xuất sắc.`, color: '#10b981', bg: 'rgba(16,185,129,.08)' };
      if (score === 1) return { text: `ROE ${val.toFixed(1)}% — Ở mức khá. Hiệu quả sử dụng vốn trên trung bình nhưng còn dư địa cải thiện.`, color: '#f59e0b', bg: 'rgba(245,158,11,.08)' };
      return { text: `ROE ${val.toFixed(1)}% — Thấp hơn ngưỡng chuẩn 15%. Công ty đang kém hiệu quả trong việc sử dụng vốn cổ đông, cần xem xét thêm về chiến lược kinh doanh.`, color: '#ef4444', bg: 'rgba(239,68,68,.06)' };
    },
  },
  ROA: {
    title: 'ROA — Tỷ suất sinh lợi tài sản',
    full: 'Return on Assets',
    icon: 'account_balance',
    color: '#3b82f6',
    meaning: 'Cho biết mỗi đồng tài sản tạo ra bao nhiêu đồng lợi nhuận. ROA cao nghĩa là công ty khai thác tài sản hiệu quả, ít lãng phí nguồn lực.',
    formula: 'ROA = Lợi nhuận sau thuế ÷ Tổng tài sản × 100%',
    tiers: [
      { pts: 2, label: '≥ 10%',  desc: 'Tốt — Khai thác tài sản hiệu quả',      color: '#10b981', bg: 'rgba(16,185,129,.08)' },
      { pts: 1, label: '5 – 10%', desc: 'Khá — Hiệu quả ở mức trung bình khá',  color: '#f59e0b', bg: 'rgba(245,158,11,.08)' },
      { pts: 0, label: '< 5%',   desc: 'Yếu — Tài sản nhiều nhưng lợi nhuận thấp', color: '#ef4444', bg: 'rgba(239,68,68,.06)' },
    ],
    interpret: (val, score) => {
      if (val == null) return { text: 'Không có dữ liệu.', color: '#6b7280', bg: 'rgba(107,114,128,.06)' };
      if (score === 2) return { text: `ROA ${val.toFixed(1)}% — Xuất sắc! Công ty khai thác tài sản rất hiệu quả, tạo ra lợi nhuận tốt từ nguồn lực hiện có.`, color: '#10b981', bg: 'rgba(16,185,129,.08)' };
      if (score === 1) return { text: `ROA ${val.toFixed(1)}% — Khá tốt. Hiệu suất tài sản ở mức trung bình khá.`, color: '#f59e0b', bg: 'rgba(245,158,11,.08)' };
      return { text: `ROA ${val.toFixed(1)}% — Dưới ngưỡng 5%. Tài sản lớn nhưng sinh lời thấp, có thể do ngành vốn nặng hoặc hiệu quả kinh doanh kém.`, color: '#ef4444', bg: 'rgba(239,68,68,.06)' };
    },
  },
  EPS: {
    title: 'EPS — Lợi nhuận / cổ phiếu',
    full: 'Earnings Per Share',
    icon: 'attach_money',
    color: '#f59e0b',
    meaning: 'Phần lợi nhuận sau thuế chia đều cho từng cổ phiếu đang lưu hành. EPS cao và tăng trưởng liên tục là dấu hiệu tốt cho nhà đầu tư.',
    formula: 'EPS = Lợi nhuận sau thuế ÷ Số cổ phiếu lưu hành',
    tiers: [
      { pts: 2, label: '≥ 5.000 ₫',      desc: 'Tốt — Lợi nhuận cao trên mỗi cổ phần',     color: '#10b981', bg: 'rgba(16,185,129,.08)' },
      { pts: 1, label: '2.000 – 5.000 ₫', desc: 'Khá — Mức lợi nhuận trung bình chấp nhận', color: '#f59e0b', bg: 'rgba(245,158,11,.08)' },
      { pts: 0, label: '< 2.000 ₫',       desc: 'Yếu — Lợi nhuận thấp hoặc thua lỗ',        color: '#ef4444', bg: 'rgba(239,68,68,.06)' },
    ],
    interpret: (val, score) => {
      if (val == null) return { text: 'Không có dữ liệu.', color: '#6b7280', bg: 'rgba(107,114,128,.06)' };
      const fv = val >= 1000 ? (val/1000).toFixed(1) + 'K' : val.toFixed(0);
      if (score === 2) return { text: `EPS ${fv}₫ — Xuất sắc! Lợi nhuận trên mỗi cổ phiếu cao, cho thấy công ty kinh doanh hiệu quả.`, color: '#10b981', bg: 'rgba(16,185,129,.08)' };
      if (score === 1) return { text: `EPS ${fv}₫ — Ở mức khá. Lợi nhuận đủ để duy trì hoạt động nhưng chưa nổi bật.`, color: '#f59e0b', bg: 'rgba(245,158,11,.08)' };
      return { text: `EPS ${fv}₫ — Thấp. Lợi nhuận trên mỗi cổ phiếu rất nhỏ, có thể chưa đủ để trả cổ tức hấp dẫn hoặc tái đầu tư.`, color: '#ef4444', bg: 'rgba(239,68,68,.06)' };
    },
  },
  PE: {
    title: 'P/E — Hệ số giá / lợi nhuận',
    full: 'Price-to-Earnings Ratio',
    icon: 'show_chart',
    color: '#8b5cf6',
    meaning: 'Cho biết thị trường sẵn sàng trả bao nhiêu lần EPS để sở hữu một cổ phiếu. P/E thấp thường nghĩa là cổ phiếu đang được định giá rẻ so với lợi nhuận; P/E quá cao là dấu hiệu có thể bị định giá quá cao.',
    formula: 'P/E = Giá thị trường ÷ EPS (Lợi nhuận / cổ phiếu)',
    tiers: [
      { pts: 2, label: '8 – 15x',         desc: 'Định giá hợp lý — vùng đầu tư giá trị',  color: '#10b981', bg: 'rgba(16,185,129,.08)' },
      { pts: 1, label: '15 – 20x',         desc: 'Hơi cao — cần thận trọng',               color: '#f59e0b', bg: 'rgba(245,158,11,.08)' },
      { pts: 0, label: '> 20x hoặc < 8x', desc: 'Rất cao (bong bóng) hoặc rủi ro khác',   color: '#ef4444', bg: 'rgba(239,68,68,.06)' },
    ],
    interpret: (val, score) => {
      if (val == null) return { text: 'Không có dữ liệu.', color: '#6b7280', bg: 'rgba(107,114,128,.06)' };
      if (score === 2) return { text: `P/E ${val.toFixed(1)}x — Định giá hợp lý! Cổ phiếu đang ở vùng giá trị tốt so với lợi nhuận, phù hợp cho đầu tư dài hạn.`, color: '#10b981', bg: 'rgba(16,185,129,.08)' };
      if (score === 1) return { text: `P/E ${val.toFixed(1)}x — Hơi đắt. Thị trường đang kỳ vọng tăng trưởng cao, cần theo dõi kết quả kinh doanh tiếp theo.`, color: '#f59e0b', bg: 'rgba(245,158,11,.08)' };
      if (val > 20) return { text: `P/E ${val.toFixed(1)}x — Rất cao! Giá cổ phiếu đang ở mức premium so với lợi nhuận thực. Rủi ro định giá cao nếu lợi nhuận không tăng trưởng tương xứng.`, color: '#ef4444', bg: 'rgba(239,68,68,.06)' };
      return { text: `P/E ${val.toFixed(1)}x — Dưới 8x có thể là tín hiệu giá trị hoặc cảnh báo về vấn đề cơ bản của công ty. Cần phân tích thêm.`, color: '#ef4444', bg: 'rgba(239,68,68,.06)' };
    },
  },
  PB: {
    title: 'P/B — Hệ số giá / giá trị sổ',
    full: 'Price-to-Book Ratio',
    icon: 'library_books',
    color: '#ec4899',
    meaning: 'So sánh giá thị trường với giá trị sổ sách (tổng tài sản trừ nợ) của công ty. P/B < 1 nghĩa là mua cổ phiếu rẻ hơn giá trị tài sản thực.',
    formula: 'P/B = Giá thị trường ÷ BVPS  |  BVPS = Vốn CSH ÷ Số CP lưu hành',
    tiers: [
      { pts: 2, label: '< 1.5x',    desc: 'Rẻ — Đang giao dịch gần hoặc dưới giá trị sổ',     color: '#10b981', bg: 'rgba(16,185,129,.08)' },
      { pts: 1, label: '1.5 – 2.5x', desc: 'Bình thường — Phổ biến với doanh nghiệp ổn định', color: '#f59e0b', bg: 'rgba(245,158,11,.08)' },
      { pts: 0, label: '> 2.5x',    desc: 'Đắt — Thị trường kỳ vọng tăng trưởng cao',          color: '#ef4444', bg: 'rgba(239,68,68,.06)' },
    ],
    interpret: (val, score) => {
      if (val == null) return { text: 'Chưa tính được P/B do thiếu dữ liệu số cổ phiếu lưu hành từ báo cáo tài chính.', color: '#6b7280', bg: 'rgba(107,114,128,.06)' };
      if (score === 2) return { text: `P/B ${val.toFixed(2)}x — Hấp dẫn! Cổ phiếu đang được định giá gần sát hoặc dưới giá trị sổ sách, tiềm năng upside tốt.`, color: '#10b981', bg: 'rgba(16,185,129,.08)' };
      if (score === 1) return { text: `P/B ${val.toFixed(2)}x — Ở mức bình thường. Thị trường định giá hợp lý dựa trên tài sản công ty.`, color: '#f59e0b', bg: 'rgba(245,158,11,.08)' };
      return { text: `P/B ${val.toFixed(2)}x — Khá đắt. Nhà đầu tư đang trả giá cao hơn nhiều so với giá trị tài sản thực. Cần tăng trưởng lợi nhuận mạnh để biện minh.`, color: '#ef4444', bg: 'rgba(239,68,68,.06)' };
    },
  },
  DE: {
    title: 'D/E — Tỷ lệ nợ / vốn CSH',
    full: 'Debt-to-Equity Ratio',
    icon: 'balance',
    color: '#06b6d4',
    meaning: 'Đo lường mức độ sử dụng đòn bẩy tài chính. D/E thấp cho thấy công ty ít phụ thuộc vào vay nợ, an toàn hơn trong suy thoái kinh tế. D/E cao có thể tăng lợi nhuận nhưng cũng tăng rủi ro phá sản.',
    formula: 'D/E = Tổng nợ ÷ Vốn chủ sở hữu',
    tiers: [
      { pts: 2, label: '< 1',  desc: 'An toàn — Ít nợ, cấu trúc vốn vững chắc',     color: '#10b981', bg: 'rgba(16,185,129,.08)' },
      { pts: 1, label: '1 – 2', desc: 'Chấp nhận — Đòn bẩy vừa phải',               color: '#f59e0b', bg: 'rgba(245,158,11,.08)' },
      { pts: 0, label: '> 2',  desc: 'Rủi ro — Nợ nhiều, dễ tổn thương khi lãi suất tăng', color: '#ef4444', bg: 'rgba(239,68,68,.06)' },
    ],
    interpret: (val, score) => {
      if (val == null) return { text: 'Không có dữ liệu.', color: '#6b7280', bg: 'rgba(107,114,128,.06)' };
      if (score === 2) return { text: `D/E ${val.toFixed(2)} — Tuyệt vời! Cấu trúc vốn lành mạnh, ít phụ thuộc vào vay nợ. Công ty có khả năng chống chịu tốt trong giai đoạn khó khăn.`, color: '#10b981', bg: 'rgba(16,185,129,.08)' };
      if (score === 1) return { text: `D/E ${val.toFixed(2)} — Chấp nhận được. Đòn bẩy tài chính vừa phải, cần theo dõi khả năng trả nợ khi lãi suất thay đổi.`, color: '#f59e0b', bg: 'rgba(245,158,11,.08)' };
      return { text: `D/E ${val.toFixed(2)} — Đòn bẩy cao! Nợ vay gấp hơn 2 lần vốn chủ sở hữu, rủi ro tài chính đáng kể nếu lãi suất tăng hoặc doanh thu giảm.`, color: '#ef4444', bg: 'rgba(239,68,68,.06)' };
    },
  },
};

function _bindFundModal() {
  const modal    = document.getElementById('fundModal');
  const backdrop = document.getElementById('fmBackdrop');
  const closeBtn = document.getElementById('fmClose');
  if (!modal) return;

  const openModal = (key) => {
    const cfg   = FUND_EXPLAIN[key];
    if (!cfg) return;

    const fundData = _currentFundData;
    const chiSo    = fundData.chi_so    || {};
    const chamDiem = fundData.cham_diem || {};
    const val   = chiSo[key];
    const score = chamDiem[key] ?? 0;

    // Format value
    const fmtMap = {
      ROE: v => v != null ? v.toFixed(1) + '%' : '—',
      ROA: v => v != null ? v.toFixed(1) + '%' : '—',
      EPS: v => v != null ? fmtInt(v) + ' ₫'   : '—',
      PE:  v => v != null ? v.toFixed(1) + 'x'  : '—',
      PB:  v => v != null ? v.toFixed(2) + 'x'  : '—',
      DE:  v => v != null ? v.toFixed(2)         : '—',
    };
    const fmtVal = (fmtMap[key] || (() => '—'))(val);

    // Header
    const iconEl = document.getElementById('fmIcon');
    if (iconEl) {
      iconEl.innerHTML = `<span class="material-icons">${cfg.icon}</span>`;
      iconEl.style.cssText = `background:${cfg.color}18; color:${cfg.color}; width:48px; height:48px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:22px;`;
    }
    setText('fmTitle',  cfg.title);
    setText('fmFull',   cfg.full);
    setText('fmVal',    fmtVal);

    // Score badge
    const STAR_LABELS = { 2: '⭐⭐ Tốt — 2/2', 1: '⭐ Khá — 1/2', 0: '✗ Yếu — 0/2' };
    const STAR_CLASS  = { 2: 's2', 1: 's1', 0: 's0' };
    const scoreEl = document.getElementById('fmScore');
    if (scoreEl) {
      scoreEl.textContent = STAR_LABELS[score] ?? '—';
      scoreEl.className   = `fund-kpi-star ${STAR_CLASS[score] ?? ''}`;
    }

    // Meaning & formula
    setText('fmMeaning', cfg.meaning);
    setText('fmFormula', cfg.formula);

    // Tiers
    const tiersEl = document.getElementById('fmTiers');
    if (tiersEl) {
      tiersEl.innerHTML = cfg.tiers.map(t => {
        const isActive = t.pts === score;
        return `<div class="fund-modal-tier ${isActive ? 'active' : ''}" style="background:${isActive ? t.bg : 'transparent'}; color:${t.color};">
          <span class="fund-modal-tier-label">${t.label}</span>
          <span class="fund-modal-tier-desc">${t.desc}</span>
          <span class="fund-modal-tier-pts">${t.pts}/2</span>
        </div>`;
      }).join('');
    }

    // Interpretation
    const interp   = cfg.interpret(val, score);
    const interpEl = document.getElementById('fmInterpret');
    if (interpEl) {
      interpEl.textContent  = interp.text;
      interpEl.style.cssText = `background:${interp.bg}; border-left-color:${interp.color}; color:var(--color-text);`;
    }

    // Show
    modal.setAttribute('aria-hidden', 'false');
    modal.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  };

  const closeModal = () => {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  };

  // Bind card clicks
  document.querySelectorAll('.fund-kpi-card[data-metric]').forEach(card => {
    card.addEventListener('click', () => openModal(card.dataset.metric));
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openModal(card.dataset.metric); }
    });
  });

  // Close handlers
  if (backdrop) backdrop.addEventListener('click', closeModal);
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
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
// Excel export — bind ngay khi DOM ready, không phụ thuộc vào API response
// ---------------------------------------------------------------------------

function _bindExcelButton(ma_cp) {
  const btnExcel = document.getElementById('btnXuatExcel');
  if (!btnExcel) return;

  // Tránh bind nhiều lần
  if (btnExcel.dataset.bound === '1') return;
  btnExcel.dataset.bound = '1';

  btnExcel.addEventListener('click', async () => {
    btnExcel.disabled = true;
    btnExcel.innerHTML = '<span class="material-icons" style="animation:spin 1s linear infinite">hourglass_top</span> Đang xuất…';

    try {
      const res = await fetch(`/api/xuat-excel/${encodeURIComponent(ma_cp)}`);

      if (res.ok) {
        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        // Lấy tên file từ Content-Disposition header nếu có
        const cd   = res.headers.get('Content-Disposition') || '';
        const match = cd.match(/filename\*?=['"]?(?:UTF-\d['"]*)?([^;\r\n"']+)/i);
        a.download = match ? decodeURIComponent(match[1]) : `${ma_cp}_phan_tich.xlsx`;
        a.href = url;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 3000);
      } else {
        let errMsg = 'Xuất Excel thất bại';
        try {
          const j = await res.json();
          errMsg = j.error || errMsg;
        } catch (_) {}
        _showExcelToast(errMsg, 'danger');
      }
    } catch (err) {
      _showExcelToast('Lỗi kết nối — không thể xuất file', 'danger');
      console.error('Excel export error:', err);
    } finally {
      btnExcel.disabled = false;
      btnExcel.innerHTML = '<span class="material-icons">download</span> Xuất Excel';
    }
  });
}

/** Hiển thị toast nhỏ gần nút Excel */
function _showExcelToast(msg, type = 'danger') {
  const existing = document.getElementById('excelToast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'excelToast';
  toast.style.cssText = [
    'position:fixed', 'bottom:1.5rem', 'right:1.5rem', 'z-index:9999',
    'padding:.75rem 1.25rem', 'border-radius:.75rem',
    `background:${type === 'danger'
      ? cssVar('--color-danger',  '#dc3545')
      : cssVar('--color-success', '#198754')}`,
    'color:#fff', 'font-size:.875rem', 'box-shadow:0 4px 20px rgba(0,0,0,.35)',
    'display:flex', 'align-items:center', 'gap:.5rem',
    'animation:slideInRight .3s ease',
  ].join(';');
  toast.innerHTML = `<span class="material-icons" style="font-size:18px">
    ${type === 'danger' ? 'error_outline' : 'check_circle'}</span>${msg}`;
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity .4s'; }, 3500);
  setTimeout(() => toast.remove(), 4000);
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
