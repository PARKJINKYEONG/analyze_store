import os
import re
import glob
import numpy as np
import pandas as pd

BASE_DIR = "C:\\Users\\A\\Desktop\\데이터"
CONSUME_ROOT = os.path.join(BASE_DIR, "구미 소비데이터")

PROJECT_DIR = "C:\\Users\\A\\Desktop\\Proj\\store analysis"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")
os.makedirs(OUT_DIR, exist_ok=True)

YEARS = [2023, 2024]

TARGET_CATEGORIES = [
    "한식", "중식", "일식", "양식", "패스트푸드",
    "기타음식점", "뷔페", "커피전문점", "제과점/아이스크림"
]


def read_table_auto(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    for enc in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=enc)
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
        year_dir = os.path.join(CONSUME_ROOT, f"{year}년")
        folders.extend(glob.glob(os.path.join(year_dir, f"{year}_*월_소비")))
    return sorted(folders)


def classify_category(row):
    b1 = str(row.get("mc_bzc1_nm", ""))
    b2 = str(row.get("mc_bzc2_nm", ""))
    b3 = str(row.get("mc_bzc3_nm", ""))

    text = f"{b1} {b2} {b3}"

    if "한식" in text:
        return "한식"
    if "중식" in text:
        return "중식"
    if "일식" in text:
        return "일식"
    if "양식" in text:
        return "양식"
    if "패스트푸드" in text:
        return "패스트푸드"
    if "기타음식점" in text or "기타 음식" in text:
        return "기타음식점"
    if "뷔페" in text:
        return "뷔페"
    if "커피전문점" in text or "커피" in text:
        return "커피전문점"
    if "제과점" in text or "아이스크림" in text or "제과" in text:
        return "제과점/아이스크림"

    return "제외"


def find_amount_col(df):
    for c in ["us_am", "이용금액", "사용금액", "소비금액", "lc_us_am"]:
        if c in df.columns:
            return c
    return None


def find_count_col(df):
    for c in ["us_cnt", "이용건수", "사용건수", "lc_us_cnt"]:
        if c in df.columns:
            return c
    return None


def find_customer_col(df):
    for c in ["cust_cnt", "이용자수", "고객수", "lc_cst_cnt"]:
        if c in df.columns:
            return c
    return None


