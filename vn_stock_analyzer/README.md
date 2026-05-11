# UI Design System — VN Stock Analyzer

Tài liệu này là chuẩn giao diện duy nhất cho toàn bộ dự án.
Mọi thành phần HTML, CSS, và Chart.js **phải** tuân theo các quy tắc dưới đây.

---

## 1. Màu sắc (Color Palette)

### 1.1 CSS Variables — khai báo trong `static/css/style.css`

```css
:root {
  /* Brand */
  --color-primary:        #0d6efd;   /* Bootstrap blue — nút chính, link */
  --color-primary-dark:   #0a58ca;   /* hover state */
  --color-secondary:      #6c757d;   /* văn bản phụ, badge */

  /* Background */
  --color-bg:             #f8f9fa;   /* nền trang */
  --color-bg-card:        #ffffff;   /* nền card / panel */
  --color-bg-header:      #212529;   /* navbar */

  /* Border */
  --color-border:         #dee2e6;   /* viền card, bảng */

  /* Tín hiệu giao dịch */
  --color-mua-manh:       #198754;   /* MUA MẠNH  — Bootstrap success */
  --color-mua:            #20c997;   /* MUA        — Bootstrap teal */
  --color-giu:            #ffc107;   /* GIỮ        — Bootstrap warning */
  --color-ban:            #dc3545;   /* BÁN        — Bootstrap danger */

  /* Phân loại cơ bản */
  --color-tot:            #198754;   /* TỐT  — xanh lá */
  --color-kha:            #fd7e14;   /* KHÁ  — cam */
  --color-yeu:            #dc3545;   /* YẾU  — đỏ */

  /* Typography */
  --font-size-base:       0.9375rem; /* 15px */
  --font-size-sm:         0.8125rem; /* 13px */
  --font-size-lg:         1.125rem;  /* 18px */
  --font-weight-normal:   400;
  --font-weight-medium:   500;
  --font-weight-bold:     600;
}
```

### 1.2 Bảng màu tín hiệu kỹ thuật

| Tín hiệu | Màu hex   | Bootstrap class | CSS variable       |
| -------- | --------- | --------------- | ------------------ |
| MUA MẠNH | `#198754` | `text-success`  | `--color-mua-manh` |
| MUA      | `#20c997` | `text-info`     | `--color-mua`      |
| GIỮ      | `#ffc107` | `text-warning`  | `--color-giu`      |
| BÁN      | `#dc3545` | `text-danger`   | `--color-ban`      |

### 1.3 Bảng màu phân loại cơ bản

| Phân loại | Màu hex   | Bootstrap class | CSS variable  |
| --------- | --------- | --------------- | ------------- |
| TỐT       | `#198754` | `text-success`  | `--color-tot` |
| KHÁ       | `#fd7e14` | `text-warning`  | `--color-kha` |
| YẾU       | `#dc3545` | `text-danger`   | `--color-yeu` |

### 1.4 Màu biểu đồ Chart.js (tối đa 5 mã)

Dùng cho trang **So sánh** — mỗi mã cổ phiếu một màu, theo thứ tự cố định:

```js
// static/js/charts.js
const TICKER_COLORS = [
  { border: '#0d6efd', bg: 'rgba(13,110,253,0.12)'  },  // xanh dương
  { border: '#dc3545', bg: 'rgba(220,53,69,0.12)'   },  // đỏ
  { border: '#198754', bg: 'rgba(25,135,84,0.12)'   },  // xanh lá
  { border: '#fd7e14', bg: 'rgba(253,126,20,0.12)'  },  // cam
  { border: '#6f42c1', bg: 'rgba(111,66,193,0.12)'  },  // tím
];
```

Màu dành riêng cho đường đơn trong tab **Kỹ thuật**:

| Đường          | Màu hex   |
| -------------- | --------- |
| Giá đóng cửa   | `#0d6efd` |
| MA20           | `#ffc107` |
| MA50           | `#fd7e14` |
| MA200          | `#dc3545` |
| Bollinger trên | `#6f42c1` |
| Bollinger dưới | `#6f42c1` |
| MACD           | `#0d6efd` |
| Signal         | `#dc3545` |
| Histogram      | `#198754` |

