import os
import re
import glob
import numpy as np
import pandas as pd

BASE_DIR = r"C:\Users\A\Desktop\데이터"
POP_ROOT = os.path.join(BASE_DIR, "구미 유동인구 데이터")

PROJECT_DIR = r"C:\Users\A\Desktop\Proj\store analysis"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")
os.makedirs(OUT_DIR, exist_ok=True)

YEARS = [2023, 2024]


def read_table_auto(path):
    ext = os.path.splitext(path)[1].lower()

    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    for enc in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            with open(path, "r", encoding=enc) as f:
                first_line = f.readline()

            sep = "|" if "|" in first_line else "," if "," in first_line else "\t"
            return pd.read_csv(path, encoding=enc, sep=sep)

        except Exception:
            continue

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
        folders.extend(glob.glob(os.path.join(POP_ROOT, f"{year}_*월_인구")))
    return sorted(folders)


def find_file(folder, pattern):
    files = (
        glob.glob(os.path.join(folder, "*.csv"))
        + glob.glob(os.path.join(folder, "*.xlsx"))
        + glob.glob(os.path.join(folder, "*.xls"))
    )

    for f in files:
        name = os.path.basename(f).lower()
        if re.search(pattern, name):
            return f

    return None


def normalize_code(x):
    if pd.isna(x):
        return ""

    try:
        x = str(int(float(str(x).replace(",", "").strip())))
    except:
        x = str(x).strip()

    if x.endswith(".0"):
        x = x[:-2]

    # 10자리 행정동코드면 뒤 2자리 제거해서 8자리로 통일
    if len(x) == 10 and x.startswith("4719"):
        x = x[:8]

    return x

