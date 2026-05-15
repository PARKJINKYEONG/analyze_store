import os
import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm
from pyproj import Transformer


PROJECT_DIR = r"C:\Users\Gaeng2\Desktop\Proj\store analysis"
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

    boundary = boundary.to_crs(epsg=4326)
    boundary = boundary.dissolve(by=["dong_key", "dong"], as_index=False)


    return boundary[["dong_key", "dong", "geometry"]]


def load_analysis_result():
    path = os.path.join(OUT_DIR, "market_analysis_result_integrated_2023_2024.csv")

    if not os.path.exists(path):
        raise FileNotFoundError("market_analysis_result_integrated_2023_2024.csv 파일이 없습니다. analyze_market.py 먼저 실행해줘.")

    df = pd.read_csv(path, encoding="utf-8-sig")

    if "dong_code" in df.columns:
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

    # store_supply.csv 기준 업소 수로 최종 보정
    supply = load_final_store_supply()

    if not supply.empty:
        df = df.drop(columns=["store_count"], errors="ignore")
        df = df.merge(
            supply,
            on=["dong", "category"],
            how="left"
        )
        df["store_count"] = pd.to_numeric(
            df["store_count"],
            errors="coerce"
        ).fillna(0)

    return df

def load_final_store_supply():
    path = os.path.join(OUT_DIR, "store_supply.csv")

    if not os.path.exists(path):
        print("store_supply.csv 없음: 분석결과의 store_count 그대로 사용")
        return pd.DataFrame(columns=["dong", "category", "store_count"])

    supply = pd.read_csv(path, encoding="utf-8-sig")

    supply["dong"] = supply["dong"].astype(str).str.strip()
    supply["category"] = supply["category"].astype(str).str.strip()
    supply["store_count"] = pd.to_numeric(
        supply["store_count"],
        errors="coerce"
    ).fillna(0)

    supply = supply.drop_duplicates(subset=["dong", "category"])

    return supply

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
            avg_location_score=("location_score", "mean"),

            external_ratio=("external_ratio", "mean"),
            sales_shortage=("sales_shortage", "mean"),
            amount_growth_24_vs_23=("amount_growth_24_vs_23", "mean")
        )
    )

    summary["consumption_activation"] = (
        summary["total_amount"] / summary["avg_total_demand_pop"].replace(0, pd.NA)
    ).fillna(0)
    

    summary["map_name"] = map_name

    return summary

def load_cell_consumption():
    cell_path = os.path.join(OUT_DIR, "consumption_monthly_cell.csv")

    if not os.path.exists(cell_path):
        print("consumption_monthly_cell.csv 파일이 없어 격자를 표시하지 않습니다.")
        return pd.DataFrame()

    cell = pd.read_csv(cell_path, encoding="utf-8-sig")
    cell = cell[cell["category"].isin(TARGET_CATEGORIES)].copy()

    cell["xcdn"] = pd.to_numeric(cell["xcdn"], errors="coerce")
    cell["ycdn"] = pd.to_numeric(cell["ycdn"], errors="coerce")
    cell["amount"] = pd.to_numeric(cell["amount"], errors="coerce").fillna(0)
    cell["count"] = pd.to_numeric(cell["count"], errors="coerce").fillna(0)
    cell["customer"] = pd.to_numeric(cell["customer"], errors="coerce").fillna(0)

    cell = cell.dropna(subset=["xcdn", "ycdn"])

    return cell

