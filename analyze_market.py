import os
import re
import glob
import numpy as np
import pandas as pd


PROJECT_DIR = r"C:\Users\A\Desktop\Proj\store analysis"
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

    VALID_DONGS = [
        "선산읍", "고아읍", "산동읍",
        "무을면", "옥성면", "도개면", "해평면", "장천면",
        "송정동", "도량동", "지산동", "선주원남동",
        "형곡1동", "형곡2동", "신평1동", "신평2동",
        "광평동", "상모사곡동", "임오동", "인동동",
        "진미동", "양포동", "비산동", "공단동", "원평동",

        # 법정동
        "봉곡동", "부곡동", "남통동", "선기동",
        "형곡동", "신평동", "상모동", "사곡동",
        "오태동", "임은동", "인의동", "황상동",
        "구평동", "진평동", "시미동", "임수동",
        "옥계동", "구포동", "금전동", "거의동",
        "양호동", "신동"
    ]

    # 1) 주소에 실제 읍면동명이 포함되어 있으면 그것만 사용
    for dong in VALID_DONGS:
        if dong in text:
            return dong

    # =====================================================
    # 도로명 기반 행정동 보정
    # =====================================================

    ROAD_TO_DONG = {

        # 선주원남동
        "봉곡로": "봉곡동",
        "선주로": "봉곡동",
        "야은로": "봉곡동",
        "고아읍원호": "봉곡동",

        # 형곡동
        "형곡로": "형곡동",
        "신시로": "형곡동",

        # 신평동
        "칠성로": "신평동",
        "구미중앙로": "신평동",

        # 상모사곡동
        "상사서로": "상모동",
        "박정희로": "상모동",
        "상모로": "상모동",
        "사곡로": "사곡동",

        # 임오동
        "임은길": "임은동",
        "금오대로": "오태동",
        "오태길": "오태동",

        # 인동동
        "인의로": "인의동",
        "황상동로": "황상동",
        "구평동로": "구평동",
        "인동가산로": "인의동",

        # 진미동
        "인동중앙로": "진평동",
        "산호대로": "진평동",
        "여헌로": "진평동",
        "수출대로": "시미동",
        "3공단로": "임수동",

        # 양포동
        "옥계북로": "옥계동",
        "산호대로31길": "옥계동",
        "해마루공원로": "옥계동",

        # 송정동
        "송정대로": "송정동",

        # 도량동
        "도량로": "도량동",

        # 원평동
        "구미역로": "원평동",
        "원남로": "원평동",

        # 비산동
        "비산로": "비산동",

        # 공단동
        "1공단로": "공단동",
        "2공단로": "공단동",
        "4공단로": "공단동",

        # 광평동
        "광평길": "광평동",

        # 산동읍
        "신당로": "산동읍",

        # 고아읍
        "문장로": "고아읍",
        "들성로": "고아읍",

        # 선산읍
        "선산대로": "선산읍",

        # 해평면
        "해평시장로": "해평면",

        # 장천면
        "장천로": "장천면",

        # 도개면
        "도개다곡길": "도개면",

        # 무을면
        "무을로": "무을면",

        # 옥성면
        "옥성중앙로": "옥성면",
    }

    for road, dong in ROAD_TO_DONG.items():
        if road in text:
            return dong

    return np.nan

def legal_to_admin_dong(dong):
    if pd.isna(dong):
        return np.nan

    dong = str(dong).strip()

    mapping = {
        "선산읍": "선산읍",
        "고아읍": "고아읍",
        "산동읍": "산동읍",
        "무을면": "무을면",
        "옥성면": "옥성면",
        "도개면": "도개면",
        "해평면": "해평면",
        "장천면": "장천면",

        "송정동": "송정동",
        "도량동": "도량동",
        "지산동": "지산동",
        "원평동": "원평동",
        "비산동": "비산동",
        "공단동": "공단동",
        "광평동": "광평동",

        "봉곡동": "선주원남동",
        "부곡동": "선주원남동",
        "남통동": "선주원남동",
        "선기동": "선주원남동",

        "형곡동": "형곡1동",
        "신평동": "신평1동",

        "상모동": "상모사곡동",
        "사곡동": "상모사곡동",

        "오태동": "임오동",
        "임은동": "임오동",

        "인의동": "인동동",
        "황상동": "인동동",
        "구평동": "인동동",

        "진평동": "진미동",
        "시미동": "진미동",
        "임수동": "진미동",

        "옥계동": "양포동",
        "구포동": "양포동",
        "금전동": "양포동",
        "거의동": "양포동",
        "양호동": "양포동",
        "신동": "양포동",
    }

    return mapping.get(dong, np.nan)
