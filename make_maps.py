import os
import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm

PROJECT_DIR = r"C:\Users\A\Desktop\Proj\store analysis"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")
MAP_DIR = os.path.join(OUT_DIR, "maps")
BOUNDARY_DIR = os.path.join(PROJECT_DIR, "data", "boundary")

os.makedirs(MAP_DIR, exist_ok=True)

FOOD_CATEGORIES = ["한식", "중식", "일식", "양식", "패스트푸드"]
CAFE_CATEGORIES = ["커피전문점", "제과점/아이스크림"]
TARGET_CATEGORIES = FOOD_CATEGORIES + CAFE_CATEGORIES

GUMI_DONG_CODE_MAP = {
    "37050110": "선산읍",
    "37050120": "고아읍",
    "37050130": "산동읍",

    "37050310": "무을면",
    "37050320": "옥성면",
    "37050330": "도개면",
    "37050340": "해평면",
    "37050360": "장천면",

    "37050510": "송정동",
    "37050550": "도량동",
    "37050560": "지산동",
    "37050570": "선주원남동",
    "37050590": "형곡1동",
    "37050600": "형곡2동",
    "37050610": "신평1동",
    "37050620": "신평2동",
    "37050660": "광평동",
    "37050670": "상모사곡동",
    "37050690": "임오동",
    "37050700": "인동동",
    "37050710": "진미동",
    "37050720": "양포동",
    "37050730": "비산동",
    "37050740": "공단동",
    "37050750": "원평동",
}

ZOOM_DONGS = [
    "선주원남동",
    "도량동",
    "지산동",
    "원평동",
    "신평1동",
    "신평2동",
    "비산동",
    "송정동",
    "광평동",
    "형곡1동",
    "형곡2동",
    "상모사곡동",
    "공단동",
    "임오동",
]


def safe_name(text):
    return str(text).replace("/", "_").replace("\\", "_")


def normalize_code(x):
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

def normalize_dong_name(x):
    if pd.isna(x):
        return ""

    x = str(x).strip()

    x = x.replace("경상북도", "")
    x = x.replace("구미시", "")
    x = x.replace(" ", "")

    return x

def fix_korean_mojibake(x):
    if pd.isna(x):
        return ""

    x = str(x).strip()

    # 1차: 깨진 한글 자동 복구
    try:
        fixed = x.encode("cp949", errors="ignore").decode("utf-8", errors="ignore")
        if fixed and fixed != x:
            x = fixed
    except Exception:
        pass

    # 2차: 자동 복구 안 되는 깨진 행정동명 직접 매핑
    mojibake_map = {
        # 동 지역
        "怨듬떒룞": "공단동",
        "怨좎븘쓭": "고아읍",
        "愿묓룊룞": "광평동",
        "鍮꾩궛룞": "비산동",
        "꽑二쇱썝궓룞": "선주원남동",
        "넚젙룞": "송정동",
        "떊룊1룞": "신평1동",
        "떊룊2룞": "신평2동",
        "룄웾룞": "도량동",
        "뼇룷룞": "양포동",
        "삎怨1룞": "형곡1동",
        "삎怨2룞": "형곡2동",
        "썝룊룞": "원평동",
        "씤룞룞": "인동동",
        "엫삤룞": "임오동",
        "吏궛룞": "지산동",
        "吏꾨몃룞": "진미동",

        # 읍
        "怨좎븘쓭": "고아읍",
        "궛룞쓭": "산동읍",
        "꽑궛쓭": "선산읍",

        # 면
        "臾댁쓣硫": "무을면",
        "룄媛쒕㈃": "도개면",
        "빐룊硫": "해평면",
        "삦꽦硫": "옥성면",
        "옣泥쒕㈃": "장천면",

    }

    return mojibake_map.get(x, x)

def extract_admin_dong_name(name):
    
    if pd.isna(name):
        return ""

    name = str(name).replace(" ", "").strip()

    dong_list = [
        "송정동",
        "원평동",
        "지산동",
        "도량동",
        "선주원남동",
        "형곡1동",
        "형곡2동",
        "신평1동",
        "신평2동",
        "비산동",
        "공단동",
        "광평동",
        "상모사곡동",
        "임오동",
        "인동동",
        "진미동",
        "양포동",

        "선산읍",
        "고아읍",
        "산동읍",

        "무을면",
        "옥성면",
        "도개면",
        "해평면",
        "장천면"
    ]

    for dong in dong_list:
        if dong in name:
            return dong

    return name



