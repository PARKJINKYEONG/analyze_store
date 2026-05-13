import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc


PROJECT_DIR = r"C:\Users\GAENG2\Desktop\analyze_store_main"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")
PPT_DIR = os.path.join(OUT_DIR, "ppt_outputs")

os.makedirs(PPT_DIR, exist_ok=True)

font_path = "C:/Windows/Fonts/malgun.ttf"
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc("font", family=font_name)
plt.rcParams["axes.unicode_minus"] = False


def save_csv(df, filename):
    path = os.path.join(PPT_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print("CSV 저장:", path)


def save_barh(df, x_col, y_col, title, xlabel, filename, value_format="number"):
    temp = df.sort_values(x_col, ascending=True).copy()

    plt.figure(figsize=(10, 6))
    bars = plt.barh(temp[y_col], temp[x_col])

    for bar in bars:
        width = bar.get_width()

        if value_format == "percent":
            label = f"{width:.1f}%"
        elif value_format == "score":
            label = f"{width:.3f}"
        else:
            label = f"{width:,.0f}"

        plt.text(
            width,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            fontsize=8
        )

    plt.title(title, fontsize=15)
    plt.xlabel(xlabel)
    plt.ylabel("")
    plt.tight_layout()

    path = os.path.join(PPT_DIR, filename)
    plt.savefig(path, dpi=250)
    plt.close()

    print("PNG 저장:", path)


def load_data():
    result_path = os.path.join(OUT_DIR, "market_analysis_result_integrated_2023_2024.csv")
    top_path = os.path.join(OUT_DIR, "market_recommendation_top10_integrated_2023_2024.csv")

    if not os.path.exists(result_path):
        raise FileNotFoundError("market_analysis_result_integrated_2023_2024.csv 파일이 없습니다. analyze_market.py를 먼저 실행하세요.")

    if not os.path.exists(top_path):
        raise FileNotFoundError("market_recommendation_top10_integrated_2023_2024.csv 파일이 없습니다. analyze_market.py를 먼저 실행하세요.")

    result = pd.read_csv(result_path, encoding="utf-8-sig")
    top = pd.read_csv(top_path, encoding="utf-8-sig")

    numeric_cols = [
        "total_amount",
        "total_count",
        "total_customer",
        "avg_total_demand_pop",
        "store_count",
        "external_ratio",
        "amount_growth_24_vs_23",
        "sales_shortage",
        "location_score",
        "amount_score",
        "pop_score",
        "growth_score",
        "sales_shortage_score",
        "external_score",
    ]

    for col in numeric_cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0)

    return result, top


def step_01_consumption_size(result):
    df = (
        result.groupby("dong", as_index=False)
        .agg(
            total_amount=("total_amount", "sum"),
            total_count=("total_count", "sum"),
            total_customer=("total_customer", "sum"),
        )
        .sort_values("total_amount", ascending=False)
        .head(10)
    )

    save_csv(df, "PPT_01_행정동별_소비규모_TOP10.csv")
    save_barh(
        df,
        "total_amount",
        "dong",
        "행정동별 총 소비금액 TOP10",
        "총 소비금액",
        "PPT_01_행정동별_소비규모_TOP10.png"
    )


def step_02_external_inflow(result):
    df = (
        result.groupby("dong", as_index=False)
        .agg(
            external_ratio=("external_ratio", "mean"),
            total_amount=("total_amount", "sum"),
        )
        .sort_values("external_ratio", ascending=False)
        .head(10)
    )

    df["external_ratio_percent"] = df["external_ratio"] * 100

    save_csv(df, "PPT_02_외부유입_소비비율_TOP10.csv")
    save_barh(
        df,
        "external_ratio_percent",
        "dong",
        "외부 유입 소비 비율 TOP10",
        "외부 유입 소비 비율(%)",
        "PPT_02_외부유입_소비비율_TOP10.png",
        value_format="percent"
    )


def step_03_growth(result):
    df = (
        result.sort_values("amount_growth_24_vs_23", ascending=False)
        .head(10)
        .copy()
    )

    df["label"] = df["dong"].astype(str) + " - " + df["category"].astype(str)
    df["growth_percent"] = df["amount_growth_24_vs_23"] * 100

    save_csv(
        df[[
            "dong",
            "category",
            "amount_growth_24_vs_23",
            "growth_percent",
            "total_amount"
        ]],
        "PPT_03_소비성장률_TOP10.csv"
    )

    save_barh(
        df,
        "growth_percent",
        "label",
        "2023년 대비 2024년 소비 성장률 TOP10",
        "소비 성장률(%)",
        "PPT_03_소비성장률_TOP10.png",
        value_format="percent"
    )


def step_04_supply_shortage(result):
    df = (
        result.sort_values("sales_shortage", ascending=False)
        .head(10)
        .copy()
    )

    df["label"] = df["dong"].astype(str) + " - " + df["category"].astype(str)

    save_csv(
        df[[
            "dong",
            "category",
            "total_amount",
            "store_count",
            "sales_shortage",
            "sales_shortage_score"
        ]],
        "PPT_04_공급대비_소비부족_TOP10.csv"
    )

    save_barh(
        df,
        "sales_shortage",
        "label",
        "공급 대비 소비 부족 TOP10",
        "소비금액 / 업소 수",
        "PPT_04_공급대비_소비부족_TOP10.png"
    )


