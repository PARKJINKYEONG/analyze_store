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
            df = pd.read_csv(path, encoding=enc)

            if len(df.columns) == 1:
                first_col = str(df.columns[0])
                if "|" in first_col:
                    df = pd.read_csv(path, encoding=enc, sep="|")
                elif "\t" in first_col:
                    df = pd.read_csv(path, encoding=enc, sep="\t")

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
    files = (
        glob.glob(os.path.join(folder, "*.csv"))
        + glob.glob(os.path.join(folder, "*.xlsx"))
        + glob.glob(os.path.join(folder, "*.xls"))
    )

    for f in files:
        if keyword in os.path.basename(f):
            return f

    return None


def normalize_dong_code(x):
    if pd.isna(x):
        return ""

    x = str(x).strip()

    if x.endswith(".0"):
        x = x[:-2]

    try:
        if "e" in x.lower():
            x = str(int(float(x)))
    except Exception:
        pass

    return x


def find_code_col(df):
    candidates = [
        "admdong_cd",
        "admdong_id",
        "admi_cd",
        "adm_cd",
        "emd_cd",
        "행정동코드",
        "행정동",
        "mc_ad3",
        "mc_ad3_cd",
    ]

    for c in candidates:
        if c in df.columns:
            return c

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
    cols = list(df.columns)

    exclude_keywords = [
        "code", "cd", "id", "dong", "admi", "adm", "emd",
        "date", "dt", "timezn", "time_cd", "year", "month",
        "cell", "xcdn", "ycdn", "x_", "y_", "lon", "lat",
        "시도", "시군구", "행정", "법정", "주소", "지역",
    ]

    if pop_type == "home":
        pop_cols = [
            c for c in cols
            if str(c).startswith("H_")
        ]

    elif pop_type == "work":
        pop_cols = [
            c for c in cols
            if str(c).startswith("W_")
        ]

    elif pop_type == "time_home":
        pop_cols = [
            c for c in cols
            if str(c).startswith("H_")
            or "home_pop" in str(c).lower()
            or "h_pop" in str(c).lower()
        ]

    elif pop_type == "time_work":
        pop_cols = [
            c for c in cols
            if str(c).startswith("W_")
            or "work_pop" in str(c).lower()
            or "w_pop" in str(c).lower()
        ]

    elif pop_type == "inflow":
        include_keywords = [
            "inflow",
            "flow",
            "pop",
            "cnt",
            "인구",
            "유입",
            "방문",
            "유동",
        ]

        pop_cols = []
        for c in cols:
            c_str = str(c).lower()

            if any(ex in c_str for ex in exclude_keywords):
                continue

            if any(key in c_str for key in include_keywords):
                pop_cols.append(c)

        # 그래도 못 찾으면 숫자형 컬럼 중 코드/좌표/날짜 제외
        if not pop_cols:
            for c in cols:
                c_str = str(c).lower()

                if any(ex in c_str for ex in exclude_keywords):
                    continue

                sample = clean_numeric_series(df[c])
                max_val = sample.max()

                # 인구값으로 보기 어려운 거대 코드값 제거
                if 0 < max_val < 10_000_000:
                    pop_cols.append(c)

    else:
        pop_cols = []

    return pop_cols


def sum_population_file(path, pop_type):
    df = read_table_auto(path)

    print(f"\n[인구 파일 읽음] {os.path.basename(path)}")
    print("컬럼:", df.columns.tolist())

    code_col = find_code_col(df)

    if code_col is None:
        print(f"[스킵] {os.path.basename(path)}: 행정동 코드 컬럼 없음")
        return pd.DataFrame(columns=["dong_code", "pop_value"])

    pop_cols = find_population_columns(df, pop_type)

    if len(pop_cols) == 0:
        print(f"[스킵] {os.path.basename(path)}: 인구 수치 컬럼 없음")
        return pd.DataFrame(columns=["dong_code", "pop_value"])

    print("사용한 행정동 코드 컬럼:", code_col)
    print("사용한 인구 컬럼:", pop_cols)

    df["dong_code"] = df[code_col].apply(normalize_dong_code)

    for c in pop_cols:
        df[c] = clean_numeric_series(df[c])

    df["pop_value"] = df[pop_cols].sum(axis=1)

    # 비정상적으로 큰 값 제거
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

    home_file = find_file(folder, "exist_dong_h")
    work_file = find_file(folder, "exist_dong_w")
    time_home_file = find_file(folder, "exist_time_pcell_h")
    time_work_file = find_file(folder, "exist_time_pcell_w")
    inflow_file = find_file(folder, "inflow")

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

    if time_home_file:
        th = (
            sum_population_file(time_home_file, "time_home")
            .rename(columns={"pop_value": "time_home_pop"})
        )
        base = th if base.empty else base.merge(th, on="dong_code", how="outer")

    if time_work_file:
        tw = (
            sum_population_file(time_work_file, "time_work")
            .rename(columns={"pop_value": "time_work_pop"})
        )
        base = tw if base.empty else base.merge(tw, on="dong_code", how="outer")

    if inflow_file:
        inflow = (
            sum_population_file(inflow_file, "inflow")
            .rename(columns={"pop_value": "inflow_pop"})
        )
        base = inflow if base.empty else base.merge(inflow, on="dong_code", how="outer")

    if base.empty:
        return None

    base["year_month"] = ym

    for col in [
        "home_pop",
        "work_pop",
        "time_home_pop",
        "time_work_pop",
        "inflow_pop",
    ]:
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

    cols = [
        "dong_code",
        "year_month",
        "home_pop",
        "work_pop",
        "time_home_pop",
        "time_work_pop",
        "living_pop",
        "time_pop",
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
        avg_living_pop=("living_pop", "mean"),
        avg_work_pop=("work_pop", "mean"),
        avg_time_pop=("time_pop", "mean"),
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