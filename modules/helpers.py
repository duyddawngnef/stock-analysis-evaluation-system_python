"""
helpers.py — Shared utility functions used across all modules.

Functions
---------
doc_cache(cache_file)  → bool
    Trả về True nếu file cache tồn tại và được tạo < 24 giờ trước.

ghi_cache(cache_file, data) → None
    Ghi data (dict hoặc list) thành file JSON UTF-8.
    Tự động tạo thư mục cha nếu chưa tồn tại.
"""

import json
import os
import time


# Thời gian cache hợp lệ: 24 giờ (tính bằng giây)
CACHE_TTL_SECONDS = 24 * 60 * 60


def doc_cache(cache_file: str) -> bool:
    """
    Kiểm tra xem file cache có hợp lệ không.

    Hợp lệ khi:
    1. File tồn tại trên ổ đĩa.
    2. Thời gian tạo/sửa đổi file < 24 giờ so với hiện tại.

    Parameters
    ----------
    cache_file : str
        Đường dẫn tới file cache (tương đối hoặc tuyệt đối).

    Returns
    -------
    bool
        True nếu cache hợp lệ, False nếu không.
    """
    if not os.path.exists(cache_file):
        return False

    file_age = time.time() - os.path.getmtime(cache_file)
    return file_age < CACHE_TTL_SECONDS


def ghi_cache(cache_file: str, data) -> None:
    """
    Ghi data vào file JSON (UTF-8, indent=2).

    Tự động tạo thư mục cha nếu chưa tồn tại.
    Ghi đè nếu file đã tồn tại.

    FIX: Xử lý trường hợp cache_file không có thư mục cha
    (os.path.dirname trả về "" thay vì path hợp lệ).

    Parameters
    ----------
    cache_file : str
        Đường dẫn tới file cache cần ghi.
    data : dict | list
        Dữ liệu có thể serialize thành JSON.
    """
    # FIX #2: dirname trả về "" nếu file ở thư mục hiện tại → makedirs("") crash
    parent_dir = os.path.dirname(cache_file)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(cache_file, "w", encoding="utf-8") as f:
        # viết dữ liệu data vào file f
        json.dump(data, f, ensure_ascii=False,
                  indent=2, default=_json_serializer)


def _json_serializer(obj):
    """
    Custom JSON serializer để xử lý các kiểu pandas/numpy không serialize được mặc định.

    Xử lý: numpy.int64, numpy.float64, pandas.Timestamp, numpy.bool_
    """
    import numpy as np
    import pandas as pd

    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if hasattr(obj, "item"):
        # Fallback cho các numpy scalar khác
        return obj.item()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
