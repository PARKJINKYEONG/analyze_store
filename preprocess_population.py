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
    """파일 자동 읽기 (구분자/인코딩 자동 판별)"""
    ext = os.path.splitext(path)[1].lower()

    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    for enc in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            # 먼저 첫 줄을 읽어서 구분자 판별
            with open(path, "r", encoding=enc) as f:
                first_line = f.readline()

            if "|" in first_line:
                sep = "|"
            elif "\t" in first_line:
                sep = "\t"
            else:
                sep = ","

            df = pd.read_csv(path, encoding=enc, sep=sep)
            return df

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
        pattern = os.path.join(POP_ROOT, f"{year}_*월_인구")
        folders.extend(glob.glob(pattern))

    return sorted(folders)


def debug_folder(folder):
    files = (
        glob.glob(os.path.join(folder, "*.csv"))
        + glob.glob(os.path.join(folder, "*.xlsx"))
        + glob.glob(os.path.join(folder, "*.xls"))
    )
    print(f"\n[디버그] 폴더 내 파일 목록 ({os.path.basename(folder)})")
    for f in files:
        print(" -", os.path.basename(f))


def find_file_by_pattern(folder, pattern):
    """정규식 패턴으로 파일명 매칭"""
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


def normalize_dong_code(x):
    """행정동 코드 정규화"""
    if pd.isna(x):
        return ""

    x = str(x).strip()

    try:
        if "e" in x.lower() or "." in x:
            x = str(int(float(x)))
    except Exception:
        pass

    if x.endswith(".0"):
        x = x[:-2]

    return x


def find_code_col(df):
    """행정동 코드 컬럼 찾기"""
    candidates = [
        "admdong_cd", "admdong_id", "admi_cd", "adm_cd", "emd_cd",
        "행정동코드", "행정동", "mc_ad3", "mc_ad3_cd",
    ]

    cols_lower = {str(c).lower(): c for c in df.columns}

    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]

    return None