def step_05_category_activation(result):
    df = (
        result.groupby("category", as_index=False)
        .agg(
            avg_total_amount=("total_amount", "mean"),
            avg_location_score=("location_score", "mean"),
            total_store_count=("store_count", "sum"),
        )
        .sort_values("avg_location_score", ascending=False)
    )

    save_csv(df, "PPT_05_업종별_상권활성도.csv")

    save_barh(
        df,
        "avg_total_amount",
        "category",
        "업종별 평균 소비금액",
        "평균 소비금액",
        "PPT_05_업종별_평균소비금액.png"
    )

    save_barh(
        df,
        "avg_location_score",
        "category",
        "업종별 평균 입지추천점수",
        "평균 입지추천점수",
        "PPT_05_업종별_평균입지추천점수.png",
        value_format="score"
    )


def step_06_final_recommendation(result, top):
    df = (
        result.sort_values("location_score", ascending=False)
        .head(10)
        .copy()
    )

    df["label"] = df["dong"].astype(str) + " - " + df["category"].astype(str)

    keep_cols = [
        "dong",
        "category",
        "group",
        "location_score",
        "grade",
        "reason",
        "total_amount",
        "avg_total_demand_pop",
        "amount_growth_24_vs_23",
        "external_ratio",
        "sales_shortage",
        "store_count",
    ]

    existing_cols = [c for c in keep_cols if c in df.columns]

    save_csv(df[existing_cols], "PPT_06_최종_입지추천_TOP10.csv")

    save_barh(
        df,
        "location_score",
        "label",
        "최종 입지추천점수 TOP10",
        "입지추천점수",
        "PPT_06_최종_입지추천_TOP10.png",
        value_format="score"
    )

    table_df = (
        top.sort_values(["group", "category", "rank"])
        .groupby(["group", "category"])
        .head(3)
        .copy()
    )

    table_cols = ["group", "category", "rank", "dong", "location_score", "grade", "reason"]
    table_cols = [c for c in table_cols if c in table_df.columns]

    save_csv(table_df[table_cols], "PPT_06_업종별_추천지역_TOP3.csv")


def step_07_map_data(result):
    df = (
        result.groupby("dong", as_index=False)
        .agg(
            total_amount=("total_amount", "sum"),
            total_count=("total_count", "sum"),
            total_customer=("total_customer", "sum"),
            avg_total_demand_pop=("avg_total_demand_pop", "mean"),
            store_count=("store_count", "sum"),
            avg_location_score=("location_score", "mean"),
        )
    )

    df["consumption_activation"] = (
        df["total_amount"] / df["avg_total_demand_pop"].replace(0, pd.NA)
    ).fillna(0)

    df = df.sort_values("avg_location_score", ascending=False)

    save_csv(df, "PPT_07_지도시각화용_행정동요약.csv")


def make_process_summary_csv():
    process_df = pd.DataFrame([
        {
            "분석절차": "1. 행정동별 소비 규모 분석",
            "분석목표": "행정동별 소비금액·소비건수·소비자수 규모 파악",
            "활용데이터": "구미시 소비 데이터, 행정동 코드",
            "사용프로그램": "Python, Pandas, Matplotlib",
            "결과": "소비 규모 상위 행정동 도출"
        },
        {
            "분석절차": "2. 외부 유입 소비 비율 분석",
            "분석목표": "구미 외부지역 소비자의 유입 소비 비중 파악",
            "활용데이터": "외부유입 소비 데이터, 소비금액",
            "사용프로그램": "Python, Pandas, Matplotlib",
            "결과": "외부 유입 소비 비율 상위 지역 도출"
        },
        {
            "분석절차": "3. 소비 성장률 분석",
            "분석목표": "2023년 대비 2024년 소비 증가 지역·업종 파악",
            "활용데이터": "2023~2024 소비금액",
            "사용프로그램": "Python, Pandas, Matplotlib",
            "결과": "소비 성장률 상위 행정동·업종 도출"
        },
        {
            "분석절차": "4. 공급 대비 소비 부족 분석",
            "분석목표": "소비는 높지만 업소 수가 부족한 지역 파악",
            "활용데이터": "소비금액, 업소 수",
            "사용프로그램": "Python, Pandas, Matplotlib",
            "결과": "공급 대비 소비 부족 지역 도출"
        },
        {
            "분석절차": "5. 업종별 상권 활성도 분석",
            "분석목표": "업종별 소비 활성도와 입지 가능성 비교",
            "활용데이터": "업종별 소비금액, 입지추천점수",
            "사용프로그램": "Python, Pandas, Matplotlib",
            "결과": "업종별 평균 소비금액·추천점수 도출"
        },
        {
            "분석절차": "6. 최종 입지추천 점수 산정",
            "분석목표": "소비규모·수요인구·성장성·공급부족·외부유입 종합 평가",
            "활용데이터": "소비, 인구, 유입, 업소 수 데이터",
            "사용프로그램": "Python, Pandas",
            "결과": "최종 추천 행정동 TOP10 도출"
        },
        {
            "분석절차": "7. 최적 입지 지도 시각화",
            "분석목표": "분석 결과를 행정동 지도와 격자 지도에 표현",
            "활용데이터": "행정동 경계 SHP, 소비격자 좌표, 분석결과 CSV",
            "사용프로그램": "Python, GeoPandas, Folium",
            "결과": "PPT용 지도 HTML 생성"
        },
    ])

    save_csv(process_df, "PPT_00_분석절차_요약표.csv")


def main():
    result, top = load_data()

    make_process_summary_csv()

    step_01_consumption_size(result)
    step_02_external_inflow(result)
    step_03_growth(result)
    step_04_supply_shortage(result)
    step_05_category_activation(result)
    step_06_final_recommendation(result, top)
    step_07_map_data(result)

    print("\nPPT용 CSV/PNG 생성 완료")
    print("저장 위치:", PPT_DIR)


if __name__ == "__main__":
    main()