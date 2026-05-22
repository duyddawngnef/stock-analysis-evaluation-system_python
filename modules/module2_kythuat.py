import pandas as pd

# Tính đường trung bình động (Moving Average).
def tinh_ma(df_gia: pd.DataFrame, period: int) -> pd.Series:
    ma = df_gia['close'].rolling(window=period).mean()
    ma.name = f"MA{period}" 
    return ma

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
    avg_loss = avg_loss.replace(0, 1e-10)
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
    assert len(df_gia) >= 20, f"Cần ít nhất 20 ngày dữ liệu, chỉ có {len(df_gia)}"
    assert 'close' in df_gia.columns, "DataFrame thiếu cột 'close'"

    ma20  = tinh_ma(df_gia, 20)
    ma50  = tinh_ma(df_gia, 50)
    ma200 = tinh_ma(df_gia, 200)
    rsi_series = tinh_rsi(df_gia)
    macd_data  = tinh_macd(df_gia)
    bb         = tinh_bollinger(df_gia)
    tin_hieu   = tao_tin_hieu_chung(df_gia)

    def safe(val):
        return round(float(val), 2) if not pd.isna(val) else None

    return {
        "ma": {
            "MA20":  safe(ma20.iloc[-1]),
            "MA50":  safe(ma50.iloc[-1]),
            "MA200": safe(ma200.iloc[-1]),
        },
        "rsi":     round(float(rsi_series.iloc[-1]), 2),
        "macd": {
            "macd":      round(float(macd_data['macd'].iloc[-1]), 4),
            "signal":    round(float(macd_data['signal'].iloc[-1]), 4),
            "histogram": round(float(macd_data['histogram'].iloc[-1]), 4),
        },
        "bollinger": {
            "upper":  safe(bb['upper'].iloc[-1]),
            "middle": safe(bb['middle'].iloc[-1]),
            "lower":  safe(bb['lower'].iloc[-1]),
        },
        "tin_hieu":        tin_hieu['tin_hieu'],
        "so_tin_hieu_mua": tin_hieu['so_tin_hieu_mua'],
        "giai_thich":      tin_hieu['giai_thich'],
        "rsi_series": rsi_series.dropna().tolist(),
    }