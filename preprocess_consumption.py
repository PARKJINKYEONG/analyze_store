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
    
    # 1순위: 원본 업종명
    text = (
        str(row.get("mc_bzc1_nm", "")) + " " +
        str(row.get("mc_bzc2_nm", "")) + " " +
        str(row.get("mc_bzc3_nm", ""))
    )

    text = text.replace(" ", "").lower()

    # 패스트푸드
    if any(x in text for x in [
        "햄버거", "버거", "치킨",
        "피자", "패스트푸드", "샌드위치"
    ]):
        return "패스트푸드"

    # 중식
    if any(x in text for x in [
        "중식", "짜장", "짬뽕",
        "탕수육", "마라", "양꼬치"
    ]):
        return "중식"

    # 일식
    if any(x in text for x in [
        "일식", "초밥", "스시",
        "우동", "라멘", "돈까스",
        "횟집", "회"
    ]):
        return "일식"

    # 양식
    if any(x in text for x in [
        "양식", "파스타", "스테이크",
        "브런치", "레스토랑", "퓨전"
    ]):
        return "양식"

    # 제과
    if any(x in text for x in [
        "제과", "베이커리",
        "디저트", "도넛",
        "아이스크림"
    ]):
        return "제과점/아이스크림"

    # 카페
    if any(x in text for x in [
        "카페", "커피", "다방"
    ]):
        return "커피전문점"

    # 한식
    if any(x in text for x in [
        "한식", "국밥", "찌개",
        "백반", "칼국수", "냉면",
        "삼겹", "갈비", "한정식"
    ]):
        return "한식"

    return classify_store_name(
        row.get("store_name",
            row.get("업소명",
                row.get("가맹점명", "")
            )
        ),

        row.get("소재지(지번)",
            row.get("addr",
                row.get("소재지",
                    row.get("주소", "")
                )
            )
        ),

        row.get("map_category", "")
    )
