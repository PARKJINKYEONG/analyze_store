import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

PROJECT_DIR = r"C:\Users\GAENG2\Desktop\analyze_store_main"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")
VIZ_DIR = os.path.join(OUT_DIR, "visuals")
os.makedirs(VIZ_DIR, exist_ok=True)

font_path = "C:/Windows/Fonts/malgun.ttf"
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc("font", family=font_name)
plt.rcParams["axes.unicode_minus"] = False

FOOD_CATEGORIES = ["한식", "중식", "일식", "양식", "패스트푸드"]
CAFE_CATEGORIES = ["커피전문점", "제과점/아이스크림"]


def safe_name(text):
    return str(text).replace("/", "_").replace("\\", "_")


def save_barh(df, x, y, title, xlabel, filename):
    temp = df.sort_values(x, ascending=True)

    plt.figure(figsize=(10, 6))
    bars = plt.barh(temp[y], temp[x])

    for bar in bars:
        width = bar.get_width()
        plt.text(
            width,
            bar.get_y() + bar.get_height() / 2,
            f"{width:,.0f}",
            va="center",
            fontsize=8
        )

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("행정동")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, filename), dpi=250)
    plt.close()


def save_barh_percent(df, x, y, title, xlabel, filename):
    temp = df.sort_values(x, ascending=True)

    plt.figure(figsize=(10, 6))
    bars = plt.barh(temp[y], temp[x])

    for bar in bars:
        width = bar.get_width()
        plt.text(
            width,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.1f}%",
            va="center",
            fontsize=8
        )

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("행정동")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, filename), dpi=250)
    plt.close()


def visualize_year(year):
    result_file = os.path.join(OUT_DIR, f"market_analysis_result_{year}.csv")
    top_file = os.path.join(OUT_DIR, f"market_recommendation_top10_{year}.csv")

    if not os.path.exists(result_file) or not os.path.exists(top_file):
        print(f"{year}년 결과 파일 없음. 건너뜀.")
        return

    result = pd.read_csv(result_file, encoding="utf-8-sig")
    top = pd.read_csv(top_file, encoding="utf-8-sig")

    # 1. 음식점/카페 소비금액 TOP10
    for group in ["음식점", "카페"]:
        temp = (
            result[result["group"] == group]
            .groupby("dong", as_index=False)["total_amount"]
            .sum()
            .sort_values("total_amount", ascending=False)
            .head(10)
        )

        save_barh(
            temp,
            "total_amount",
            "dong",
            f"{year}년 {group} 소비금액 TOP10",
            "소비금액",
            f"{year}_01_{group}_소비금액_TOP10.png"
        )

    # 2. 음식점/카페 평균 수요인구 TOP10
    for group in ["음식점", "카페"]:
        temp = (
            result[result["group"] == group]
            .drop_duplicates("dong")
            .sort_values("avg_total_demand_pop", ascending=False)
            .head(10)
        )

        save_barh(
            temp,
            "avg_total_demand_pop",
            "dong",
            f"{year}년 {group} 평균 수요인구 TOP10",
            "평균 수요인구",
            f"{year}_02_{group}_평균수요인구_TOP10.png"
        )

    # 3. 입지추천점수 히트맵
    for group in ["음식점", "카페"]:
        temp = result[result["group"] == group].copy()

        pivot = temp.pivot_table(
            index="dong",
            columns="category",
            values="location_score",
            fill_value=0
        )

        pivot["평균"] = pivot.mean(axis=1)
        pivot = pivot.sort_values("평균", ascending=False).drop(columns="평균").head(20)

        plt.figure(figsize=(12, 8))
        plt.imshow(pivot.values, aspect="auto")
        plt.colorbar(label="입지추천점수")
        plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45)
        plt.yticks(range(len(pivot.index)), pivot.index)
        plt.title(f"{year}년 {group} 행정동별 입지추천점수")
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, f"{year}_03_{group}_입지추천점수_히트맵.png"), dpi=250)
        plt.close()

    # 4. 소비 대비 공급 부족도 히트맵
    for group in ["음식점", "카페"]:
        temp = result[result["group"] == group].copy()

        pivot = temp.pivot_table(
            index="dong",
            columns="category",
            values="sales_shortage",
            fill_value=0
        )

        pivot["평균"] = pivot.mean(axis=1)
        pivot = pivot.sort_values("평균", ascending=False).drop(columns="평균").head(20)

        plt.figure(figsize=(12, 8))
        plt.imshow(pivot.values, aspect="auto")
        plt.colorbar(label="소비 대비 공급 부족도")
        plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45)
        plt.yticks(range(len(pivot.index)), pivot.index)
        plt.title(f"{year}년 {group} 소비 대비 공급 부족도")
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, f"{year}_04_{group}_소비대비공급부족도_히트맵.png"), dpi=250)
        plt.close()

    # 5. 업종별 추천 TOP5
    for cat in top["category"].unique():
        temp = (
            top[top["category"] == cat]
            .sort_values("location_score", ascending=False)
            .head(5)
            .sort_values("location_score", ascending=True)
        )

        plt.figure(figsize=(9, 5))
        bars = plt.barh(temp["dong"], temp["location_score"])

        for bar in bars:
            width = bar.get_width()
            plt.text(
                width,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.3f}",
                va="center",
                fontsize=8
            )

        plt.title(f"{year}년 {cat} 신규 입지 추천 TOP5")
        plt.xlabel("입지추천점수")
        plt.ylabel("행정동")
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, f"{year}_05_{safe_name(cat)}_추천_TOP5.png"), dpi=250)
        plt.close()

    # 6. 최종 추천표 이미지
    final_table = (
        top.sort_values(["group", "category", "rank"])
        .groupby(["group", "category"])
        .head(3)
    )

    final_table = final_table[["group", "category", "rank", "dong", "location_score", "grade", "reason"]]

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.axis("off")

    table = ax.table(
        cellText=final_table.values,
        colLabels=final_table.columns,
        loc="center",
        cellLoc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.6)

    plt.title(f"{year}년 업종별 추천 행정동 TOP3", fontsize=16, pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, f"{year}_06_업종별_추천표_TOP3.png"), dpi=250)
    plt.close()