def attach_grid_store_count(cell, result):
    """
    격자별 업소수 추정
    - 행정동 업소수를 격자 소비비율 기반으로 분배
    """

    if cell.empty:
        return cell

    temp = cell.copy()

    temp["amount"] = pd.to_numeric(
        temp["amount"],
        errors="coerce"
    ).fillna(0)

    # -------------------------------------------------
    # 행정동+업종 총 소비금액
    # -------------------------------------------------

    dong_total = (
        temp.groupby(["dong", "category"], as_index=False)
        .agg(
            dong_amount=("amount", "sum")
        )
    )

    temp = temp.merge(
        dong_total,
        on=["dong", "category"],
        how="left"
    )

    # -------------------------------------------------
    # 소비 비율 계산
    # -------------------------------------------------

    temp["amount_ratio"] = (
        temp["amount"]
        / temp["dong_amount"].replace(0, pd.NA)
    ).fillna(0)

    # -------------------------------------------------
    # analyze_market.py 결과의 업소수 사용
    # -------------------------------------------------

    supply = (
        result.groupby(["dong", "category"], as_index=False)
        .agg(
            dong_store_count=("store_count", "mean")
        )
    )

    temp = temp.merge(
        supply,
        on=["dong", "category"],
        how="left",
        suffixes=("","_supply")
    )

    temp["dong_store_count"] = pd.to_numeric(
        temp["dong_store_count"],
        errors="coerce"
    ).fillna(0)

    # -------------------------------------------------
    # 격자별 업소수 배분
    # -------------------------------------------------

    temp["grid_store_count"] = (
        temp["dong_store_count"]
        * temp["amount_ratio"]
    )

    return temp

def grid_color_by_value(value, vmin, vmax):
    if vmax <= vmin:
        return "#fee5d9"

    ratio = (value - vmin) / (vmax - vmin)
    ratio = max(0, min(1, ratio))

    if ratio >= 0.85:
        return "#99000d"
    elif ratio >= 0.65:
        return "#cb181d"
    elif ratio >= 0.45:
        return "#ef3b2c"
    elif ratio >= 0.25:
        return "#fb6a4a"
    elif ratio >= 0.10:
        return "#fcae91"
    else:
        return "#fee5d9"


def make_grid_bounds(x, y, transformer, size=500):
    half = size / 2

    corners = [
        (x - half, y - half),
        (x - half, y + half),
        (x + half, y + half),
        (x + half, y - half),
        (x - half, y - half),
    ]

    bounds = []
    for cx, cy in corners:
        lon, lat = transformer.transform(cx, cy)
        bounds.append([lat, lon])

    return bounds

def add_index_legend(m, title, metric_name, description):
    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 9999;
        background-color: white;
        padding: 12px;
        border: 2px solid gray;
        border-radius: 6px;
        font-size: 12px;
        min-width:230px;
    ">
        <b>지도 해석</b><br>
        진한 색: {metric_name} 상대적으로 높음<br>
        연한 색: {metric_name} 상대적으로 낮음<br><br><br>
        
        <b>{title}</b><br><br>

        <span style="background:#fff5f0; padding:2px 12px;"></span>
        0.00 ~ 0.10 : 매우 낮음<br>

        <span style="background:#fee0d2; padding:2px 12px;"></span>
        0.10 ~ 0.25 : 낮음<br>

        <span style="background:#fcbba1; padding:2px 12px;"></span>
        0.25 ~ 0.45 : 보통 이하<br>

        <span style="background:#fc9272; padding:2px 12px;"></span>
        0.45 ~ 0.65 : 보통<br>

        <span style="background:#fb6a4a; padding:2px 12px;"></span>
        0.65 ~ 0.85 : 높음<br>

        <span style="background:#a50f15; padding:2px 12px;"></span>
        0.85 ~ 1.00 : 매우 높음<br>


        <hr>
        <b>지표:</b> {metric_name}<br>
        ※ {description}
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))

