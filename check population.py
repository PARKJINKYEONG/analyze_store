import pandas as pd

path = r"C:\Users\A\Desktop\데이터\구미 유동인구 데이터\2023_01월_인구\gumi_exist_time_pcell_h_pop_202301.csv"

for enc in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
    try:
        df = pd.read_csv(path, encoding=enc, nrows=5)
        print("인코딩:", enc)
        print("컬럼:", df.columns.tolist())
        print(df.head())
        break
    except Exception:
        continue