def classify_store_name(store_name, addr="", map_category=""):
    store = str(store_name).replace(" ", "").lower()
    addr = str(addr).replace(" ", "").lower()
    map_category = str(map_category).replace(" ", "").lower()

    full_text = f"{store} {addr} {map_category}"

     # =========================================
    # 패스트푸드
    # =========================================
    if any(x in full_text for x in [
        "맘스터치", "버거킹", "롯데리아", "맥도날드",
        "kfc", "케이에프씨", "프랭크버거",
        "버거", "햄버거", "핫도그",
        "치킨", "통닭", "닭강정",
        "피자", "도미노", "피자헛", "피자스쿨",
        "피자마루", "고피자", "59쌀피자",
        "샌드위치", "토스트", "서브웨이",
        "굽네", "교촌", "bbq", "비비큐",
        "bhc", "비에이치씨", "또래오래",
        "호식이", "처갓집", "네네치킨",
        "지코바", "멕시카나", "페리카나",
        "오븐에꾸운닭", "60계치킨", "땅땅치킨",
        "자담치킨", "푸라닭", "티바두마리치킨",
        "피자나라치킨공주", "닭강정"
    ]):
        return "패스트푸드"

    # =========================
    # 2. 중식
    # =========================
    if any(x in full_text for x in [
        "중식", "중국집", "중화", "중화요리",
        "반점", "대반점", "각반점",
        "짜장", "자장", "짬뽕", "탕수육",
        "마라", "마라탕", "훠궈", "양꼬치",
        "양육관", "상하이", "샹하이",
        "북경", "자금성", "홍콩반점",
        "차이나", "중국관", "중국성",
        "동보성", "만리장성", "중화루",
        "백화원", "태화루", "태화각",
        "청운각", "성빈각", "향원반점",
        "리안중화요리", "교동짬뽕",
        "홍콩", "천안문", "취팔선",
        "동북양꼬치", "인동양꼬치", "북경양꼬치"
    ]):
        return "중식"

    # =========================
    # 3. 일식
    # =========================
    if any(x in full_text for x in [
        "일식", "초밥", "스시", "참치",
        "라멘", "라면전문", "돈부리",
        "카츠", "가츠", "돈까스", "돈가스",
        "텐동", "이자카야", "사시미",
        "오니기리", "갓포", "쇼쿠",
        "모미지", "타다이마", "유메노",
        "오사카", "히로시마",
        "하나스시", "스시가한", "사천일식",
        "항구일식", "토모미", "아스카",
        "미소야", "메차쿠차", "이찌돈",
        "담뽀뽀", "대성암본가초밥집",
        "후우미라멘", "가마메구미"
    ]):
        return "일식"

    # =========================
    # 4. 양식
    # =========================
    if any(x in full_text for x in [
        "양식", "양식당", "양식코너",
        "레스토랑", "파스타", "스파게티",
        "스테이크", "스테이크하우스",
        "브런치", "리조또", "라자냐",
        "비스트로", "이태리", "이탈리",
        "아웃백", "라라코스트", "코지하우스",
        "오스테리아", "파스타부오노",
        "봉대박스파게티", "스테이크팩토리",
        "샐러드", "포케", "다이닝"
    ]):
        return "양식"


    # =========================================
    # 제과/디저트
    # =========================================
    if any(x in full_text for x in [
        "베이커리", "제과", "제빵",
        "빵", "도넛", "와플",
        "젤라또", "탕후루", "베이글",
        "크로와", "파티세리",
        "마카롱", "디저트",
        "케이크", "쿠키", "크로플",
        "빙수", "설빙", "떡",
        "꽈배기", "호두과자",
        "화과", "오븐", "브레드"
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

    # =========================
    # 5. 한식
    # =========================
    if any(x in full_text for x in [
        "한식", "한식당", "식당", "밥상", "집밥",
        "백반", "기사식당", "뷔페", "한식뷔페",
        "국밥", "돼지국밥", "순대", "순대국밥",
        "곱창", "막창", "대창", "양곱창",
        "삼겹", "목살", "갈비", "숯불", "석쇠",
        "불고기", "고기집", "식육식당", "정육식당",
        "한우", "생고기", "뒷고기",
        "백숙", "삼계탕", "오리", "닭갈비",
        "찜닭", "닭볶음탕", "닭곰탕",
        "추어탕", "매운탕", "어탕", "알탕",
        "동태탕", "해물탕", "아구찜", "아귀찜",
        "해물찜", "복집", "복어", "장어",
        "곰장어", "꼼장어", "조개", "굴국밥",
        "횟집", "회센터", "회센타", "회수산",
        "회타운", "물회", "세꼬시", "수산",
        "대게", "생선구이", "오징어",
        "칼국수", "국수", "냉면", "밀면",
        "보쌈", "족발", "감자탕", "해장국",
        "뚝배기", "한정식", "분식", "김밥",
        "떡볶이", "부대찌개", "김치찜",
        "도시락", "본죽", "죽이야기", "비빔밥",
        "가든", "보양탕", "보신탕", "염소",
        "묵집", "두부", "쌈밥", "전집",
        "막걸리", "주막", "포차"
    ]):
        return "한식"


    # =========================================
    # 기타
    # =========================================
    return "기타음식점"

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

    if inflow_frames:
        inflow = pd.concat(inflow_frames, ignore_index=True)

        inflow_summary = inflow.groupby(
            ["year_month", "dong_code", "dong", "category"],
            as_index=False
        ).agg(
            external_amount=("amount", lambda x: x[inflow.loc[x.index, "is_external"]].sum()),
            total_amount=("amount", "sum")
        )

        inflow_summary["external_ratio"] = (
            inflow_summary["external_amount"]
            / inflow_summary["total_amount"].replace(0, np.nan)
        ).fillna(0)

        inflow_summary.to_csv(
            os.path.join(OUT_DIR, "consumption_inflow_summary.csv"),
            index=False,
            encoding="utf-8-sig"
        )

    print("소비 전처리 완료")


if __name__ == "__main__":
    main()