def add_grid_heat_layer(m, cell, categories, target_dongs=None, layer_name="격자 소비 밀집도"):
    if cell.empty:
        return

    grid = cell[cell["category"].isin(categories)].copy()

    if target_dongs is not None:
        grid = grid[grid["dong"].isin(target_dongs)].copy()

    if grid.empty:
        return

    grid = (
        grid.groupby(["dong", "cell_id"], as_index=False)
        .agg(
            xcdn=("xcdn", "median"),
            ycdn=("ycdn", "median"),
            grid_amount=("amount", "sum"),
            grid_count=("count", "sum"),
            grid_customer=("customer", "sum"),
            grid_store_count=("grid_store_count", "sum")
        )
    )


    grid["cell_id"] = grid["cell_id"].astype(str).str.strip()

    positive = grid[grid["grid_amount"] > 0]["grid_amount"]

    if len(positive) == 0:
        return

    vmin = positive.quantile(0.05)
    vmax = positive.quantile(0.95)

    if vmax <= vmin:
        vmin = positive.min()
        vmax = positive.max()

    # 색상별 소비금액 구간 계산
    breaks = [
        vmin,
        vmin + (vmax - vmin) * 0.10,
        vmin + (vmax - vmin) * 0.25,
        vmin + (vmax - vmin) * 0.45,
        vmin + (vmax - vmin) * 0.65,
        vmin + (vmax - vmin) * 0.85,
        vmax
    ]

    color_legend_html = f"""
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        z-index: 9999;
        background-color: white;
        padding: 12px;
        border: 2px solid gray;
        border-radius: 6px;
        font-size: 12px;">
        <b>{layer_name} 색상 구간</b><br>
        <span style="background:#fee5d9; padding:2px 12px;"></span>
        {breaks[0]:,.0f} ~ {breaks[1]:,.0f}원<br>
        <span style="background:#fcae91; padding:2px 12px;"></span>
        {breaks[1]:,.0f} ~ {breaks[2]:,.0f}원<br>
        <span style="background:#fb6a4a; padding:2px 12px;"></span>
        {breaks[2]:,.0f} ~ {breaks[3]:,.0f}원<br>
        <span style="background:#ef3b2c; padding:2px 12px;"></span>
        {breaks[3]:,.0f} ~ {breaks[4]:,.0f}원<br>
        <span style="background:#cb181d; padding:2px 12px;"></span>
        {breaks[4]:,.0f} ~ {breaks[5]:,.0f}원<br>
        <span style="background:#99000d; padding:2px 12px;"></span>
        {breaks[5]:,.0f}원 이상<br>
        <hr>
        ※ 하위 5%~상위 95% 기준으로 색상 구간 산정
    </div>
    """
    m.get_root().html.add_child(folium.Element(color_legend_html))

    transformer = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)

    fg = folium.FeatureGroup(name=layer_name, show=True)

    
    for _, r in grid.iterrows():
        bounds = make_grid_bounds(r["xcdn"], r["ycdn"], transformer, size=500)
        color = grid_color_by_value(r["grid_amount"], vmin, vmax)


        popup = f"""
        <b>행정동:</b> {r['dong']}<br>
        <b>cell_id:</b> {r['cell_id']}<br>

        <hr>

        <b>격자 소비금액:</b> {r['grid_amount']:,.0f}원<br>
        <b>격자 소비건수:</b> {r['grid_count']:,.0f}건<br>
        <b>격자 소비자수:</b> {r['grid_customer']:,.0f}명<br>
        <b>격자 업소수:</b> {round(r['grid_store_count'])}개<br>
        """
        

        folium.Polygon(
            locations=bounds,
            color="#555555",
            weight=0.7,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            opacity=0.85,
            popup=folium.Popup(popup, max_width=350)
        ).add_to(fg)

        
  
    fg.add_to(m)
    
def make_activation_map(boundary, summary, map_name, cell, categories):
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
    gdf.loc[gdf["dong"].str.contains("□| |\\?", regex=True, na=False), "dong"] = ""

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

    gdf["store_count"] = (
        gdf["store_count"]
        .round(0)
        .astype(int)
    )
    
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

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="위성지도",
        overlay=False,
        control=True
    ).add_to(m)

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
            "fillOpacity": 0.50 if raw_value >= 0 else 0.10,
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

    add_index_legend(
        m,
        title=f"{map_name} 인구 대비 소비 활성도 행정동 색상 구간",
        metric_name="인구 대비 소비 활성도",
        description="해당 업종의 소비금액을 평균 총수요인구로 나눈 상대지수"
    )    

    non_zoom_gdf = gdf[~gdf["dong"].isin(ZOOM_DONGS)].copy()

    add_grid_heat_layer(
        m,
        cell,
        categories,
        target_dongs=None,
        layer_name=f"{map_name} 격자 소비 밀집도",
    )
    
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

        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="위성지도",
            overlay=False,
            control=True
        ).add_to(zoom_map)

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

        add_index_legend(                m,
            title=f"{map_name} 입지추천점수",
            metric_name="입지추천점수",
            description="소비규모, 수요인구, 성장률, 외부유입, 공급부족을 종합한 상대지수"
        )

              
        add_grid_heat_layer(
            zoom_map,
            cell,
            categories,
            target_dongs=ZOOM_DONGS,
            layer_name=f"{map_name} 도심권 격자 소비 밀집도"
        )


        folium.LayerControl().add_to(zoom_map)

        zoom_save_path = os.path.join(
            MAP_DIR,
            f"{safe_name(map_name)}_도심권확대_인구대비소비활성도_업소수지도.html"
        )

        zoom_map.save(zoom_save_path)
        print("도심권 확대 저장:", zoom_save_path)

    return gdf

