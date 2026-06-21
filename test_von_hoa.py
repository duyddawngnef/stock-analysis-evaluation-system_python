import sys
sys.path.insert(0, '.')
from modules.module1_thudulieu import lay_thong_tin_co_phieu

result = lay_thong_tin_co_phieu('VNM')
for k, v in result.items():
    print(f'{k}: {repr(v)}')
print('---')
vh = result.get('von_hoa', 0)
print(f'Von hoa: {vh:,.1f} ty dong')
if vh > 0:
    print('SUCCESS: von hoa != 0')
else:
    print('FAIL: von hoa still 0')
