import os
import pandas as pd

PROJECT_DIR = r"C:\Users\A\Desktop\Proj\store analysis"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")

INPUT_PATH = os.path.join(OUT_DIR, "store_classified_geocoded.csv")

SAVE_PATH = os.path.join(
    OUT_DIR,
    "기타음식점_재분류후보.csv"
)


def detect_category(text):
    text = str(text).replace(" ", "").lower()

    # =========================
    # 패스트푸드
    # =========================
    fastfood_keywords = [
        "버거", "햄버거", "피자",
        "치킨", "핫도그",
        "토스트", "샌드위치",
        "타코야끼", "컵밥",
        "닭꼬치", "푸드코트"
    ]

    # =========================
    # 중식
    # =========================
    chinese_keywords = [
        "짜장", "짬뽕", "탕수육",
        "마라", "훠궈",
        "양꼬치", "중화",
        "반점", "딤섬",
        "사천", "중국관",
        "중국집"
    ]

    # =========================
    # 일식
    # =========================
    japanese_keywords = [
        "초밥", "스시", "라멘",
        "우동", "돈까스",
        "돈카츠", "규카츠",
        "규동", "텐동",
        "소바", "오마카세",
        "사케", "야키",
        "야끼", "덮밥",
        "이자카야"
    ]

    # =========================
    # 양식
    # =========================
    western_keywords = [
        "파스타", "스테이크",
        "브런치", "리조또",
        "라자냐", "필라프",
        "트라토리아",
        "레스토랑",
        "와인바", "펍",
        "브리또", "타코",
        "함박스테이크"
    ]

    for k in fastfood_keywords:
        if k in text:
            return "패스트푸드", k

    for k in chinese_keywords:
        if k in text:
            return "중식", k

    for k in japanese_keywords:
        if k in text:
            return "일식", k

    for k in western_keywords:
        if k in text:
            return "양식", k

    return None, None


def main():

    if not os.path.exists(INPUT_PATH):
        print("파일 없음:", INPUT_PATH)
        return

    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

    if "category" not in df.columns:
        print("category 컬럼 없음")
        return

    etc = df[df["category"] == "기타음식점"].copy()

    results = []

    for _, row in etc.iterrows():

        store = str(row.get("store_name", ""))
        addr = str(row.get("addr", ""))

        full_text = f"{store} {addr}"

        new_cat, keyword = detect_category(full_text)

        if new_cat is not None:

            results.append({
                "store_name": store,
                "addr": addr,
                "기존분류": "기타음식점",
                "추천분류": new_cat,
                "감지키워드": keyword
            })

    result_df = pd.DataFrame(results)

    result_df.to_csv(
        SAVE_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    print("=" * 50)
    print("재분류 후보 저장 완료")
    print(SAVE_PATH)
    print("=" * 50)

    if not result_df.empty:
        print(result_df["추천분류"].value_counts())


if __name__ == "__main__":
    main()