def make_recommendation_score_map(boundary, summary, map_name, cell, categories):
    gdf = boundary.merge(
        summary,
        on="dong_key",
        how="left",
        suffixes=("_boundary", "_data")
    )

    if "dong_data" in gdf.columns:
        gdf["dong"] = gdf["dong_data"].fillna(gdf["dong_boundary"])
    else:
        gdf["dong"] = gdf["dong_boundary"]

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

    gdf["store_count"] = (
        gdf["store_count"]
        .round(0)
        .astype(int)
    )

    # 입지추천점수 기준 정규화
    valid = gdf["avg_location_score"] > 0
    gdf["recommend_norm"] = 0.0

    if valid.sum() > 0:
        values = gdf.loc[valid, "avg_location_score"]
        vmin = values.quantile(0.05)
        vmax = values.quantile(0.95)

        if vmax == vmin:
            gdf.loc[valid, "recommend_norm"] = 0.6
        else:
            gdf.loc[valid, "recommend_norm"] = (
                (gdf.loc[valid, "avg_location_score"] - vmin) / (vmax - vmin)
            ).clip(0, 1)

    center_geom = gdf.to_crs(epsg=5179).geometry.centroid.to_crs(epsg=4326)
    center = [center_geom.y.mean(), center_geom.x.mean()]

    m = folium.Map(location=center, zoom_start=12, tiles="cartodbpositron")

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="위성지도",
        overlay=False,
        control=True
    ).add_to(m)

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
        caption=f"{map_name} 입지추천점수"
    )

    def style_function(feature):
        value = feature["properties"].get("recommend_norm", 0)
        raw_score = feature["properties"].get("avg_location_score", 0)

        return {
            "fillColor": colormap(value),
            "color": "black",
            "weight": 2.5,
            "fillOpacity": 0.58 if raw_score >= 0 else 0.12,
        }

    folium.GeoJson(
        gdf,
        name=f"{map_name}_입지추천점수",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "dong",
                "avg_location_score",
                "recommend_norm",
                "total_amount",
                "store_count",
                "avg_total_demand_pop",
                "consumption_activation",
                "total_count",
                "total_customer"
            ],
            aliases=[
                "행정동",
                "평균 입지추천점수",
                "추천점수 상대지수",
                "총 소비금액",
                "현재 업소 수",
                "평균 총수요인구",
                "인구 대비 소비활성도",
                "소비건수",
                "소비자수"
            ],
            localize=True
        )
    ).add_to(m)

    colormap.add_to(m)

    add_index_legend(
        m,
        title=f"{map_name} 입지추천점수 행정동 색상 구간",
        metric_name="입지추천점수",
        description="소비규모, 수요인구, 성장률, 외부유입, 공급부족을 종합한 상대지수"
    )

    add_grid_heat_layer(
        m,
        cell,
        categories,
        target_dongs=None,
        layer_name=f"{map_name} 격자 소비 밀집도"
    )

    folium.LayerControl().add_to(m)

    save_path = os.path.join(
        MAP_DIR,
        f"{safe_name(map_name)}_입지추천점수지도.html"
    )

    m.save(save_path)
    print("입지추천 지도 저장:", save_path)