def preprocess_main_consumption(folder):
    ym = ym_from_folder(folder)
    files = glob.glob(os.path.join(folder, "*DD_R_2*"))

    frames = []

    for f in files:
        if "DD2" in os.path.basename(f):
            continue

        df = read_table_auto(f)

        amount_col = find_amount_col(df)
        count_col = find_count_col(df)
        customer_col = find_customer_col(df)

        if amount_col is None:
            continue

        df["category"] = df.apply(classify_category, axis=1)
        df = df[df["category"].isin(TARGET_CATEGORIES)].copy()

        if df.empty:
            continue

        df["year_month"] = ym
        df["dong_code"] = df["mc_ad3"].astype(str) if "mc_ad3" in df.columns else ""
        df["dong"] = df["mc_ad3_nm"] if "mc_ad3_nm" in df.columns else df["dong_code"]

        df["amount"] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)
        df["count"] = pd.to_numeric(df[count_col], errors="coerce").fillna(0) if count_col else 0
        df["customer"] = pd.to_numeric(df[customer_col], errors="coerce").fillna(0) if customer_col else 0

        if "cell_id" not in df.columns:
            df["cell_id"] = np.nan
        if "xcdn" not in df.columns:
            df["xcdn"] = np.nan
        if "ycdn" not in df.columns:
            df["ycdn"] = np.nan

        frames.append(df[[
            "year_month", "dong_code", "dong", "cell_id", "xcdn", "ycdn",
            "category", "amount", "count", "customer"
        ]])

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def preprocess_age_consumption(folder):
    ym = ym_from_folder(folder)
    files = glob.glob(os.path.join(folder, "*DD_R_4*"))

    frames = []

    for f in files:
        if "DD2" in os.path.basename(f):
            continue

        df = read_table_auto(f)

        amount_col = find_amount_col(df)
        count_col = find_count_col(df)
        customer_col = find_customer_col(df)

        if amount_col is None:
            continue

        df["category"] = df.apply(classify_category, axis=1)
        df = df[df["category"].isin(TARGET_CATEGORIES)].copy()

        if df.empty:
            continue

        df["year_month"] = ym
        df["dong_code"] = df["mc_ad3"].astype(str) if "mc_ad3" in df.columns else ""
        df["dong"] = df["mc_ad3_nm"] if "mc_ad3_nm" in df.columns else df["dong_code"]
        df["sex"] = df["cst_sex"] if "cst_sex" in df.columns else np.nan
        df["age"] = df["cat_age"] if "cat_age" in df.columns else np.nan

        df["amount"] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)
        df["count"] = pd.to_numeric(df[count_col], errors="coerce").fillna(0) if count_col else 0
        df["customer"] = pd.to_numeric(df[customer_col], errors="coerce").fillna(0) if customer_col else 0

        frames.append(df[[
            "year_month", "dong_code", "dong", "category",
            "sex", "age", "amount", "count", "customer"
        ]])

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def preprocess_inflow_consumption(folder):
    ym = ym_from_folder(folder)
    files = glob.glob(os.path.join(folder, "*DD2_R_3*")) + glob.glob(os.path.join(folder, "*DD_R_3*"))

    frames = []

    for f in files:
        df = read_table_auto(f)

        amount_col = find_amount_col(df)
        count_col = find_count_col(df)
        customer_col = find_customer_col(df)

        if amount_col is None:
            continue

        df["category"] = df.apply(classify_category, axis=1)
        df = df[df["category"].isin(TARGET_CATEGORIES)].copy()

        if df.empty:
            continue

        df["year_month"] = ym
        df["dong_code"] = df["mc_ad3"].astype(str) if "mc_ad3" in df.columns else ""
        df["dong"] = df["mc_ad3_nm"] if "mc_ad3_nm" in df.columns else df["dong_code"]

        df["customer_region"] = ""
        if "cst_ad_g2" in df.columns:
            df["customer_region"] = df["cst_ad_g2"].astype(str)
        elif "cst_ad_g" in df.columns:
            df["customer_region"] = df["cst_ad_g"].astype(str)

        df["amount"] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)
        df["count"] = pd.to_numeric(df[count_col], errors="coerce").fillna(0) if count_col else 0
        df["customer"] = pd.to_numeric(df[customer_col], errors="coerce").fillna(0) if customer_col else 0

        df["is_external"] = ~df["customer_region"].str.contains("구미|01_구미시", na=False)

        frames.append(df[[
            "year_month", "dong_code", "dong", "category",
            "customer_region", "is_external", "amount", "count", "customer"
        ]])

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def main():
    main_frames = []
    age_frames = []
    inflow_frames = []

    for folder in get_month_folders():
        print("처리 중:", folder)

        main_df = preprocess_main_consumption(folder)
        if not main_df.empty:
            main_frames.append(main_df)

        age_df = preprocess_age_consumption(folder)
        if not age_df.empty:
            age_frames.append(age_df)

        inflow_df = preprocess_inflow_consumption(folder)
        if not inflow_df.empty:
            inflow_frames.append(inflow_df)

    consume = pd.concat(main_frames, ignore_index=True)
    consume.to_csv(os.path.join(OUT_DIR, "consumption_monthly_cell.csv"), index=False, encoding="utf-8-sig")

    dong_monthly = consume.groupby(
        ["year_month", "dong_code", "dong", "category"],
        as_index=False
    ).agg(
        amount=("amount", "sum"),
        count=("count", "sum"),
        customer=("customer", "sum")
    )
    dong_monthly.to_csv(os.path.join(OUT_DIR, "consumption_monthly_dong.csv"), index=False, encoding="utf-8-sig")

    if age_frames:
        age = pd.concat(age_frames, ignore_index=True)
        age.to_csv(os.path.join(OUT_DIR, "consumption_age_gender.csv"), index=False, encoding="utf-8-sig")

    if inflow_frames:
        inflow = pd.concat(inflow_frames, ignore_index=True)
        inflow.to_csv(os.path.join(OUT_DIR, "consumption_inflow.csv"), index=False, encoding="utf-8-sig")

        inflow_summary = inflow.groupby(
            ["year_month", "dong_code", "dong", "category"],
            as_index=False
        ).agg(
            external_amount=("amount", lambda x: x[inflow.loc[x.index, "is_external"]].sum()),
            total_amount=("amount", "sum")
        )
        inflow_summary["external_ratio"] = (
            inflow_summary["external_amount"] / inflow_summary["total_amount"].replace(0, np.nan)
        ).fillna(0)

        inflow_summary.to_csv(os.path.join(OUT_DIR, "consumption_inflow_summary.csv"), index=False, encoding="utf-8-sig")

    print("소비 전처리 완료")


if __name__ == "__main__":
    main()