---

## 2. Typography

Font mặc định của Bootstrap 5 (`system-ui` stack). Không import font ngoài.

```css
body {
  font-family: var(--bs-font-sans-serif);
  font-size: var(--font-size-base);
  color: #212529;
  background-color: var(--color-bg);
}

h1, h2, h3  { font-weight: var(--font-weight-bold); }
.text-muted  { color: var(--color-secondary) !important; }
.label-metric {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}
```

---

## 3. Cấu trúc trang

### 3.1 Navbar (`base.html`)

```html
<nav class="navbar navbar-dark bg-dark sticky-top">
  <div class="container-fluid">
    <a class="navbar-brand fw-bold" href="/">
      <span class="material-icons align-middle">bar_chart</span>
      VN Stock Analyzer
    </a>
  </div>
</nav>
```

### 3.2 Layout trang chính

```html
<div class="container py-4">
  <!-- nội dung trang -->
</div>
```

---

## 4. Các thành phần tái sử dụng

### 4.1 Card chỉ số

```html
<div class="card border-0 shadow-sm h-100">
  <div class="card-body">
    <p class="label-metric text-muted mb-1">Tên chỉ số</p>
    <p class="fs-5 fw-bold mb-0">Giá trị</p>
  </div>
</div>
```

### 4.2 Badge tín hiệu

```html
<span class="badge rounded-pill fs-6 badge-mua-manh">MUA MẠNH</span>
<span class="badge rounded-pill fs-6 badge-mua">MUA</span>
<span class="badge rounded-pill fs-6 badge-giu">GIỮ</span>
<span class="badge rounded-pill fs-6 badge-ban">BÁN</span>
```

CSS tương ứng:

```css
/* style.css */
.badge-mua-manh { background-color: var(--color-mua-manh); color: #fff; }
.badge-mua      { background-color: var(--color-mua);      color: #fff; }
.badge-giu      { background-color: var(--color-giu);      color: #212529; }
.badge-ban      { background-color: var(--color-ban);      color: #fff; }

.badge-tot { background-color: var(--color-tot); color: #fff; }
.badge-kha { background-color: var(--color-kha); color: #fff; }
.badge-yeu { background-color: var(--color-yeu); color: #fff; }
```

Render badge động từ JS:

```js
const SIGNAL_CLASS = {
  'MUA MẠNH': 'badge-mua-manh',
  'MUA':      'badge-mua',
  'GIỮ':      'badge-giu',
  'BÁN':      'badge-ban',
};
const RANK_CLASS = { 'TỐT': 'badge-tot', 'KHÁ': 'badge-kha', 'YẾU': 'badge-yeu' };
```

### 4.3 Tab điều hướng (`ket_qua.html`)

```html
<ul class="nav nav-tabs mb-4" id="resultTabs" role="tablist">
  <li class="nav-item">
    <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tong-quan">
      <span class="material-icons align-middle me-1" style="font-size:18px;">info</span>
      Tổng quan
    </button>
  </li>
  <li class="nav-item">
    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#ky-thuat">
      <span class="material-icons align-middle me-1" style="font-size:18px;">trending_up</span>
      Kỹ thuật
    </button>
  </li>
  <li class="nav-item">
    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#co-ban">
      <span class="material-icons align-middle me-1" style="font-size:18px;">analytics</span>
      Cơ bản
    </button>
  </li>
  <li class="nav-item">
    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#so-sanh">
      <span class="material-icons align-middle me-1" style="font-size:18px;">compare_arrows</span>
      So sánh
    </button>
  </li>
</ul>
```

### 4.4 Bảng dữ liệu

```html
<table class="table table-sm table-hover align-middle">
  <thead class="table-dark">
    <tr><th>Cột</th></tr>
  </thead>
  <tbody>
    <tr><td>...</td></tr>
  </tbody>
</table>
```

### 4.5 Nút hành động

