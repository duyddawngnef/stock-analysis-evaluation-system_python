/**
 * api_client.js — Thin wrapper around all Flask API endpoints.
 *
 * Usage:
 *   const info = await API.thongTin('VNM');
 *   const prices = await API.giaLichSu('VNM');
 *   const tech = await API.kyThuat('VNM');
 *   const fund = await API.coBan('VNM');
 *   const compare = await API.soSanh(['VNM', 'FPT']);
 */

const API = (() => {
  /**
   * Internal fetch helper.
   * Throws an object { error, detail } on non-2xx responses.
   */
  async function _get(url) {
    const res = await fetch(url);
    const json = await res.json();
    if (!res.ok) {
      throw { error: json.error || 'Lỗi không xác định', detail: json.detail || '' };
    }
    return json;
  }

  async function _post(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const json = await res.json();
    if (!res.ok) {
      throw { error: json.error || 'Lỗi không xác định', detail: json.detail || '' };
    }
    return json;
  }

  return {
    /** Thông tin chung cổ phiếu */
    thongTin:  (ma) => _get(`/api/thong-tin/${encodeURIComponent(ma)}`),

    /** Lịch sử giá OHLCV — trả về array of {date, open, high, low, close, volume} */
    giaLichSu: (ma) => _get(`/api/gia-lich-su/${encodeURIComponent(ma)}`),

    /** Phân tích kỹ thuật */
    kyThuat:   (ma) => _get(`/api/ky-thuat/${encodeURIComponent(ma)}`),

    /** Phân tích cơ bản */
    coBan:     (ma) => _get(`/api/co-ban/${encodeURIComponent(ma)}`),

    /** So sánh nhiều mã — body: { ma_list: ['VNM', 'FPT', ...] } */
    soSanh:    (maList) => _post('/api/so-sanh', { ma_list: maList }),
  };
})();
