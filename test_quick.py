# -*- coding: utf-8 -*-
import sys, time
sys.stdout.reconfigure(encoding='utf-8')

from modules import module1_thudulieu as m1
from modules import module2_kythuat as m2
from modules import module3_coban as m3

mas = ['VCB', 'HPG', 'VNM', 'FPT', 'GAS', 'SSI', 'REE']
print(f"{'MA':6s} | {'THOI GIAN':10s} | {'GIA':8s} | {'RSI':6s} | {'PHAN LOAI'}")
print("-" * 60)
for ma in mas:
    t = time.time()
    info  = m1.lay_thong_tin_co_phieu(ma)
    df    = m1.lay_gia_lich_su(ma)
    tech  = m2.tom_tat_module2(df)
    fund  = m3.tom_tat_module3(ma)
    elapsed = time.time() - t
    gia = info.get('gia_hien_tai', 0)
    rsi = tech.get('rsi', 0)
    phan_loai = fund['cham_diem']['phan_loai']
    print(f"{ma:6s} | {elapsed:.3f}s     | {gia:8.1f} | {rsi:6.2f} | {phan_loai}")