def clean_numeric_series(s):
    return (
        s.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .replace(["", "nan", "None", "NaN"], np.nan)
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def find_population_columns(df, pop_type):
    """인구 수치 컬럼 자동 탐색

    pop_type:
      - home : h_로 시작하는 거주인구 컬럼 (h_m_*, h_f_*)
      - work : w_로 시작하는 근무인구 컬럼
      - inflow : 유입인구 관련 컬럼
    """
    cols = list(df.columns)

    exclude_keywords = [
        "code", "cd", "id", "dong", "admi", "adm", "emd",
        "date", "dt", "timezn", "time_cd", "year", "month",
        "cell", "xcdn", "ycdn", "x_", "y_", "lon", "lat", "coord",
        "시도", "시군구", "행정", "법정", "주소", "지역",
    ]

    pop_cols = []

    if pop_type == "home":
        for c in cols:
            c_lower = str(c).lower()

            if any(ex in c_lower for ex in exclude_keywords):
                continue

            if re.match(r"^h[_]", c_lower):
                pop_cols.append(c)

    elif pop_type == "work":
        for c in cols:
            c_lower = str(c).lower()

            if any(ex in c_lower for ex in exclude_keywords):
                continue

            if re.match(r"^w[_]", c_lower):
                pop_cols.append(c)

    elif pop_type == "inflow":
        include_keywords = [
            "inflow", "flow", "pop", "cnt",
            "인구", "유입", "방문", "유동",
        ]

        for c in cols:
            c_lower = str(c).lower()

            if any(ex in c_lower for ex in exclude_keywords):
                continue

            if any(key in c_lower for key in include_keywords):
                pop_cols.append(c)

        if not pop_cols:
            for c in cols:
                c_lower = str(c).lower()

                if any(ex in c_lower for ex in exclude_keywords):
                    continue

                sample = clean_numeric_series(df[c])
                max_val = sample.max()

                if 0 < max_val < 10_000_000:
                    pop_cols.append(c)

    return pop_cols


def sum_population_file(path, pop_type):
    df = read_table_auto(path)

    print(f"\n[인구 파일 읽음] {os.path.basename(path)}")
    print(f"컬럼 ({len(df.columns)}개):", df.columns.tolist()[:10],
          "..." if len(df.columns) > 10 else "")

    code_col = find_code_col(df)

    if code_col is None:
        print(f"[스킵] {os.path.basename(path)}: 행정동 코드 컬럼 없음")
        return pd.DataFrame(columns=["dong_code", "pop_value"])

    pop_cols = find_population_columns(df, pop_type)

    if len(pop_cols) == 0:
        print(f"[스킵] {os.path.basename(path)}: 인구 수치 컬럼 없음 (pop_type={pop_type})")
        return pd.DataFrame(columns=["dong_code", "pop_value"])

    print(f"행정동 코드 컬럼: {code_col}")
    print(f"인구 컬럼 ({len(pop_cols)}개): {pop_cols[:5]}"
          + (" ..." if len(pop_cols) > 5 else ""))

    df["dong_code"] = df[code_col].apply(normalize_dong_code)

    for c in pop_cols:
        df[c] = clean_numeric_series(df[c])

    df["pop_value"] = df[pop_cols].sum(axis=1)

    # 비정상 거대값 제거
    df.loc[df["pop_value"] > 100_000_000, "pop_value"] = np.nan
    df["pop_value"] = df["pop_value"].fillna(0)

    result = (
        df.groupby("dong_code", as_index=False)["pop_value"]
        .sum()
    )

    return result


def preprocess_one_month(folder):
    ym = ym_from_folder(folder)

    if ym is None:
        return None

    debug_folder(folder)

    # 행정동 단위 파일만 사용 (pcell = 격자 단위는 좌표만 있어서 제외)
    home_file = find_file_by_pattern(folder, r"exist_dong_h[_]?pop")
    work_file = find_file_by_pattern(folder, r"exist_dong_w[_]?pop")
    inflow_file = find_file_by_pattern(folder, r"^gumi_inflow")

    print(f"\n[파일 매칭 결과] {os.path.basename(folder)}")
    print("  home_file   :", os.path.basename(home_file) if home_file else "없음")
    print("  work_file   :", os.path.basename(work_file) if work_file else "없음")
    print("  inflow_file :", os.path.basename(inflow_file) if inflow_file else "없음")

    base = pd.DataFrame(columns=["dong_code"])

    if home_file:
        home = (
            sum_population_file(home_file, "home")
            .rename(columns={"pop_value": "home_pop"})
        )
        base = home if base.empty else base.merge(home, on="dong_code", how="outer")

    if work_file:
        work = (
            sum_population_file(work_file, "work")
            .rename(columns={"pop_value": "work_pop"})
        )
        base = work if base.empty else base.merge(work, on="dong_code", how="outer")

    if inflow_file:
        inflow = (
            sum_population_file(inflow_file, "inflow")
            .rename(columns={"pop_value": "inflow_pop"})
        )
        base = inflow if base.empty else base.merge(inflow, on="dong_code", how="outer")

    if base.empty:
        return None

    # 빈 dong_code 제거
    base = base[base["dong_code"].astype(str).str.len() > 0].copy()

    base["year_month"] = ym

    for col in ["home_pop", "work_pop", "inflow_pop"]:
        if col not in base.columns:
            base[col] = 0

        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)

    # dong_code 기준 재집계 (혹시 같은 코드가 여러 행이면 합산)
    base = base.groupby(["dong_code", "year_month"], as_index=False).agg({
        "home_pop": "sum",
        "work_pop": "sum",
        "inflow_pop": "sum",
    })

    base["living_pop"] = base["home_pop"] + base["work_pop"]

    # 시간대별(time_pop) 제외에 따른 가중치 재배분
    # 기존: living 0.40 + work 0.25 + time 0.25 + inflow 0.10
    # 변경: living 0.55 + work 0.30 + inflow 0.15
    base["total_demand_pop"] = (
        base["home_pop"] * 0.55
        + base["work_pop"] * 0.30
        + base["inflow_pop"] * 0.15
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
        print("\n==============================")
        print("처리 중:", folder)

        temp = preprocess_one_month(folder)

        if temp is not None and not temp.empty:
            all_months.append(temp)

    if not all_months:
        raise ValueError("처리된 인구 데이터가 없습니다.")

    result = pd.concat(all_months, ignore_index=True)

    result.to_csv(
        os.path.join(OUT_DIR, "population_monthly.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    summary = result.groupby("dong_code", as_index=False).agg(
        avg_home_pop=("home_pop", "mean"),
        avg_work_pop=("work_pop", "mean"),
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