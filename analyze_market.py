import os
import numpy as np
import pandas as pd


PROJECT_DIR = r"C:\Users\Gaeng2\Desktop\Proj\store analysis"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")
STORE_DIR = os.path.join(PROJECT_DIR, "data", "store")

FOOD_CATEGORIES = ["한식", "중식", "일식", "양식", "패스트푸드"]
CAFE_CATEGORIES = ["커피전문점", "제과점/아이스크림"]
TARGET_CATEGORIES = FOOD_CATEGORIES + CAFE_CATEGORIES


def minmax(s):
    s = pd.to_numeric(s, errors="coerce").fillna(0)
    if s.max() == s.min():
        return pd.Series(0, index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def load_store_supply():

    final_supply_path = os.path.join(
        OUT_DIR,
        "store_supply.csv"
    )

    if not os.path.exists(final_supply_path):
        raise FileNotFoundError(
            "store_supply.csv 파일이 없습니다."
        )

    supply = pd.read_csv(
        final_supply_path,
        encoding="utf-8-sig"
    )

    supply["dong"] = (
        supply["dong"]
        .astype(str)
        .str.strip()
    )

    supply["category"] = (
        supply["category"]
        .astype(str)
        .str.strip()
    )

    supply["store_count"] = pd.to_numeric(
        supply["store_count"],
        errors="coerce"
    ).fillna(0)

    supply = supply[
        supply["category"].isin(TARGET_CATEGORIES)
    ].copy()

    supply = supply.drop_duplicates(
        subset=["dong", "category"]
    )

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
    
    # ---------------------------------------------------------
    # 필요한 컬럼 보정
    # ---------------------------------------------------------

    fill_cols = [
        "total_amount",
        "avg_monthly_amount",
        "total_count",
        "total_customer",
        "amount_growth_24_vs_23",
        "avg_living_pop",
        "avg_work_pop",
        "avg_inflow_pop",
        "avg_total_demand_pop",
        "external_ratio",
        "store_count"
    ]

    for c in fill_cols:
        if c not in base.columns:
            base[c] = 0

    base[fill_cols] = base[fill_cols].fillna(0)

    # ---------------------------------------------------------
    # 성장률 미사용 시 제거
    # ---------------------------------------------------------

    if not use_growth:
        base["amount_growth_24_vs_23"] = 0

    # ---------------------------------------------------------
    # 그룹 구분
    # ---------------------------------------------------------

    base["group"] = base["category"].apply(
        lambda x: "카페" if x in CAFE_CATEGORIES else "음식점"
    )

    base["store_count"] = (
        pd.to_numeric(base["store_count"], errors="coerce")
        .fillna(0)
    )

    base["store_count_adj"] = (
        base["store_count"]
        .replace(0, 0.5)
    )

    # ---------------------------------------------------------
    # 공급 부족도 계산
    # ---------------------------------------------------------

    # 소비 대비 공급 부족
    base["sales_shortage"] = (
        base["total_amount"] / base["store_count_adj"]
    )

    # 인구 대비 공급 부족
    base["pop_shortage"] = (
        base["avg_total_demand_pop"] / base["store_count_adj"]
    )

    # ---------------------------------------------------------
    # 정규화 점수
    # ---------------------------------------------------------

    # 소비 규모
    base["amount_score"] = minmax(base["total_amount"])

    # 수요 인구
    base["pop_score"] = minmax(base["avg_total_demand_pop"])

    # 성장성
    base["growth_score"] = minmax(base["amount_growth_24_vs_23"])

    # 외부 유입
    base["external_score"] = minmax(base["external_ratio"])

    # 공급 부족도
    base["sales_shortage_score"] = minmax(base["sales_shortage"])

    # ---------------------------------------------------------
    # 최종 입지추천점수
    # ---------------------------------------------------------
    # 총합 = 1.00
    #
    # 소비규모        35%
    # 수요인구        25%
    # 성장성          15%
    # 공급부족        15%
    # 외부유입        10%
    # ---------------------------------------------------------

    if use_growth:

        base["location_score"] = (

            # 소비규모
            base["amount_score"] * 0.35

            # 수요인구
            + base["pop_score"] * 0.25

            # 성장성
            + base["growth_score"] * 0.15

            # 공급 부족도
            + base["sales_shortage_score"] * 0.15

            # 외부 유입
            + base["external_score"] * 0.10
        )

    else:

        # 연도별 단독 분석 시 성장률 제외
        # 총합 = 1.00

        base["location_score"] = (

            # 소비규모
            base["amount_score"] * 0.45

            # 수요인구
            + base["pop_score"] * 0.30

            # 공급 부족도
            + base["sales_shortage_score"] * 0.15

            # 외부 유입
            + base["external_score"] * 0.10
        )

    # ---------------------------------------------------------
    # 반올림
    # ---------------------------------------------------------

    base["location_score"] = (
        base["location_score"]
        .round(4)
    )

    # ---------------------------------------------------------
    # 추천 등급
    # ---------------------------------------------------------

    def grade(x):

        if x >= 0.75:
            return "매우 추천"

        elif x >= 0.55:
            return "추천"

        elif x >= 0.35:
            return "검토 가능"

        else:
            return "낮음"

    # ---------------------------------------------------------
    # 추천 사유
    # ---------------------------------------------------------

    def reason(row):

        r = []

        # 소비 규모
        if row["amount_score"] >= 0.6:
            r.append("소비 규모 높음")

        # 수요 인구
        if row["pop_score"] >= 0.6:
            r.append("수요인구 높음")

        # 성장성
        if use_growth and row["growth_score"] >= 0.6:
            r.append("소비 성장률 높음")

        # 공급 부족
        if row["sales_shortage_score"] >= 0.6:
            r.append("공급 대비 소비 부족")

        # 외부 유입
        if row["external_score"] >= 0.6:
            r.append("외부 유입 소비 높음")

        if len(r) == 0:
            return "특징 약함"

        return " + ".join(r)

    # ---------------------------------------------------------
    # 최종 컬럼 생성
    # ---------------------------------------------------------

    base["grade"] = (
        base["location_score"]
        .apply(grade)
    )

    base["reason"] = (
        base.apply(reason, axis=1)
    )

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

    consume_summary["dong"] = consume_summary["dong"].astype(str).str.strip()
    consume_summary["category"] = consume_summary["category"].astype(str).str.strip()

    supply["dong"] = supply["dong"].astype(str).str.strip()
    supply["category"] = supply["category"].astype(str).str.strip()

    base = consume_summary.merge(growth, on=["dong_code", "dong", "category"], how="left")
    base = base.merge(pop_summary, on=["dong_code", "dong"], how="left")
    base = base.merge(inflow_summary, on=["dong_code", "dong", "category"], how="left")
    base = base.merge(supply, on=["dong", "category"], how="left")


    base["store_count"] = pd.to_numeric(
        base["store_count"],
        errors="coerce"
    ).fillna(0)

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