def clean_num(s):
    return (
        s.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .replace(["", "nan", "None", "NaN"], np.nan)
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def aggregate_population(path, code_col, prefixes, value_name):
    df = read_table_auto(path)

    if code_col not in df.columns:
        print(f"[스킵] {os.path.basename(path)}: {code_col} 컬럼 없음")
        return pd.DataFrame(columns=["dong_code", value_name])

    pop_cols = []

    for c in df.columns:
        c_low = str(c).lower()

        for p in prefixes:
            if c_low.startswith(p.lower()):
                pop_cols.append(c)
                break

    if not pop_cols:
        print(f"[스킵] {os.path.basename(path)}: 인구 컬럼 없음")
        return pd.DataFrame(columns=["dong_code", value_name])

    print(f"[읽음] {os.path.basename(path)}")
    print("  코드 컬럼:", code_col)
    print("  인구 컬럼 수:", len(pop_cols))
    print("  예시:", pop_cols[:6])

    df["dong_code"] = df[code_col].apply(normalize_code)

    for c in pop_cols:
        df[c] = clean_num(df[c])

    df[value_name] = df[pop_cols].sum(axis=1)

    # 월 단위 평균값으로 집계
    result = (
        df.groupby("dong_code", as_index=False)[value_name]
        .mean()
    )

    return result


def preprocess_one_month(folder):
    ym = ym_from_folder(folder)
    if ym is None:
        return None

    print("\n==============================")
    print("처리 중:", folder)

    # 1~4월 포함 공통 파일 구조
    exist_dong_file = find_file(folder, r"^gumi_exist_dong_\d{6}")
    living_file = find_file(folder, r"^gumi_living_pop_\d{6}")
    inflow_file = find_file(folder, r"^gumi_inflow_\d{6}")

    # 혹시 이후 월에 분리 파일이 있으면 대비
    home_file = find_file(folder, r"exist.*dong.*h.*pop")
    work_file = find_file(folder, r"exist.*dong.*w.*pop")

    print("[파일 매칭]")
    print("  exist_dong_file:", os.path.basename(exist_dong_file) if exist_dong_file else "없음")
    print("  living_file    :", os.path.basename(living_file) if living_file else "없음")
    print("  home_file      :", os.path.basename(home_file) if home_file else "없음")
    print("  work_file      :", os.path.basename(work_file) if work_file else "없음")
    print("  inflow_file    :", os.path.basename(inflow_file) if inflow_file else "없음")

    base = pd.DataFrame(columns=["dong_code"])

    # --------------------------------------------------
    # gumi_exist_dong_YYYYMM.csv
    # h_* = 주거인구, w_* = 직장인구, v_* = 방문/시간대 인구
    # --------------------------------------------------
    if exist_dong_file:
        home = aggregate_population(
            exist_dong_file,
            code_col="admdong_cd",
            prefixes=["h_m_", "h_f_"],
            value_name="home_pop"
        )
        base = home if base.empty else base.merge(home, on="dong_code", how="outer")

        work = aggregate_population(
            exist_dong_file,
            code_col="admdong_cd",
            prefixes=["w_m_", "w_f_"],
            value_name="work_pop"
        )
        base = work if base.empty else base.merge(work, on="dong_code", how="outer")

        # visit = aggregate_population(
        #     exist_dong_file,
        #     code_col="admdong_cd",
        #     prefixes=["v_m_", "v_f_"],
        #     value_name="time_pop"
        # )
        #base = visit if base.empty else base.merge(visit, on="dong_code", how="outer")

    else:
        if home_file:
            home = aggregate_population(
                home_file,
                code_col="admdong_cd",
                prefixes=["h_m_", "h_f_", "h_"],
                value_name="home_pop"
            )
            base = home if base.empty else base.merge(home, on="dong_code", how="outer")

        if work_file:
            work = aggregate_population(
                work_file,
                code_col="admdong_cd",
                prefixes=["w_m_", "w_f_", "w_"],
                value_name="work_pop"
            )
            base = work if base.empty else base.merge(work, on="dong_code", how="outer")

    # --------------------------------------------------
    # gumi_living_pop_YYYYMM.csv
    # F_*, M_* = 생활인구
    # 기준 컬럼은 rsdn_admdong_cd
    # --------------------------------------------------
    # if living_file:
    #     living = aggregate_population(
    #         living_file,
    #         code_col="rsdn_admdong_cd",
    #         prefixes=["F_", "M_"],
    #         value_name="living_pop"
    #     )
    #     base = living if base.empty else base.merge(living, on="dong_code", how="outer")

    # --------------------------------------------------
    # gumi_inflow_YYYYMM.csv
    # F_*, M_* = 유입인구
    # 기준 컬럼은 admdong_cd
    # --------------------------------------------------
    if inflow_file:
        inflow = aggregate_population(
            inflow_file,
            code_col="admdong_cd",
            prefixes=["F_", "M_"],
            value_name="inflow_pop"
        )
        base = inflow if base.empty else base.merge(inflow, on="dong_code", how="outer")

    if base.empty:
        return None

    base = base[base["dong_code"].astype(str).str.len() > 0].copy()
    base["year_month"] = ym

    for col in ["home_pop", "work_pop", "living_pop", "inflow_pop"]:
        if col not in base.columns:
            base[col] = 0
        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)

    base["living_pop"] = base["living_pop"].astype(float)
    # living_pop 파일이 없는 경우 대체
    base.loc[base["living_pop"] == 0, "living_pop"] = (
        base["home_pop"] + base["work_pop"]
    )

    # 최종 수요인구
    # 생활인구, 직장인구, 방문/시간대 인구, 유입인구를 균형 반영
    base["total_demand_pop"] = (
        base["home_pop"] * 0.35
        + base["work_pop"] * 0.35
        + base["inflow_pop"] * 0.30
    )

    cols = [
        "dong_code",
        "year_month",
        "home_pop",
        "work_pop",
        "living_pop",
        "inflow_pop",
        "total_demand_pop",
    ]

    return base[cols]


def main():
    all_months = []

    for folder in get_month_folders():
        temp = preprocess_one_month(folder)

        if temp is not None and not temp.empty:
            all_months.append(temp)

    if not all_months:
        raise ValueError("처리된 인구 데이터가 없습니다.")

    result = pd.concat(all_months, ignore_index=True)

    result = result.groupby(["dong_code", "year_month"], as_index=False).agg(
        home_pop=("home_pop", "sum"),
        work_pop=("work_pop", "sum"),
        living_pop=("living_pop", "sum"),
        inflow_pop=("inflow_pop", "sum"),
        total_demand_pop=("total_demand_pop", "sum")
    )

    result.to_csv(
        os.path.join(OUT_DIR, "population_monthly.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    summary = result.groupby("dong_code", as_index=False).agg(
        avg_home_pop=("home_pop", "mean"),
        avg_work_pop=("work_pop", "mean"),
        avg_living_pop=("living_pop", "mean"),
        avg_inflow_pop=("inflow_pop", "mean"),
        avg_total_demand_pop=("total_demand_pop", "mean")
    )

    summary.to_csv(
        os.path.join(OUT_DIR, "population_summary.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    print("\n인구 전처리 완료")
    print("저장:", os.path.join(OUT_DIR, "population_monthly.csv"))
    print("저장:", os.path.join(OUT_DIR, "population_summary.csv"))


if __name__ == "__main__":
    main()