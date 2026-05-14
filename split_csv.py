import os
import pandas as pd

PROJECT_DIR = r"C:\Users\A\Desktop\Proj\store analysis"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")


def split_by_period(df, prefix):
    """year_month 기준 6개월 단위 4분할 저장"""
    df = df.copy()
    df["year_month"] = df["year_month"].astype(str)

    periods = {
        f"{prefix}_2023_H1": ("202301", "202306"),
        f"{prefix}_2023_H2": ("202307", "202312"),
        f"{prefix}_2024_H1": ("202401", "202406"),
        f"{prefix}_2024_H2": ("202407", "202412"),
    }

    print(f"\n=== {prefix} 월별 분포 진단 ===")
    print(df["year_month"].value_counts().sort_index())
    print(f"전체 행 수: {len(df):,}")
    print(f"고유 월: {sorted(df['year_month'].unique())}")

    for name, (start, end) in periods.items():
        sub = df[(df["year_month"] >= start) & (df["year_month"] <= end)].copy()
        path = os.path.join(OUT_DIR, f"{name}.csv")
        sub.to_csv(path, index=False, encoding="utf-8-sig")
        months_in_sub = sorted(sub["year_month"].unique()) if len(sub) > 0 else []
        print(f"저장: {os.path.basename(path)} | 행 수: {len(sub):>10,} | 포함 월: {months_in_sub}")


def main():
    # 1. cell 단위 분할
    cell_path = os.path.join(OUT_DIR, "consumption_monthly_cell.csv")
    if os.path.exists(cell_path):
        print(f"\n[1/2] {os.path.basename(cell_path)} 로딩 중...")
        cell = pd.read_csv(cell_path, encoding="utf-8-sig")
        print(f"로딩 완료. 행 수: {len(cell):,}")
        split_by_period(cell, "consumption_monthly_cell")
    else:
        print(f"파일 없음: {cell_path}")

    # 2. 행정동 단위 분할
    dong_path = os.path.join(OUT_DIR, "consumption_monthly_dong.csv")
    if os.path.exists(dong_path):
        print(f"\n[2/2] {os.path.basename(dong_path)} 로딩 중...")
        dong = pd.read_csv(dong_path, encoding="utf-8-sig")
        print(f"로딩 완료. 행 수: {len(dong):,}")
        split_by_period(dong, "consumption_monthly_dong")
    else:
        print(f"파일 없음: {dong_path}")

    print("\n분할 완료")


if __name__ == "__main__":
    main()