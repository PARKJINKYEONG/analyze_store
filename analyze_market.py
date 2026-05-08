import os
import re
import glob
import numpy as np
import pandas as pd

PROJECT_DIR = "C:\\Users\\A\\Desktop\\Proj\\store analysis"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")
STORE_DIR = os.path.join(PROJECT_DIR, "data", "store")

FOOD_CATEGORIES = ["한식", "중식", "일식", "양식", "패스트푸드"]
CAFE_CATEGORIES = ["커피전문점", "제과점/아이스크림"]
TARGET_CATEGORIES = FOOD_CATEGORIES + CAFE_CATEGORIES


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


def minmax(s):
    s = pd.to_numeric(s, errors="coerce").fillna(0)
    if s.max() == s.min():
        return pd.Series(0, index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def extract_dong(text):
    if pd.isna(text):
        return np.nan
    text = str(text)

    m = re.search(r"\(([^()]*?(동|읍|면))", text)
    if m:
        return m.group(1)

    m = re.search(r"구미시\s+([가-힣0-9]+(?:동|읍|면))", text)
    if m:
        return m.group(1)

    return np.nan

def legal_to_admin_dong(dong):
    if pd.isna(dong):
        return np.nan

    dong = str(dong).strip()

    mapping = {
        # 인동동 관할 법정동 예시
        "인의동": "인동동",
        "황상동": "인동동",
        "구평동": "인동동",

        # 진미동 관할 법정동 예시
        "진평동": "진미동",
        "시미동": "진미동",
        "임수동": "진미동",

        # 선주원남동 주변
        "봉곡동": "선주원남동",
        "부곡동": "선주원남동",
        "원평동": "원평동",
        "남통동": "선주원남동",

        # 상모사곡동
        "상모동": "상모사곡동",
        "사곡동": "상모사곡동",

        # 임오동
        "오태동": "임오동",
        "임은동": "임오동",

        # 양포동
        "옥계동": "양포동",
        "구포동": "양포동",
        "금전동": "양포동",

        # 비산동/공단동 등은 그대로
        "비산동": "비산동",
        "공단동": "공단동",
        "광평동": "광평동",
        "송정동": "송정동",
        "도량동": "도량동",
        "지산동": "지산동",
        "형곡동": "형곡1동",
        
        # 신평동은 법정동이 하나라 신평1/2동 구분이 어려움
        # 우선 신평동 업소를 신평1동으로 임시 배정
        "신평동": "신평동",

        # 형곡동도 법정동 기준이라 형곡1/2동 구분이 어려움
        # 우선 형곡동 업소를 형곡1동으로 임시 배정
        "형곡동": "형곡동",
    }

    return mapping.get(dong, dong)

def classify_store(name):
    text = str(name)

    if any(k in text for k in ["커피", "카페", "스타벅스", "이디야", "메가", "컴포즈", "빽다방", "투썸"]):
        return "커피전문점"
    if any(k in text for k in ["제과", "베이커리", "빵", "아이스크림", "디저트"]):
        return "제과점/아이스크림"
    if any(k in text for k in ["중식", "중화", "짜장", "짬뽕", "마라", "반점"]):
        return "중식"
    if any(k in text for k in ["일식", "스시", "초밥", "라멘", "우동", "돈카츠", "돈까스"]):
        return "일식"
    if any(k in text for k in ["양식", "파스타", "피자", "스테이크", "레스토랑"]):
        return "양식"
    if any(k in text for k in ["햄버거", "버거", "패스트푸드", "맥도날드", "롯데리아", "버거킹"]):
        return "패스트푸드"

    return "한식"


def load_store_supply():
    files = glob.glob(os.path.join(STORE_DIR, "*.csv")) + glob.glob(os.path.join(STORE_DIR, "*.xlsx"))
    frames = []

    for f in files:
        df = read_table_auto(f)

        name_col = next((c for c in ["업소명", "상호명", "사업장명"] if c in df.columns), None)
        addr_col = next((c for c in ["소재지(도로명)", "소재지(지번)", "도로명주소", "주소", "소재지전체주소"] if c in df.columns), None)

        if name_col is None or addr_col is None:
            continue

        temp = pd.DataFrame()
        temp["store_name"] = df[name_col]
        temp["addr"] = df[addr_col]
        temp["legal_dong"] = temp["addr"].apply(extract_dong)
        temp["dong"] = temp["legal_dong"].apply(legal_to_admin_dong)

        file_name = os.path.basename(f)
        if "카페" in file_name or "휴게" in file_name:
            temp["category"] = "커피전문점"
        else:
            temp["category"] = temp["store_name"].apply(classify_store)

        frames.append(temp)

    stores = pd.concat(frames, ignore_index=True)
    stores = stores.dropna(subset=["dong"])
    stores = stores[stores["category"].isin(TARGET_CATEGORIES)].copy()

    supply = stores.groupby(["dong", "category"], as_index=False).agg(
        store_count=("store_name", "count")
    )

    split_rows = []

    for _, row in supply.iterrows():
        dong = row["dong"]

        # 소비 비율 기반 분배
        split_ratio = {
            "신평동": {
                "신평1동": 0.45,
                "신평2동": 0.55,
            },
            "형곡동": {
            "형곡1동": 0.45,
            "형곡2동": 0.55,
        }
    }

    split_rows = []

    for _, row in supply.iterrows():
        dong = row["dong"]

        if dong in split_ratio:
            for target, ratio in split_ratio[dong].items():
                new_row = row.copy()
                new_row["dong"] = target
                new_row["store_count"] = row["store_count"] * ratio
                split_rows.append(new_row)
        else:
            split_rows.append(row)

    supply = pd.DataFrame(split_rows)

    supply = supply.groupby(["dong", "category"], as_index=False).agg(
        store_count=("store_count", "sum")
    )


    # ---------------------------------------------------------
    # 법정동이 행정동 1/2동으로 나뉘는 경우 보정
    # 신평동, 형곡동 업소를 각각 1동/2동에 균등 배분
    # ---------------------------------------------------------

    split_rows = []

    for _, row in supply.iterrows():
        dong = row["dong"]

        if dong == "신평동":
            for target in ["신평1동", "신평2동"]:
                new_row = row.copy()
                new_row["dong"] = target
                new_row["store_count"] = row["store_count"] / 2
                split_rows.append(new_row)

        elif dong == "형곡동":
            for target in ["형곡1동", "형곡2동"]:
                new_row = row.copy()
                new_row["dong"] = target
                new_row["store_count"] = row["store_count"] / 2
                split_rows.append(new_row)

        else:
            split_rows.append(row)

    supply = pd.DataFrame(split_rows)

    supply = supply.groupby(["dong", "category"], as_index=False).agg(
        store_count=("store_count", "sum")
    )

    stores.to_csv(os.path.join(OUT_DIR, "store_classified.csv"), index=False, encoding="utf-8-sig")
    supply.to_csv(os.path.join(OUT_DIR, "store_supply.csv"), index=False, encoding="utf-8-sig")

    return supply


def calc_growth(consume):
    temp = consume.copy()
    temp["year"] = temp["year_month"].astype(str).str[:4]

    yearly = temp.groupby(["dong_code", "dong", "category", "year"], as_index=False)["amount"].sum()

    pivot = yearly.pivot_table(
        index=["dong_code", "dong", "category"],
        columns="year",
        values="amount",
        fill_value=0
    ).reset_index()

    if "2023" not in pivot.columns:
        pivot["2023"] = 0
    if "2024" not in pivot.columns:
        pivot["2024"] = 0

    pivot["amount_growth_24_vs_23"] = (
        (pivot["2024"] - pivot["2023"]) / pivot["2023"].replace(0, np.nan)
    ).replace([np.inf, -np.inf], np.nan).fillna(0)

    return pivot[["dong_code", "dong", "category", "amount_growth_24_vs_23"]]


def make_pop_summary(pop, consume, year=None):
    temp = pop.copy()

    if year is not None:
        temp = temp[temp["year_month"].astype(str).str.startswith(str(year))].copy()

    pop_summary = temp.groupby("dong_code", as_index=False).agg(
        avg_living_pop=("living_pop", "mean"),
        avg_work_pop=("work_pop", "mean"),
        avg_time_pop=("time_pop", "mean"),
        avg_inflow_pop=("inflow_pop", "mean"),
        avg_total_demand_pop=("total_demand_pop", "mean")
    )

    dong_name_map = consume[["dong_code", "dong"]].drop_duplicates()
    pop_summary = pop_summary.merge(dong_name_map, on="dong_code", how="left")

    return pop_summary


def make_inflow_summary(inflow, year=None):
    if inflow.empty:
        return pd.DataFrame(columns=["dong_code", "dong", "category", "external_ratio"])

    temp = inflow.copy()

    if year is not None:
        temp = temp[temp["year_month"].astype(str).str.startswith(str(year))].copy()

    if temp.empty:
        return pd.DataFrame(columns=["dong_code", "dong", "category", "external_ratio"])

    return temp.groupby(["dong_code", "dong", "category"], as_index=False).agg(
        external_ratio=("external_ratio", "mean")
    )


def score_market(base, use_growth=True):
    fill_cols = [
        "total_amount", "avg_monthly_amount", "total_count", "total_customer",
        "amount_growth_24_vs_23", "avg_living_pop", "avg_work_pop",
        "avg_time_pop", "avg_inflow_pop", "avg_total_demand_pop",
        "external_ratio", "store_count"
    ]

    for c in fill_cols:
        if c not in base.columns:
            base[c] = 0

    base[fill_cols] = base[fill_cols].fillna(0)

    if not use_growth:
        base["amount_growth_24_vs_23"] = 0

    base["group"] = base["category"].apply(
        lambda x: "카페" if x in CAFE_CATEGORIES else "음식점"
    )

    base["store_count_adj"] = base["store_count"].replace(0, 0.5)

    base["pop_shortage"] = base["avg_total_demand_pop"] / base["store_count_adj"]
    base["sales_shortage"] = base["total_amount"] / base["store_count_adj"]
    base["count_shortage"] = base["total_count"] / base["store_count_adj"]

    base["pop_score"] = minmax(base["avg_total_demand_pop"])
    base["amount_score"] = minmax(base["total_amount"])
    base["count_score"] = minmax(base["total_count"])
    base["customer_score"] = minmax(base["total_customer"])
    base["growth_score"] = minmax(base["amount_growth_24_vs_23"])
    base["external_score"] = minmax(base["external_ratio"])
    base["pop_shortage_score"] = minmax(base["pop_shortage"])
    base["sales_shortage_score"] = minmax(base["sales_shortage"])
    base["competition_score"] = minmax(base["store_count"])

    if use_growth:
        base["location_score"] = (
            base["pop_score"] * 0.18
            + base["amount_score"] * 0.25
            + base["count_score"] * 0.10
            + base["customer_score"] * 0.08
            + base["growth_score"] * 0.12
            + base["external_score"] * 0.05
            + base["pop_shortage_score"] * 0.10
            + base["sales_shortage_score"] * 0.12
            - base["competition_score"] * 0.10
        )
    else:
        base["location_score"] = (
            base["pop_score"] * 0.22
            + base["amount_score"] * 0.28
            + base["count_score"] * 0.12
            + base["customer_score"] * 0.10
            + base["external_score"] * 0.05
            + base["pop_shortage_score"] * 0.11
            + base["sales_shortage_score"] * 0.12
            - base["competition_score"] * 0.10
        )

    base["location_score"] = base["location_score"].round(4)

    def grade(x):
        if x >= 0.75:
            return "매우 추천"
        if x >= 0.55:
            return "추천"
        if x >= 0.35:
            return "검토 가능"
        return "낮음"

    def reason(row):
        r = []
        if row["pop_score"] >= 0.6:
            r.append("유동/생활인구 높음")
        if row["amount_score"] >= 0.6:
            r.append("소비금액 높음")
        if use_growth and row["growth_score"] >= 0.6:
            r.append("2024년 소비 성장")
        if row["sales_shortage_score"] >= 0.6:
            r.append("소비 대비 공급 부족")
        if row["competition_score"] <= 0.3:
            r.append("경쟁 업소 적음")
        return " + ".join(r) if r else "특징 약함"

    base["grade"] = base["location_score"].apply(grade)
    base["reason"] = base.apply(reason, axis=1)

    return base


def make_top(base):
    top = (
        base.sort_values(["group", "category", "location_score"], ascending=[True, True, False])
        .groupby(["group", "category"])
        .head(10)
        .copy()
    )

    top["rank"] = top.groupby(["group", "category"])["location_score"].rank(
        method="first", ascending=False
    ).astype(int)

    return top


def analyze_by_year(year, pop, consume, inflow, supply):
    year_consume = consume[consume["year_month"].astype(str).str.startswith(str(year))].copy()

    consume_summary = year_consume.groupby(["dong_code", "dong", "category"], as_index=False).agg(
        total_amount=("amount", "sum"),
        avg_monthly_amount=("amount", "mean"),
        total_count=("count", "sum"),
        total_customer=("customer", "sum")
    )

    pop_summary = make_pop_summary(pop, consume, year=year)
    inflow_summary = make_inflow_summary(inflow, year=year)

    base = consume_summary.merge(pop_summary, on=["dong_code", "dong"], how="left")
    base = base.merge(inflow_summary, on=["dong_code", "dong", "category"], how="left")
    base = base.merge(supply, on=["dong", "category"], how="left")

    base = score_market(base, use_growth=False)
    top = make_top(base)

    base.to_csv(os.path.join(OUT_DIR, f"market_analysis_result_{year}.csv"), index=False, encoding="utf-8-sig")
    top.to_csv(os.path.join(OUT_DIR, f"market_recommendation_top10_{year}.csv"), index=False, encoding="utf-8-sig")

    base[base["group"] == "음식점"].to_csv(os.path.join(OUT_DIR, f"market_analysis_food_{year}.csv"), index=False, encoding="utf-8-sig")
    base[base["group"] == "카페"].to_csv(os.path.join(OUT_DIR, f"market_analysis_cafe_{year}.csv"), index=False, encoding="utf-8-sig")

    top[top["group"] == "음식점"].to_csv(os.path.join(OUT_DIR, f"market_recommendation_food_top10_{year}.csv"), index=False, encoding="utf-8-sig")
    top[top["group"] == "카페"].to_csv(os.path.join(OUT_DIR, f"market_recommendation_cafe_top10_{year}.csv"), index=False, encoding="utf-8-sig")

    return base, top


def analyze_integrated(pop, consume, inflow, supply):
    consume_summary = consume.groupby(["dong_code", "dong", "category"], as_index=False).agg(
        total_amount=("amount", "sum"),
        avg_monthly_amount=("amount", "mean"),
        total_count=("count", "sum"),
        total_customer=("customer", "sum")
    )

    growth = calc_growth(consume)
    pop_summary = make_pop_summary(pop, consume, year=None)
    inflow_summary = make_inflow_summary(inflow, year=None)

    base = consume_summary.merge(growth, on=["dong_code", "dong", "category"], how="left")
    base = base.merge(pop_summary, on=["dong_code", "dong"], how="left")
    base = base.merge(inflow_summary, on=["dong_code", "dong", "category"], how="left")
    base = base.merge(supply, on=["dong", "category"], how="left")

    base = score_market(base, use_growth=True)
    top = make_top(base)

    base.to_csv(os.path.join(OUT_DIR, "market_analysis_result_integrated_2023_2024.csv"), index=False, encoding="utf-8-sig")
    top.to_csv(os.path.join(OUT_DIR, "market_recommendation_top10_integrated_2023_2024.csv"), index=False, encoding="utf-8-sig")

    base[base["group"] == "음식점"].to_csv(os.path.join(OUT_DIR, "market_analysis_food_integrated_2023_2024.csv"), index=False, encoding="utf-8-sig")
    base[base["group"] == "카페"].to_csv(os.path.join(OUT_DIR, "market_analysis_cafe_integrated_2023_2024.csv"), index=False, encoding="utf-8-sig")

    top[top["group"] == "음식점"].to_csv(os.path.join(OUT_DIR, "market_recommendation_food_top10_integrated_2023_2024.csv"), index=False, encoding="utf-8-sig")
    top[top["group"] == "카페"].to_csv(os.path.join(OUT_DIR, "market_recommendation_cafe_top10_integrated_2023_2024.csv"), index=False, encoding="utf-8-sig")

    return base, top


def main():
    pop = pd.read_csv(os.path.join(OUT_DIR, "population_monthly.csv"), encoding="utf-8-sig")
    consume = pd.read_csv(os.path.join(OUT_DIR, "consumption_monthly_dong.csv"), encoding="utf-8-sig")

    consume = consume[consume["category"].isin(TARGET_CATEGORIES)].copy()

    inflow_path = os.path.join(OUT_DIR, "consumption_inflow_summary.csv")
    if os.path.exists(inflow_path):
        inflow = pd.read_csv(inflow_path, encoding="utf-8-sig")
        inflow = inflow[inflow["category"].isin(TARGET_CATEGORIES)].copy()
    else:
        inflow = pd.DataFrame(columns=["year_month", "dong_code", "dong", "category", "external_ratio"])

    supply = load_store_supply()

    print("2023년 분석 중...")
    analyze_by_year(2023, pop, consume, inflow, supply)

    print("2024년 분석 중...")
    analyze_by_year(2024, pop, consume, inflow, supply)

    print("2023~2024 통합 최종 입지추천 분석 중...")
    analyze_integrated(pop, consume, inflow, supply)

    print("상권 분석 완료")


if __name__ == "__main__":
    main()