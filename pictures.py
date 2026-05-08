import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

PROJECT_DIR = "C:\\Users\\A\\Desktop\\Proj\\store analysis"
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
    plt.barh(temp[y], temp[x])
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("행정동")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, filename), dpi=250)
    plt.close()


def visualize_year(year):
    result_file = os.path.join(OUT_DIR, f"market_analysis_result_{year}.csv")
    top_file = os.path.join(OUT_DIR, f"market_recommendation_top10_{year}.csv")

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

    # 3. 입지추천점수 히트맵 - 음식점
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
        temp = top[top["category"] == cat].sort_values("location_score", ascending=True).tail(5)

        plt.figure(figsize=(9, 5))
        plt.barh(temp["dong"], temp["location_score"])
        plt.title(f"{year}년 {cat} 신규 입지 추천 TOP5")
        plt.xlabel("입지추천점수")
        plt.ylabel("행정동")
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, f"{year}_05_{safe_name(cat)}_추천_TOP5.png"), dpi=250)
        plt.close()

    # 6. 최종 추천표 이미지
    final_table = top.sort_values(["group", "category", "rank"]).groupby(["group", "category"]).head(3)
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
    result = pd.read_csv(
        os.path.join(OUT_DIR, "market_analysis_result_integrated_2023_2024.csv"),
        encoding="utf-8-sig"
    )

    top = pd.read_csv(
        os.path.join(OUT_DIR, "market_recommendation_top10_integrated_2023_2024.csv"),
        encoding="utf-8-sig"
    )

    # 1. 통합 최종 음식점 추천 TOP10
    food_top = (
        top[top["group"] == "음식점"]
        .sort_values("location_score", ascending=False)
        .head(10)
        .sort_values("location_score", ascending=True)
    )

    plt.figure(figsize=(10, 6))
    plt.barh(food_top["dong"] + " - " + food_top["category"], food_top["location_score"])
    plt.title("2023~2024 통합 음식점 최종 입지추천 TOP10")
    plt.xlabel("입지추천점수")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "통합_01_음식점_최종추천_TOP10.png"), dpi=250)
    plt.close()

    # 2. 통합 최종 카페 추천 TOP10
    cafe_top = (
        top[top["group"] == "카페"]
        .sort_values("location_score", ascending=False)
        .head(10)
        .sort_values("location_score", ascending=True)
    )

    plt.figure(figsize=(10, 6))
    plt.barh(cafe_top["dong"] + " - " + cafe_top["category"], cafe_top["location_score"])
    plt.title("2023~2024 통합 카페 최종 입지추천 TOP10")
    plt.xlabel("입지추천점수")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "통합_02_카페_최종추천_TOP10.png"), dpi=250)
    plt.close()

    # 3. 통합 입지추천 히트맵
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
        plt.title(f"2023~2024 통합 {group} 입지추천점수 히트맵")
        plt.tight_layout()
        plt.savefig(os.path.join(VIZ_DIR, f"통합_03_{group}_입지추천점수_히트맵.png"), dpi=250)
        plt.close()

    # 4. 2023 → 2024 성장률 TOP10
    growth_top = (
        result.sort_values("amount_growth_24_vs_23", ascending=False)
        .head(10)
        .sort_values("amount_growth_24_vs_23", ascending=True)
    )

    plt.figure(figsize=(10, 6))
    plt.barh(growth_top["dong"] + " - " + growth_top["category"], growth_top["amount_growth_24_vs_23"])
    plt.title("2023년 대비 2024년 소비 성장률 TOP10")
    plt.xlabel("소비 성장률")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "통합_04_소비성장률_TOP10.png"), dpi=250)
    plt.close()

    # 5. 최종 추천표
    final_table = top.sort_values(["group", "category", "rank"]).groupby(["group", "category"]).head(3)
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
    plt.savefig(os.path.join(VIZ_DIR, "통합_05_업종별_최종추천표_TOP3.png"), dpi=250)
    plt.close()


def main():
    visualize_year(2023)
    visualize_year(2024)
    visualize_integrated()

    print("시각화 완료")
    print("저장 위치:", VIZ_DIR)


if __name__ == "__main__":
    main()