def classify_store_name(store_name, addr=""):
    text = str(store_name).replace(" ", "").lower()
    addr_text = str(addr).replace(" ", "").lower()

    full_text = f"{text} {addr_text}"

     # =========================================
    # 패스트푸드
    # =========================================
    if any(x in full_text for x in [
        "맘스터치", "버거킹", "롯데리아", "맥도날드",
        "kfc", "케이에프씨", "프랭크버거", "버거", "수제버거"
        "햄버거", "핫도그", "치킨", "통닭", "닭강정",
        "피자", "도미노", "피자헛", "피자스쿨", "피자마루", 
        "고피자", "샌드위치", "토스트", "서브웨이",
        "버거앤프라이즈", "에그드랍", "굽네", "교촌", 
        "bbq", "비비큐", "bhc", "비에이치씨", "뉴욕핫도그",
        "또래오래", "호식이", "처갓집", "네네치킨", "지코바",
        "멕시카나", "페리카나", "치킨호프", "오븐에꾸운닭",
        "꾸브라꼬", "60계치킨", "토스트앤", "컵밥", 
        "분모자떡볶이", "핫바","분식카페", "즉석떡볶이",
        "도시락카페", "닭꼬치", "타코야끼", "크리스피", "푸드코트"
    ]):
        return "패스트푸드"

    # =========================================
    # 중식
    # =========================================
    if any(x in full_text for x in [
        "반점", "중화", "중식", "짜장", "짬뽕",
        "탕수육", "마라", "훠궈", "양꼬치", "양육관", 
        "상하이", "샹하이", "북경", "자금성", "홍콩",
        "차이나", "중국관", "중국성", "동보성", "만리장성",
        "중화루", "대반점", "사천", "사천성", "북경반점",
        "황궁", "황제짬뽕", "마라샹궈", "딤섬", "쿵파오", 
        "유린기", "짬뽕관", "짬뽕타운", "짜장면", "간짜장",
        "짬뽕전문", "중화반점"
    ]):
        return "중식"

    # =========================================
    # 일식
    # =========================================
    if any(x in full_text for x in [
        "초밥", "스시", "일식", "참치", "라멘", 
        "우동", "돈부리", "카츠", "가츠", "텐동",
        "이자카야", "사시미", "오니기리", "갓포",
        "쇼쿠", "모미지", "타다이마", "유메노",
        "오사카", "히로시마", "하나스시", "가마메", 
        "규카츠", "규동", "야끼", "야키", "쿠시", 
        "쿠시카츠", "스시로", "스시집", "초밥집", "연어",
        "돈카츠", "돈까스집", "소바", "메밀", "우마이",
          "오마카세", "후토마키", "덮밥", "일본가정식",
        "사케", "야키토리", "철판", "철판요리"
    ]):
        return "일식"

    # =========================================
    # 양식
    # =========================================
    if any(x in full_text for x in [
        "양식", "레스토랑", "파스타", "스파게티",
        "스테이크", "브런치", "리조또", "라자냐",
        "비스트로", "이태리", "이탈리", "아웃백",
        "라라코스트", "코지하우스", "오스테리아", "샐러드",
        "포케", "스테이크하우스", "피렌체", "트라토리아",
        "까르보나라", "크림파스타", "필라프", "그라탕",
        "함박스테이크", "브루클린", "펍", "pub", 
        "와인바", "바베큐", "멕시칸","타코", "브리또", 
        "퀘사디아", "유러피안", "다이너"
    ]):
        return "양식"


    # =========================================
    # 제과/디저트
    # =========================================
    if any(x in full_text for x in [
        "베이커리", "제과", "제빵",
        "파리바게뜨", "뚜레쥬르",
        "던킨", "도넛",
        "배스킨", "배스킨라빈스",
        "아이스크림", "설빙",
        "와플", "젤라또",
        "베이글", "크로플",
        "마카롱", "디저트",
        "케이크", "쿠키",
        "빙수", "호두과자",
        "꽈배기", "브레드",
        "파티세리"
    ]):
        return "제과점/아이스크림"
    # =========================================
    # 커피 / 카페
    # =========================================
    if any(x in full_text for x in [
        "카페", "까페", "커피", "다방",
        "스타벅스", "이디야", "투썸",
        "빽다방", "더벤티", "메가커피",
        "메가엠지씨", "컴포즈",
        "하삼동", "공차", "파스쿠찌",
        "할리스", "드롭탑",
        "엔제리너스", "요거프레소",
        "쥬씨", "천씨씨",
        "텐퍼센트", "더리터",
        "에이바우트", "읍천리",
        "봄봄", "커피베이",
        "카페보스", "감성커피",
        "커피명가", "폴바셋",
        "커피왕", "커피특별시",
        "커피팀버", "커피마루",
        "커피인", "커피온",
        "카페인중독", "디저트39",
        "카페카리타스"
    ]):
        return "커피전문점"

    # =========================================
    # 한식
    # =========================================
    if any(x in full_text for x in [
        "식당", "한식", "국밥",
        "돼지국밥", "순대", "곱창",
        "막창", "삼겹", "갈비",
        "불고기", "백숙", "삼계탕",
        "추어탕", "매운탕", "칼국수",
        "국수", "냉면", "보쌈",
        "족발", "찜닭", "감자탕",
        "해장국", "백반", "밥상",
        "집밥", "뚝배기", "한정식",
        "분식", "김밥", "떡볶이",
        "닭갈비", "쭈꾸미", "낙지",
        "장어", "오리", "가든",
        "정육식당", "식육식당",
        "기사식당", "보리밥",
        "순두부", "부대찌개",
        "김치찜", "도시락",
        "본죽", "비빔밥",
        "죽이야기"
    ]):
        return "한식"

    # =========================================
    # 기타
    # =========================================
    return "기타음식점"


