import os
import re
import glob
import numpy as np
import pandas as pd

BASE_DIR = "C:\\Users\\A\\Desktop\\데이터"
POP_ROOT = os.path.join(BASE_DIR, "구미 유동인구 데이터")

PROJECT_DIR = "C:\\Users\\A\\Desktop\\Proj\\store analysis"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")
os.makedirs(OUT_DIR, exist_ok=True)

YEARS = [2023, 2024]


def read_table_auto(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    for enc in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            df = pd.read_csv(path, encoding=enc)
            if len(df.columns) == 1 and "|" in str(df.columns[0]):
                df = pd.read_csv(path, encoding=enc, sep="|")
            return df
        except Exception:
            pass

    raise ValueError(f"파일 읽기 실패: {path}")


def ym_from_folder(folder):
    name = os.path.basename(folder)
    m = re.search(r"(20\d{2})[_-]?(\d{1,2})", name)
    if not m:
        return None
    return f"{m.group(1)}{int(m.group(2)):02d}"


def get_month_folders():
    folders = []
    for year in YEARS:
        pattern = os.path.join(POP_ROOT, f"{year}_*월_인구")
        folders.extend(glob.glob(pattern))
    return sorted(folders)


def find_file(folder, keyword):
    files = glob.glob(os.path.join(folder, "*.csv")) + glob.glob(os.path.join(folder, "*.xlsx"))
    for f in files:
        if keyword in os.path.basename(f):
            return f
    return None


def sum_population_file(path, pop_type):
    df = read_table_auto(path)

    print(f"[인구 파일 읽음] {os.path.basename(path)}")
    print("컬럼:", df.columns.tolist()[:10])

    # 1) 행정동 코드 컬럼 찾기
    code_col = None
    for c in [
        "admdong_cd", "admdong_id", "emd_cd", "행정동코드",
        "행정동", "mc_ad3", "mc_ad3_cd", "admi_cd"
    ]:
        if c in df.columns:
            code_col = c
            break

    # 2) pcell/time 파일처럼 행정동 코드가 없고 cell_id만 있으면 동 단위 집계 불가 → 스킵
    if code_col is None:
        print(f"[스킵] {os.path.basename(path)}: 행정동 코드 컬럼 없음")
        return pd.DataFrame(columns=["dong_code", "pop_value"])

    # 3) 인구 컬럼 찾기
    if pop_type == "home":
        pop_cols = [c for c in df.columns if str(c).startswith("H_")]
    elif pop_type == "work":
        pop_cols = [c for c in df.columns if str(c).startswith("W_")]
    else:
        exclude = {
            "base_date", "timezn_cd", "use_dt", "year_month",
            "admdong_cd", "admdong_id", "emd_cd", "행정동코드",
            "행정동", "mc_ad3", "mc_ad3_cd", "admi_cd",
            "cell_id", "xcdn", "ycdn", "x", "y"
        }
        pop_cols = [
            c for c in df.columns
            if c not in exclude and pd.api.types.is_numeric_dtype(df[c])
        ]

    if len(pop_cols) == 0:
        print(f"[스킵] {os.path.basename(path)}: 인구 수치 컬럼 없음")
        return pd.DataFrame(columns=["dong_code", "pop_value"])

    for c in pop_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["pop_value"] = df[pop_cols].sum(axis=1)
    df["dong_code"] = df[code_col].astype(str)

    result = df.groupby("dong_code", as_index=False)["pop_value"].sum()
    return result


def preprocess_one_month(folder):
    ym = ym_from_folder(folder)
    if ym is None:
        return None

    home_file = find_file(folder, "exist_dong_h")
    work_file = find_file(folder, "exist_dong_w")
    time_home_file = find_file(folder, "exist_time_pcell_h")
    time_work_file = find_file(folder, "exist_time_pcell_w")
    inflow_file = find_file(folder, "inflow")

    base = pd.DataFrame({"dong_code": []})

    if home_file:
        home = sum_population_file(home_file, "home").rename(columns={"pop_value": "home_pop"})
        base = home if base.empty else base.merge(home, on="dong_code", how="outer")

    if work_file:
        work = sum_population_file(work_file, "work").rename(columns={"pop_value": "work_pop"})
        base = work if base.empty else base.merge(work, on="dong_code", how="outer")

    if time_home_file:
        th = sum_population_file(time_home_file, "time").rename(columns={"pop_value": "time_home_pop"})
        base = th if base.empty else base.merge(th, on="dong_code", how="outer")

    if time_work_file:
        tw = sum_population_file(time_work_file, "time").rename(columns={"pop_value": "time_work_pop"})
        base = tw if base.empty else base.merge(tw, on="dong_code", how="outer")

    if inflow_file:
        inflow = sum_population_file(inflow_file, "time").rename(columns={"pop_value": "inflow_pop"})
        base = inflow if base.empty else base.merge(inflow, on="dong_code", how="outer")

    if base.empty:
        return None

    base["year_month"] = ym
    for col in ["home_pop", "work_pop", "time_home_pop", "time_work_pop", "inflow_pop"]:
        if col not in base.columns:
            base[col] = 0
        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)

    base["living_pop"] = base["home_pop"] + base["work_pop"]
    base["time_pop"] = base["time_home_pop"] + base["time_work_pop"]

    base["total_demand_pop"] = (
        base["living_pop"] * 0.40
        + base["work_pop"] * 0.25
        + base["time_pop"] * 0.25
        + base["inflow_pop"] * 0.10
    )

    return base


def main():
    all_months = []

    for folder in get_month_folders():
        print("처리 중:", folder)
        temp = preprocess_one_month(folder)
        if temp is not None:
            all_months.append(temp)

    if not all_months:
        raise ValueError("처리된 인구 데이터가 없습니다.")

    result = pd.concat(all_months, ignore_index=True)
    result.to_csv(os.path.join(OUT_DIR, "population_monthly.csv"), index=False, encoding="utf-8-sig")

    summary = result.groupby("dong_code", as_index=False).agg(
        avg_living_pop=("living_pop", "mean"),
        avg_work_pop=("work_pop", "mean"),
        avg_time_pop=("time_pop", "mean"),
        avg_inflow_pop=("inflow_pop", "mean"),
        avg_total_demand_pop=("total_demand_pop", "mean")
    )

    summary.to_csv(os.path.join(OUT_DIR, "population_summary.csv"), index=False, encoding="utf-8-sig")
    print("인구 전처리 완료")


if __name__ == "__main__":
    main()