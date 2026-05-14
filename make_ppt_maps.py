import os
import pandas as pd
import folium
import branca.colormap as cm

from make_maps import (
    OUT_DIR,
    MAP_DIR,
    FOOD_CATEGORIES,
    CAFE_CATEGORIES,
    TARGET_CATEGORIES,
    load_boundary,
    load_analysis_result,
    load_cell_consumption,
    load_store_grid_count,
    make_map_summary,
    add_grid_heat_layer,
    #add_store_count_circle,
)


PPT_MAP_DIR = os.path.join(MAP_DIR, "ppt_maps")
os.makedirs(PPT_MAP_DIR, exist_ok=True)


def make_ppt_single_map(boundary, result, cell, store_grid, map_name, categories):
    summary = make_map_summary(result, map_name, categories)

    if summary.empty:
        print("데이터 없음:", map_name)
        return

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
        "total_amount",
        "total_count",
        "total_customer",
        "avg_total_demand_pop",
        "store_count",
        "category_count",
        "avg_location_score",
        "consumption_activation"
    ]

    for col in fill_cols:
        if col not in gdf.columns:
            gdf[col] = 0

        gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0)

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

    center_geom = gdf.to_crs(epsg=5179).geometry.centroid.to_crs(epsg=4326)
    center = [center_geom.y.mean(), center_geom.x.mean()]

    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles="cartodbpositron"
    )

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

    def style_function(feature):
        value = feature["properties"].get("activation_norm", 0)
        raw_value = feature["properties"].get("consumption_activation", 0)

        return {
            "fillColor": colormap(value),
            "color": "black",
            "weight": 2.3,
            "fillOpacity": 0.58 if raw_value > 0 else 0.12,
        }

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
                "total_count",
                "total_customer",
                "avg_location_score"
            ],
            aliases=[
                "행정동",
                "인구 대비 소비 활성도",
                "총 소비금액",
                "평균 총수요인구",
                "업소 수",
                "소비건수",
                "소비자수",
                "평균 입지추천점수"
            ],
            localize=True
        )
    ).add_to(m)

    colormap.add_to(m)

    #add_store_count_circle(m, gdf)

    add_grid_heat_layer(
        m,
        cell,
        categories,
        target_dongs=None,
        layer_name=f"{map_name} 격자 소비 밀집도",
        store_grid=store_grid
    )

    legend_html = f"""
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
        <b>{map_name} PPT용 지도</b><br>
        진한 색: 인구 대비 소비 활성도 높음<br>
        원 안 숫자: 해당 업종 업소 수<br>
        격자 색: 격자별 소비금액
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False).add_to(m)

    save_path = os.path.join(PPT_MAP_DIR, f"PPT_07_{map_name}_지도.html")
    m.save(save_path)

    print("PPT 지도 저장:", save_path)


def main():
    print("PPT용 지도 생성 시작")

    boundary = load_boundary()
    result = load_analysis_result()
    cell = load_cell_consumption()
    store_grid = load_store_grid_count()

    make_ppt_single_map(
        boundary,
        result,
        cell,
        store_grid,
        "음식점_합본",
        FOOD_CATEGORIES
    )

    make_ppt_single_map(
        boundary,
        result,
        cell,
        store_grid,
        "카페_합본",
        CAFE_CATEGORIES
    )

    make_ppt_single_map(
        boundary,
        result,
        cell,
        store_grid,
        "전체_합본",
        TARGET_CATEGORIES
    )

    print("\nPPT용 지도 생성 완료")
    print("저장 위치:", PPT_MAP_DIR)


if __name__ == "__main__":
    main()