def load_store_supply():
    geocoded_supply_path = os.path.join(OUT_DIR, "store_supply_geocoded.csv")

    if os.path.exists(geocoded_supply_path):
        print("지오코딩 기반 업소 수 사용:", geocoded_supply_path)
        supply = pd.read_csv(geocoded_supply_path, encoding="utf-8-sig")
        supply = supply[supply["category"].isin(TARGET_CATEGORIES)].copy()
        return supply
    
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

        temp["category"] = temp.apply(classify_store_name, axis=1)

        frames.append(temp)

    stores = pd.concat(frames, ignore_index=True)

    # 업소명 정리
    stores["store_name_clean"] = (
        stores["store_name"]
        .astype(str)
        .str.replace(" ", "", regex=False)
        .str.lower()
    )

    # 같은 행정동 + 같은 업종 + 같은 업소명 중복 제거
    stores = stores.drop_duplicates(
        subset=["dong", "category", "store_name_clean"]
    )

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

    print("전체 업소 수:", len(stores))
    print("카테고리별 업소 수:")
    print(stores["category"].value_counts())

    print("행정동별 양식 업소:")
    print(
        stores[stores["category"] == "양식"]
        .groupby("dong")["store_name"]
        .count()
        .sort_values(ascending=False)
    )

    print("휴게소 관련 업소:")
    print(
        stores[stores["store_name"].astype(str).str.contains("휴게소|양식코너|퓨전코너", na=False)]
        [["store_name", "addr", "legal_dong", "dong", "category"]]
    )

    print("도개/낙동강/휴게소 확인:")
    print(
        stores[
            stores["store_name"].astype(str).str.contains("낙동강|구미휴게소|양식코너|퓨전코너|도개", na=False)
        ][["store_name", "addr", "legal_dong", "dong", "category"]]
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

    # ---------------------------------------------------------
    # 업소수 0 방지
    # ---------------------------------------------------------

    base["store_count_adj"] = base["store_count"].replace(0, 0.5)

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