| Mục đích       | Class Bootstrap                    |
| -------------- | ---------------------------------- |
| Phân tích chính| `btn btn-primary`                  |
| Xuất Excel     | `btn btn-success`                  |
| So sánh        | `btn btn-outline-primary`          |
| Xóa / reset    | `btn btn-outline-secondary btn-sm` |

### 4.6 Form tìm kiếm (`trang_chu.html`)

```html
<div class="input-group input-group-lg shadow-sm">
  <span class="input-group-text bg-white border-end-0">
    <span class="material-icons">search</span>
  </span>
  <input type="text" class="form-control border-start-0 ps-0"
         placeholder="Nhập mã cổ phiếu (VD: VNM, FPT)">
  <button class="btn btn-primary px-4" type="submit">Phân tích</button>
</div>
```

---

## 5. Biểu đồ Chart.js

### 5.1 Tùy chọn chung

```js
// static/js/charts.js
const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'top' },
    tooltip: {
      callbacks: {
        label: (ctx) =>
          `${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString('vi-VN')}`,
      },
    },
  },
  scales: {
    x: { grid: { display: false } },
    y: { grid: { color: '#f0f0f0' } },
  },
};
```

### 5.2 Chiều cao canvas

```html
<div style="position:relative; height:320px;">
  <canvas id="priceChart"></canvas>
</div>
```

### 5.3 Zoom / pan

```js
plugins: {
  zoom: {
    zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' },
    pan:  { enabled: true, mode: 'x' },
  },
},
```

---

## 6. Icons

Font cục bộ tại `static/fonts/MaterialIcons-Regular.ttf` — **không** dùng Google Fonts CDN.

```css
@font-face {
  font-family: 'Material Icons';
  font-style: normal;
  font-weight: 400;
  src: url('../fonts/MaterialIcons-Regular.ttf') format('truetype');
}

.material-icons {
  font-family: 'Material Icons';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  display: inline-block;
  line-height: 1;
  text-transform: none;
  letter-spacing: normal;
  word-wrap: normal;
  white-space: nowrap;
  direction: ltr;
  -webkit-font-smoothing: antialiased;
}
```

Bảng icon quy ước:

| Vị trí             | Icon name        |
| ------------------ | ---------------- |
| Tìm kiếm           | `search`         |
| Giá / biểu đồ giá  | `trending_up`    |
| Kỹ thuật           | `analytics`      |
| Cơ bản             | `bar_chart`      |
| So sánh            | `compare_arrows` |
| Xuất Excel         | `download`       |
| Thông tin          | `info`           |
| Cảnh báo           | `warning`        |

---

## 7. Responsive

| Breakpoint | Hành vi                                       |
| ---------- | --------------------------------------------- |
| `< 576px`  | 1 cột, tab thu gọn, ẩn label phụ              |
| `576–768px`| 2 cột card chỉ số                             |
| `≥ 768px`  | Layout đầy đủ — sidebar + chart song song     |

Dùng grid Bootstrap (`col-12 col-md-6 col-lg-4`) — không viết media query tùy chỉnh trừ khi cần thiết.

---

## 8. Định dạng số

```js
// JavaScript
number.toLocaleString('vi-VN')           // 1.234.567
price.toLocaleString('vi-VN') + ' ₫'    // 67.500 ₫
```

```python
# Jinja2
{{ value | int | format(',d') }}         # 1,234,567
```

```python
# openpyxl (Excel export)
cell.number_format = '#,##0'             # số nguyên
cell.number_format = '#,##0.00'          # số thực
```

---

## 9. Quy tắc chung

1. Dùng `var(--color-*)` thay vì hard-code hex trực tiếp trong template.
2. Màu badge tín hiệu và phân loại phải render từ `SIGNAL_CLASS` / `RANK_CLASS` — không hard-code class theo từng mã.
3. Không thêm animation hoặc transition ngoài Bootstrap default.
4. Không nhúng thư viện ngoài không có trong `requirements.txt` hoặc `static/`.
5. Mỗi trang load dưới 3 giây ở mạng trung bình.