def load_boundary():
    shp_files = [
        os.path.join(BOUNDARY_DIR, f)
        for f in os.listdir(BOUNDARY_DIR)
        if f.lower().endswith(".shp")
    ]

    if len(shp_files) == 0:
        raise FileNotFoundError("data/boundary 폴더에 shp 파일이 없습니다.")

    shp_path = shp_files[0]

    boundary = None
    for enc in ["utf-8", "cp949", "euc-kr"]:
        try:
            boundary = gpd.read_file(shp_path, encoding=enc)
            print("경계파일 인코딩:", enc)
            break
        except Exception:
            pass

    if boundary is None:
        boundary = gpd.read_file(shp_path)

    print("경계파일 컬럼:", boundary.columns.tolist())

    name_col = None
    for c in [
        "ADM_NM", "adm_nm",
        "ADM_DR_NM", "adm_dr_nm",
        "EMD_NM", "emd_nm",
        "DONG_NM", "dong_nm",
        "행정동명", "읍면동명"
    ]:
        if c in boundary.columns:
            name_col = c
            break

    code_col = None
    for c in [
        "ADM_CD", "adm_cd",
        "ADM_DR_CD", "adm_dr_cd",
        "EMD_CD", "emd_cd",
        "DONG_CD", "dong_cd",
        "행정동코드", "법정동코드"
    ]:
        if c in boundary.columns:
            code_col = c
            break

    if name_col is None:
        raise ValueError("행정동명 컬럼을 찾지 못했습니다.")
    if code_col is None:
        raise ValueError("행정동 코드 컬럼을 찾지 못했습니다.")

    boundary["adm_cd"] = boundary[code_col].apply(normalize_code)

    print("ADM_CD 확인:")
    print(boundary[["adm_cd", name_col]].head(30))

    # ADM_CD 기준 행정동명 강제 매핑
    boundary["dong"] = boundary["adm_cd"].map(GUMI_DONG_CODE_MAP)