def make_score_map(
    boundary,
    summary,
    map_name,
    value_col,
    legend_name,
    save_suffix,
    color_caption,
    cell,
    categories
):
    gdf = boundary.merge(
        summary,
        on="dong_key",
        how="left"
    )

    if "dong_y" in gdf.columns:
        gdf["dong"] = gdf["dong_y"].fillna(gdf["dong_x"])
    elif "dong_x" in gdf.columns:
        gdf["dong"] = gdf["dong_x"]
    

    if value_col not in gdf.columns:
        gdf[value_col] = 0

    gdf[value_col] = pd.to_numeric(
        gdf[value_col],
        errors="coerce"
    ).fillna(0)

    if "store_count" in gdf.columns:
        gdf["store_count"] = (
            pd.to_numeric(gdf["store_count"], errors="coerce")
            .fillna(0)
            .round(0)
            .astype(int)
        )

    valid = gdf[value_col] > 0

    gdf["norm"] = 0.0

    if valid.sum() > 0:
        values = gdf.loc[valid, value_col]

        vmin = values.quantile(0.05)
        vmax = values.quantile(0.95)

        if vmax == vmin:
            gdf.loc[valid, "norm"] = 0.6
        else:
            gdf.loc[valid, "norm"] = (
                (gdf.loc[valid, value_col] - vmin)
                / (vmax - vmin)
            ).clip(0, 1)
            gdf["norm"] = gdf["norm"].round(3)

    center_geom = (
        gdf.to_crs(epsg=5179)
        .geometry.centroid
        .to_crs(epsg=4326)
    )

    center = [
        center_geom.y.mean(),
        center_geom.x.mean()
    ]

    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles="cartodbpositron"
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="위성지도",
        overlay=False,
        control=True
    ).add_to(m)

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
        caption=color_caption
    )

    def style_function(feature):
        value = feature["properties"].get("norm", 0)
        raw_value = feature["properties"].get(value_col, 0)

        return {
            "fillColor": colormap(value),
            "color": "black",
            "weight": 2.5,
            "fillOpacity": 0.50 if raw_value >= 0 else 0.10,
        }

    folium.GeoJson(
        gdf,
        name = map_name,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "dong",
                value_col,
                "norm",
                "total_amount",
                "avg_total_demand_pop",
                "store_count",
                "total_count",
                "total_customer"
            ],
            aliases=[
                "행정동",
                f"{legend_name} 실제값",
                "색상 상대지수",
                "총 소비금액",
                "평균 총수요인구",
                "현재 업소 수",
                "소비건수",
                "소비자수"
            ],
            localize=True
        )
    ).add_to(m)

    colormap.add_to(m)

    add_index_legend(
        m,
        title=f"{map_name} {legend_name} 행정동 색상 구간",
        metric_name=legend_name,
        description=f"{legend_name} 값을 0~1 사이로 정규화한 상대지수"
    )

    save_path = os.path.join(
        MAP_DIR,
        f"{safe_name(map_name)}_{save_suffix}.html"
    )

    add_grid_heat_layer(
        m,
        cell,
        categories,
        target_dongs=None,
        layer_name=f"{map_name} 격자 소비 밀집도"
    )

    folium.LayerControl().add_to(m)

    m.save(save_path)

    print("저장:", save_path)