def visualize_integrated():
    result_path = os.path.join(OUT_DIR, "market_analysis_result_integrated_2023_2024.csv")
    top_path = os.path.join(OUT_DIR, "market_recommendation_top10_integrated_2023_2024.csv")

    result = pd.read_csv(result_path, encoding="utf-8-sig")
    top = pd.read_csv(top_path, encoding="utf-8-sig")

    # =====================================================
    # 1. 행정동별 소비 규모 분석
    # =====================================================

    dong_amount = (
        result.groupby("dong", as_index=False)["total_amount"]
        .sum()
        .sort_values("total_amount", ascending=False)
        .head(10)
    )

    save_barh(
        dong_amount,
        "total_amount",
        "dong",
        "행정동별 총 소비금액 TOP10",
        "총 소비금액",
        "PPT_01_행정동별_총소비금액_TOP10.png"
    )

    dong_count = (
        result.groupby("dong", as_index=False)["total_count"]
        .sum()
        .sort_values("total_count", ascending=False)
        .head(10)
    )

    save_barh(
        dong_count,
        "total_count",
        "dong",
        "행정동별 소비건수 TOP10",
        "소비건수",
        "PPT_01_행정동별_소비건수_TOP10.png"
    )

    dong_customer = (
        result.groupby("dong", as_index=False)["total_customer"]
        .sum()
        .sort_values("total_customer", ascending=False)
        .head(10)
    )

    save_barh(
        dong_customer,
        "total_customer",
        "dong",
        "행정동별 소비자수 TOP10",
        "소비자수",
        "PPT_01_행정동별_소비자수_TOP10.png"
    )

    # =====================================================
    # 2. 외부 유입 소비 비율 분석
    # =====================================================

    external_top = (
        result.groupby("dong", as_index=False)["external_ratio"]
        .mean()
        .sort_values("external_ratio", ascending=False)
        .head(10)
    )

    external_top["external_ratio_percent"] = external_top["external_ratio"] * 100

    save_barh_percent(
        external_top,
        "external_ratio_percent",
        "dong",
        "외부 유입 소비 비율 TOP10",
        "외부 유입 비율 (%)",
        "PPT_02_외부유입비율_TOP10.png"
    )

    # =====================================================
    # 3. 소비 성장률 분석
    # =====================================================

    growth_top = (
        result.sort_values("amount_growth_24_vs_23", ascending=False)
        .head(10)
        .copy()
    )

    growth_top["label"] = growth_top["dong"] + " - " + growth_top["category"]
    growth_top["growth_percent"] = growth_top["amount_growth_24_vs_23"] * 100

    save_barh_percent(
        growth_top,
        "growth_percent",
        "label",
        "2023년 대비 2024년 소비 성장률 TOP10",
        "성장률 (%)",
        "PPT_03_소비성장률_TOP10.png"
    )

    pivot_growth = result.pivot_table(
        index="dong",
        columns="category",
        values="amount_growth_24_vs_23",
        fill_value=0
    )

    pivot_growth["평균"] = pivot_growth.mean(axis=1)
    pivot_growth = pivot_growth.sort_values("평균", ascending=False).drop(columns="평균").head(20)

    plt.figure(figsize=(12, 8))
    plt.imshow(pivot_growth.values, aspect="auto")
    plt.colorbar(label="소비 성장률")
    plt.xticks(range(len(pivot_growth.columns)), pivot_growth.columns, rotation=45)
    plt.yticks(range(len(pivot_growth.index)), pivot_growth.index)
    plt.title("행정동-업종별 소비 성장률 히트맵")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "PPT_03_소비성장률_히트맵.png"), dpi=250)
    plt.close()

    # =====================================================
    # 4. 공급 대비 소비 부족 분석
    # =====================================================

    shortage_top = (
        result.sort_values("sales_shortage", ascending=False)
        .head(10)
        .copy()
    )

    shortage_top["label"] = shortage_top["dong"] + " - " + shortage_top["category"]

    save_barh(
        shortage_top,
        "sales_shortage",
        "label",
        "공급 대비 소비 부족 TOP10",
        "소비 대비 공급 부족도",
        "PPT_04_공급대비소비부족_TOP10.png"
    )

    scatter_df = result.copy()

    plt.figure(figsize=(10, 7))
    plt.scatter(
        scatter_df["store_count"],
        scatter_df["total_amount"],
        s=scatter_df["sales_shortage_score"] * 500 + 30,
        alpha=0.6
    )

    top_label = scatter_df.sort_values("sales_shortage_score", ascending=False).head(10)

    for _, row in top_label.iterrows():
        plt.text(
            row["store_count"],
            row["total_amount"],
            row["dong"],
            fontsize=8
        )

    plt.title("업소 수 대비 소비금액 분포")
    plt.xlabel("업소 수")
    plt.ylabel("총 소비금액")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "PPT_04_업소수_vs_소비금액_산점도.png"), dpi=250)
    plt.close()

    # =====================================================
    # 5. 업종별 상권 활성도 분석
    # =====================================================

    cat_amount = (
        result.groupby("category", as_index=False)["total_amount"]
        .mean()
        .sort_values("total_amount", ascending=False)
    )

    save_barh(
        cat_amount,
        "total_amount",
        "category",
        "업종별 평균 소비금액",
        "평균 소비금액",
        "PPT_05_업종별_평균소비금액.png"
    )

    cat_score = (
        result.groupby("category", as_index=False)["location_score"]
        .mean()
        .sort_values("location_score", ascending=False)
    )

    save_barh(
        cat_score,
        "location_score",
        "category",
        "업종별 평균 입지추천점수",
        "평균 입지추천점수",
        "PPT_05_업종별_평균입지추천점수.png"
    )

    for group in ["음식점", "카페"]:
        temp = result[result["group"] == group].copy()

        pivot = temp.pivot_table(
            index="dong",
            columns="category",
            values="location_score",
            fill_value=0
        )

        pivot["평균"] = pivot.mean(axis=1)
        pivot = pivot.sort_values("평균", ascending=False).drop(columns="평균").head(20)

        plt.figure(figsize=(12, 8))
        plt.imshow(pivot.values, aspect="auto")
        plt.colorbar(label="입지추천점수")
        plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45)
        plt.yticks(range(len(pivot.index)), pivot.index)
        plt.title(f"{group} 업종별 상권 활성도 히트맵")
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, f"PPT_05_{group}_상권활성도_히트맵.png"), dpi=250)
        plt.close()

    # =====================================================
    # 6. 입지 추천 점수 산정
    # =====================================================

    weight_df = pd.DataFrame({
        "factor": [
            "소비규모",
            "수요인구",
            "성장성",
            "공급부족",
            "외부유입"
        ],
        "weight": [
            0.35,
            0.25,
            0.15,
            0.15,
            0.10
        ]
    })

    save_barh(
        weight_df,
        "weight",
        "factor",
        "입지추천점수 가중치 구성",
        "가중치",
        "PPT_06_입지추천_가중치.png"
    )

    plt.figure(figsize=(10, 8))

    plt.scatter(
        result["amount_score"],
        result["sales_shortage_score"],
        s=result["location_score"] * 700 + 30,
        alpha=0.7
    )

    top_label = result.sort_values("location_score", ascending=False).head(15)

    for _, row in top_label.iterrows():
        plt.text(
            row["amount_score"],
            row["sales_shortage_score"],
            row["dong"],
            fontsize=8
        )

    plt.xlabel("소비 규모 점수")
    plt.ylabel("공급 부족 점수")
    plt.title("소비 규모와 공급 부족 기반 입지추천 분포")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "PPT_06_입지추천_산점도.png"), dpi=250)
    plt.close()

    top10 = (
        result.sort_values("location_score", ascending=False)
        .head(10)
        .copy()
        .sort_values("location_score", ascending=True)
    )

    top10["label"] = top10["dong"] + " - " + top10["category"]

    # 가중치 반영 구성요소
    top10["소비규모"] = top10["amount_score"] * 0.35
    top10["수요인구"] = top10["pop_score"] * 0.25
    top10["성장성"] = top10["growth_score"] * 0.15
    top10["공급부족"] = top10["sales_shortage_score"] * 0.15
    top10["외부유입"] = top10["external_score"] * 0.10

    plt.figure(figsize=(14, 8))

    left = pd.Series([0] * len(top10), index=top10.index)

    for col in ["소비규모", "수요인구", "성장성", "공급부족", "외부유입"]:
        plt.barh(top10["label"], top10[col], left=left, label=col)
        left += top10[col]

    plt.legend()
    plt.title("최종 추천지역 TOP10 점수 구성")
    plt.xlabel("입지추천점수 구성")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "PPT_06_TOP10_점수구성.png"), dpi=250)
    plt.close()

    final_table = (
        top.sort_values(["group", "category", "rank"])
        .groupby(["group", "category"])
        .head(3)
    )

    final_table = final_table[["group", "category", "rank", "dong", "location_score", "grade", "reason"]]

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.axis("off")

    table = ax.table(
        cellText=final_table.values,
        colLabels=final_table.columns,
        loc="center",
        cellLoc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.6)

    plt.title("2023~2024 통합 업종별 최종 추천 행정동 TOP3", fontsize=16, pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "PPT_06_업종별_최종추천표_TOP3.png"), dpi=250)
    plt.close()

    print("PPT용 추가 시각화 생성 완료")


def main():
    visualize_year(2023)
    visualize_year(2024)
    visualize_integrated()

    print("시각화 완료")
    print("저장 위치:", VIZ_DIR)


if __name__ == "__main__":
    main()