# 매핑 실패한 행 확인
    missing = boundary[boundary["dong"].isna()][["adm_cd", name_col]]
    if len(missing) > 0:
        print("매핑 실패한 코드:")
        print(missing)

    # 매핑 실패한 행은 제거
    boundary = boundary.dropna(subset=["dong"]).copy()

    boundary["dong"] = boundary["dong"].astype(str).str.strip()
    boundary["dong_key"] = boundary["dong"].apply(normalize_dong_name)


    # 행정동명 정리
    boundary["dong"] = (
        boundary["dong"]
        .astype(str)
        .str.replace("경상북도", "", regex=False)
        .str.replace("구미시", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.strip()
    )   

    # 행정동명 정리
    boundary["dong"] = (
        boundary["dong"]
        .str.replace("경상북도", "", regex=False)
        .str.replace("구미시", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.strip()
    )

    boundary["dong_key"] = boundary["dong"].apply(normalize_dong_name)
    boundary = boundary.to_crs(epsg=4326)
    boundary = boundary.dissolve(by=["dong_key", "dong"], as_index=False)

    print(boundary[["dong_key", "dong"]].head(30))
    print(boundary["dong"].unique())

    return boundary[["dong_key", "dong", "geometry"]]


def load_analysis_result():
    path = os.path.join(OUT_DIR, "market_analysis_result_integrated_2023_2024.csv")

    if not os.path.exists(path):
        raise FileNotFoundError("market_analysis_result_integrated_2023_2024.csv 파일이 없습니다. analyze_market.py 먼저 실행해줘.")

    df = pd.read_csv(path, encoding="utf-8-sig")

    df["dong_code"] = df["dong_code"].apply(normalize_code)
    df["dong_key"] = df["dong"].apply(normalize_dong_name)

    for col in [
        "total_amount", "total_count", "total_customer",
        "avg_total_demand_pop", "store_count", "location_score"
    ]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df[df["category"].isin(TARGET_CATEGORIES)].copy()

    return df


def make_map_summary(df, map_name, categories):
    temp = df[df["category"].isin(categories)].copy()

    if temp.empty:
        return pd.DataFrame()

    summary = (
        temp.groupby(["dong_key", "dong"], as_index=False)
        .agg(
            total_amount=("total_amount", "sum"),
            total_count=("total_count", "sum"),
            total_customer=("total_customer", "sum"),
            avg_total_demand_pop=("avg_total_demand_pop", "mean"),
            store_count=("store_count", "sum"),
            category_count=("category", "nunique"),
            avg_location_score=("location_score", "mean")
        )
    )

    summary["consumption_activation"] = (
        summary["total_amount"] / summary["avg_total_demand_pop"].replace(0, pd.NA)
    ).fillna(0)
    

    summary["map_name"] = map_name

    return summary


def add_store_count_circle(m, gdf):
    label_gdf = gdf.copy()
    label_gdf["point"] = label_gdf.geometry.representative_point()

    max_store = label_gdf["store_count"].max()
    if max_store <= 0:
        max_store = 1

    for _, row in label_gdf.iterrows():
        if row["total_amount"] <= 0:
            continue

        lat = row["point"].y
        lon = row["point"].x

        store_count = int(row["store_count"])
        radius = 16 + (store_count / max_store) * 22

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color="black",
            weight=2,
            fill=True,
            fill_color="white",
            fill_opacity=0.95,
        ).add_to(m)

        html = f"""
        <div style="
            font-size:12px;
            font-weight:bold;
            color:black;
            text-align:center;
            transform: translate(-50%, -50%);
            white-space:nowrap;">
            {store_count}
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=html)
        ).add_to(m)

        name_html = f"""
        <div style="
            font-size:11px;
            font-weight:bold;
            color:black;
            background:white;
            border:1px solid gray;
            border-radius:4px;
            padding:2px;
            text-align:center;
            white-space:nowrap;">
            {row['dong']}
        </div>
        """

        folium.Marker(
            location=[lat + 0.004, lon],
            icon=folium.DivIcon(html=name_html)
        ).add_to(m)


def make_activation_map(boundary, summary, map_name):
    gdf = boundary.merge(
        summary,
        on="dong_key",
        how="left",
        suffixes=("_boundary", "_data")
    )

    if "dong_data" in gdf.columns:
        gdf["dong"] = gdf["dong_data"]
        gdf["dong"] = gdf["dong"].fillna(gdf["dong_boundary"])
    else:
        gdf["dong"] = gdf["dong_boundary"]

    gdf["dong"] = gdf["dong"].astype(str)
    gdf.loc[gdf["dong"].str.contains("□|�|\\?", regex=True, na=False), "dong"] = ""

    fill_cols = [
        "total_amount", "total_count", "total_customer",
        "avg_total_demand_pop", "store_count",
        "category_count", "avg_location_score",
        "consumption_activation"
    ]

    for col in fill_cols:
        if col not in gdf.columns:
            gdf[col] = 0
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0)

    # 색상 표현용 정규화: 업종별 지도마다 상대적 차이를 크게 보여줌
    valid = gdf["consumption_activation"] > 0

    gdf["activation_norm"] = 0.0

    if valid.sum() == 0:
        pass
    else:
        values = gdf.loc[valid, "consumption_activation"]

        vmin = values.quantile(0.05)
        vmax = values.quantile(0.95)

        if vmax == vmin:
            gdf.loc[valid, "activation_norm"] = 0.6
        else:
            norm = (gdf.loc[valid, "consumption_activation"] - vmin) / (vmax - vmin)
            norm = norm.clip(0, 1)
            gdf.loc[valid, "activation_norm"] = norm.astype(float)

    center_geom = gdf.to_crs(epsg=5179).geometry.centroid.to_crs(epsg=4326)

    center = [
        center_geom.y.mean(),
        center_geom.x.mean()
    ]

    m = folium.Map(location=center, zoom_start=12, tiles="cartodbpositron")

    colormap = cm.LinearColormap(
        colors=[
            "#fff5f0",
            "#fee0d2",
            "#fcbba1",
            "#fc9272",
            "#fb6a4a",
            "#de2d26",
            "#a50f15"
        ],
        vmin=0,
        vmax=1,
        caption=f"{map_name} 인구 대비 소비 활성도 상대지수"
    )

    def style_function(feature):
        value = feature["properties"].get("activation_norm", 0)
        raw_value = feature["properties"].get("consumption_activation", 0)

        return {
            "fillColor": colormap(value),
            "color": "black",
            "weight": 2.5,
            "fillOpacity": 0.80 if raw_value > 0 else 0.10,
        }

    folium.GeoJson(
        gdf,
        name=map_name,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "dong",
                "consumption_activation",
                "activation_norm",
                "total_amount",
                "avg_total_demand_pop",
                "store_count",
                "category_count",
                "total_count",
                "total_customer",
                "avg_location_score"
            ],
            aliases=[
                "행정동",
                "인구 대비 소비 활성도",
                "색상 상대지수",
                "총 소비금액",
                "평균 총수요인구",
                "현재 업소 수",
                "업종 수",
                "소비건수",
                "소비자수",
                "평균 입지추천점수"
            ],
            localize=True
        )
    ).add_to(m)

    colormap.add_to(m)

    non_zoom_gdf = gdf[~gdf["dong"].isin(ZOOM_DONGS)].copy()
    add_store_count_circle(m, non_zoom_gdf)

    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        z-index: 9999;
        background-color: white;
        padding: 12px;
        border: 2px solid gray;
        border-radius: 6px;
        font-size: 13px;">
        <b>지도 해석</b><br>
        진한 색: 인구 대비 소비 활성도 상대적으로 높음<br>
        연한 색: 인구 대비 소비 활성도 상대적으로 낮음<br>
        원 안 숫자: 해당 업종 업소 수<br>
        ※ 색은 업종별 지도 내 상대 비교 기준
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl().add_to(m)

    save_path = os.path.join(
        MAP_DIR,
        f"{safe_name(map_name)}_인구대비소비활성도_업소수지도.html"
    )
    m.save(save_path)
    print("저장:", save_path)

    # =====================================================
    # 도심권 확대 지도 추가 저장
    # =====================================================
    zoom_gdf = gdf[gdf["dong"].isin(ZOOM_DONGS)].copy()

    if not zoom_gdf.empty:
        zoom_center_geom = zoom_gdf.to_crs(epsg=5179).geometry.centroid.to_crs(epsg=4326)

        zoom_center = [
            zoom_center_geom.y.mean(),
            zoom_center_geom.x.mean()
        ]

        zoom_map = folium.Map(
            location=zoom_center,
            zoom_start=13,
            tiles="cartodbpositron"
        )

        folium.GeoJson(
            zoom_gdf,
            name=f"{map_name}_도심권확대",
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=[
                    "dong",
                    "consumption_activation",
                    "activation_norm",
                    "total_amount",
                    "avg_total_demand_pop",
                    "store_count",
                    "category_count",
                    "total_count",
                    "total_customer",
                    "avg_location_score"
                ],
                aliases=[
                    "행정동",
                    "인구 대비 소비 활성도",
                    "색상 상대지수",
                    "총 소비금액",
                    "평균 총수요인구",
                    "현재 업소 수",
                    "업종 수",
                    "소비건수",
                    "소비자수",
                    "평균 입지추천점수"
                ],
                localize=True
            )   
        ).add_to(zoom_map)

        colormap.add_to(zoom_map)
        add_store_count_circle(zoom_map, zoom_gdf)

        zoom_legend_html = """
        <div style="
            position: fixed;
            bottom: 30px;
            left: 30px;
            z-index: 9999;
            background-color: white;
            padding: 12px;
            border: 2px solid gray;
            border-radius: 6px;
            font-size: 13px;">
            <b>도심권 확대 지도</b><br>
            진한 색: 인구 대비 소비 활성도 높음<br>
            연한 색: 인구 대비 소비 활성도 낮음<br>
            원 안 숫자: 해당 업종 업소 수
        </div>
        """
        zoom_map.get_root().html.add_child(folium.Element(zoom_legend_html))
        folium.LayerControl().add_to(zoom_map)

        zoom_save_path = os.path.join(
            MAP_DIR,
            f"{safe_name(map_name)}_도심권확대_인구대비소비활성도_업소수지도.html"
        )

        zoom_map.save(zoom_save_path)
        print("도심권 확대 저장:", zoom_save_path)

    return gdf


def main():
    print("1. 행정동 경계 불러오는 중...")
    boundary = load_boundary()

    print("2. 분석 결과 불러오는 중...")
    result = load_analysis_result()

    map_targets = []

    for cat in FOOD_CATEGORIES:
        map_targets.append((cat, [cat]))

    map_targets.append(("음식점_합본", FOOD_CATEGORIES))

    for cat in CAFE_CATEGORIES:
        map_targets.append((cat, [cat]))

    map_targets.append(("카페_합본", CAFE_CATEGORIES))
    map_targets.append(("전체_합본", FOOD_CATEGORIES + CAFE_CATEGORIES))

    all_summary = []

    for map_name, categories in map_targets:
        print("지도 생성 중:", map_name)

        summary = make_map_summary(result, map_name, categories)

        summary.to_csv(
            os.path.join(MAP_DIR, f"{safe_name(map_name)}_인구대비소비활성도_요약.csv"),
            index=False,
            encoding="utf-8-sig"
        )

        make_activation_map(boundary, summary, map_name)

        all_summary.append(summary.assign(map_name=map_name))

    final = pd.concat(all_summary, ignore_index=True)

    final.to_csv(
        os.path.join(MAP_DIR, "전체_인구대비소비활성도_업소수_요약.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    print("완료")
    print("저장 위치:", MAP_DIR)


if __name__ == "__main__":
    main()