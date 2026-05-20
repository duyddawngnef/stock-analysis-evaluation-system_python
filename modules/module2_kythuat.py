import pandas as pd

# Tính đường trung bình động (Moving Average).
def tinh_ma(df_gia: pd.DataFrame, period: int) -> pd.Series:
    return df_gia['close'].rolling(window=period).mean()

def tao_tin_hieu_ma(df_gia: pd.DataFrame) -> str:
    # Quy tắc:
    #   - Giá > MA20 > MA50 > MA200 → "MUA MẠNH"
    #   - Giá > MA20             → "MUA"
    #   - Giá nằm giữa MA20 và MA50 → "GIỮ"
    #   - Giá < MA20             → "BÁN"  
    gia_hien_tai = df_gia['close'].iloc[-1]
    ma20  = tinh_ma(df_gia, 20).iloc[-1]
    ma50  = tinh_ma(df_gia, 50).iloc[-1]
    ma200 = tinh_ma(df_gia, 200).iloc[-1]

    if gia_hien_tai > ma20 and ma20 > ma50 and ma50 > ma200:
        return "MUA"  
    elif gia_hien_tai < ma20:
        return "BÁN"
    else:
        return "GIỮ"
    
#Tính RSI (Chỉ số sức mạnh tương đối) để đánh giá tình trạng quá mua hoặc quá bán của cổ phiếu.
def tinh_rsi(df_gia: pd.DataFrame, period: int = 14) -> pd.Series:
    chenh_lech = df_gia['close'].diff()
    gain = chenh_lech.where(chenh_lech > 0, 0)
    loss = -chenh_lech.where(chenh_lech < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

#Tính MACD, Signal, Histogram.
def tinh_macd(df_gia: pd.DataFrame) -> dict:
    ema12 = df_gia['close'].ewm(span=12, adjust=False).mean()
    ema26 = df_gia['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return {'macd': macd, 'signal': signal, 'histogram': histogram}

#Tính Bollinger Bands — 3 đường: upper, middle, lower.
def tinh_bollinger(df_gia: pd.DataFrame, period: int = 20, std: int = 2) -> dict:
    middle = df_gia['close'].rolling(window=period).mean()
    std_dev = df_gia['close'].rolling(window=period).std()
    return {
        'upper': middle + std * std_dev,
        'middle': middle,
        'lower': middle - std * std_dev
    }

def tao_tin_hieu_chung(df_gia: pd.DataFrame) -> dict:
    #Trả về dict gồm: tin_hieu, so_tin_hieu_mua, giai_thich
    gia  = df_gia['close'].iloc[-1]
    ma20 = tinh_ma(df_gia, 20).iloc[-1]
    ma50 = tinh_ma(df_gia, 50).iloc[-1]
    ma200 = tinh_ma(df_gia, 200).iloc[-1]
    rsi  = tinh_rsi(df_gia).iloc[-1]
    macd_data = tinh_macd(df_gia)
    bb   = tinh_bollinger(df_gia)

    so_mua = 0
    giai_thich = []

    # Tín hiệu MA
    if gia > ma20 and ma20 > ma50 and ma50 > ma200:
        so_mua += 1
        giai_thich.append("MA: giá trên cả MA20/50/200 (xu hướng tăng)")
    else:
        giai_thich.append("MA: chưa có tín hiệu tăng rõ")

    # Tín hiệu RSI
    if rsi < 30:
        so_mua += 1
        giai_thich.append(f"RSI={rsi:.1f}: quá bán → có thể mua")
    elif rsi > 70:
        giai_thich.append(f"RSI={rsi:.1f}: quá mua → cẩn thận có thể bán")
    else:
        giai_thich.append(f"RSI={rsi:.1f}: vùng trung tính")

    # Tín hiệu MACD
    if macd_data['macd'].iloc[-1] > macd_data['signal'].iloc[-1]:
        so_mua += 1
        giai_thich.append("MACD trên Signal → xu hướng tăng")
    else:
        giai_thich.append("MACD dưới Signal → xu hướng giảm")

    # Tín hiệu Bollinger
    if gia <= bb['lower'].iloc[-1]:
        so_mua += 1
        giai_thich.append("Giá chạm dãy dưới Bollinger → quá bán")
    elif gia >= bb['upper'].iloc[-1]:
        giai_thich.append("Giá chạm dãy trên Bollinger → quá mua")
    else:
        giai_thich.append("Giá trong dãy Bollinger → bình thường")

    # Kết luận
    if so_mua >= 3:
        tin_hieu = "MUA MẠNH"
    elif so_mua == 2:
        tin_hieu = "MUA"
    elif so_mua == 1:
        tin_hieu = "GIỮ"
    else:
        tin_hieu = "BÁN"

    return {
        'tin_hieu': tin_hieu,
        'so_tin_hieu_mua': so_mua,
        'giai_thich': " | ".join(giai_thich)
    }

def tom_tat_module2(df_gia: pd.DataFrame) -> dict:
    #Trả về dict đúng data contract để Flask route dùng.    
    assert len(df_gia) >= 20, f"Cần ít nhất 20 ngày dữ liệu, chỉ có {len(df_gia)}"
    assert 'close' in df_gia.columns, "DataFrame thiếu cột 'close'"
    ma20  = tinh_ma(df_gia, 20).iloc[-1]
    ma50  = tinh_ma(df_gia, 50).iloc[-1]
    ma200 = tinh_ma(df_gia, 200).iloc[-1]
    rsi   = tinh_rsi(df_gia).iloc[-1]
    macd  = tinh_macd(df_gia)
    bb    = tinh_bollinger(df_gia)
    tin_hieu = tao_tin_hieu_chung(df_gia)

    return {
        "ma": {
            "MA20":  round(ma20, 2)  if not pd.isna(ma20)  else None,
            "MA50":  round(ma50, 2)  if not pd.isna(ma50)  else None,
            "MA200": round(ma200, 2) if not pd.isna(ma200) else None,
        },
        "rsi": round(float(rsi), 2),
        "macd": {
            "macd":      round(float(macd['macd'].iloc[-1]), 4),
            "signal":    round(float(macd['signal'].iloc[-1]), 4),
            "histogram": round(float(macd['histogram'].iloc[-1]), 4),
        },
        "bollinger": {
            "upper":  round(float(bb['upper'].iloc[-1]), 2),
            "middle": round(float(bb['middle'].iloc[-1]), 2),
            "lower":  round(float(bb['lower'].iloc[-1]), 2),
        },
        "tin_hieu":         tin_hieu['tin_hieu'],
        "so_tin_hieu_mua":  tin_hieu['so_tin_hieu_mua'],
        "giai_thich":       tin_hieu['giai_thich'],
    }