def make_all_categories_one_map(boundary, result, cell):
    print("통합 레이어 지도 생성 중...")

    map_targets = []

    for cat in FOOD_CATEGORIES:
        map_targets.append((cat, [cat]))

    map_targets.append(("음식점_합본", FOOD_CATEGORIES))

    for cat in CAFE_CATEGORIES:
        map_targets.append((cat, [cat]))

    map_targets.append(("카페_합본", CAFE_CATEGORIES))
    map_targets.append(("전체_합본", FOOD_CATEGORIES + CAFE_CATEGORIES))

    center_geom = boundary.to_crs(epsg=5179).geometry.centroid.to_crs(epsg=4326)
    center = [center_geom.y.mean(), center_geom.x.mean()]

    m = folium.Map(location=center, zoom_start=12, tiles="cartodbpositron")

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="위성지도",
        overlay=False,
        control=True
    ).add_to(m)

    for map_name, categories in map_targets:
        summary = make_map_summary(result, map_name, categories)

        if summary.empty:
            continue

        gdf = boundary.merge(
            summary,
            on="dong_key",
            how="left",
            suffixes=("_boundary", "_data")
        )

        if "dong_data" in gdf.columns:
            gdf["dong"] = gdf["dong_data"].fillna(gdf["dong_boundary"])
        else:
            gdf["dong"] = gdf["dong_boundary"]

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

        gdf["store_count"] = (
            gdf["store_count"]
            .round(0)
            .astype(int)
        )

        valid = gdf["consumption_activation"] > 0
        gdf["activation_norm"] = 0.0

        if valid.sum() > 0:
            values = gdf.loc[valid, "consumption_activation"]
            vmin = values.quantile(0.05)
            vmax = values.quantile(0.95)

            if vmax == vmin:
                gdf.loc[valid, "activation_norm"] = 0.6
            else:
                norm = (gdf.loc[valid, "consumption_activation"] - vmin) / (vmax - vmin)
                gdf.loc[valid, "activation_norm"] = norm.clip(0, 1).astype(float)

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
            caption=f"{map_name} 인구 대비 소비 활성도"
        )

        def style_function(feature, cmap=colormap):
            value = feature["properties"].get("activation_norm", 0)
            raw_value = feature["properties"].get("consumption_activation", 0)

            return {
                "fillColor": cmap(value),
                "color": "black",
                "weight": 2.0,
                "fillOpacity": 0.75 if raw_value >= 0 else 0.08,
            }

        layer_display_name = f"{map_name}"

        fg = folium.FeatureGroup(
            name=layer_display_name,
            show=True
        )

        folium.GeoJson(
            gdf,
            name=f"{map_name}_행정동",
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=[
                    "dong",
                    "consumption_activation",
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
        ).add_to(fg)

        fg.add_to(m)

        add_grid_heat_layer(
            m,
            cell,
            categories,
            target_dongs=None,
            layer_name=f"{map_name} 격자 소비 밀집도"
        )

    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 9999;
        background-color: white;
        padding: 12px;
        border: 2px solid gray;
        border-radius: 6px;
        font-size: 13px;">
        <b>통합 지도</b><br>
        체크박스에서 한식/중식/일식/양식/카페 선택<br>
        행정동 색: 인구 대비 소비 활성도<br>
        격자 색: 격자별 소비금액
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl().add_to(m)

    save_path = os.path.join(
        MAP_DIR,
        "전체업종_통합체크지도.html"
    )

    m.save(save_path)
    print("통합 지도 저장:", save_path)



def main():
    print("1. 행정동 경계 불러오는 중...")
    boundary = load_boundary()

    print("2. 분석 결과 불러오는 중...")
    result = load_analysis_result()

    print("3. 격자 소비데이터 불러오는 중...")
    cell = load_cell_consumption()

    cell = attach_grid_store_count(cell, result)
    
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

        if summary.empty or "dong_key" not in summary.columns:
            print(f"건너뜀: {map_name} 데이터 없음")
            continue

        summary.to_csv(
            os.path.join(MAP_DIR, f"{safe_name(map_name)}_인구대비소비활성도_요약.csv"),
            index=False,
            encoding="utf-8-sig"
        )

        make_activation_map(boundary, summary, map_name, cell, categories)
        make_recommendation_score_map(boundary, summary, map_name, cell, categories)

        make_score_map(
            boundary,
            summary,
            map_name,
            "total_amount",
            "총 소비금액",
            "소비규모지도",
            f"{map_name} 소비 규모",
            cell,
            categories,
        )

        # 외부유입 지도
        make_score_map(
            boundary,
            summary,
            map_name,
            "external_ratio",
            "외부 유입 비율",
            "외부유입지도",
            f"{map_name} 외부 유입 비율",
            cell,
            categories,
        )

        # 공급부족 지도
        make_score_map(
            boundary,
            summary,
            map_name,
            "sales_shortage",
            "공급 부족도",
            "공급부족지도",
            f"{map_name} 공급 부족도",
            cell,
            categories        
        )

        # 성장률 지도
        make_score_map(
            boundary,
            summary,
            map_name,
            "amount_growth_24_vs_23",
            "소비 성장률",
            "성장률지도",
            f"{map_name} 소비 성장률",
            cell,
            categories         
        )

        # 경쟁도 지도
        make_score_map(
            boundary,
            summary,
            map_name,
            "store_count",
            "업소 수",
            "업소밀집지도",
            f"{map_name} 업소 밀집도",
            cell,
            categories
        )
        all_summary.append(summary.assign(map_name=map_name))

    final = pd.concat(all_summary, ignore_index=True)

    final.to_csv(
        os.path.join(MAP_DIR, "전체_인구대비소비활성도_업소수_요약.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    print("완료")
    make_all_categories_one_map(boundary, result, cell)
    print("저장 위치:", MAP_DIR)


if __name__ == "__main__":
    main()