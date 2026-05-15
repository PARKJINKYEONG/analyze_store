import os
import time
import glob
import requests
import numpy as np
import pandas as pd
from pyproj import Transformer

from analyze_market import (
    read_table_auto,
    classify_store_name,
    extract_dong,
    legal_to_admin_dong,
    TARGET_CATEGORIES,
)


PROJECT_DIR = r"C:\Users\Gaeng2\Desktop\Proj\store analysis"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")
STORE_DIR = os.path.join(PROJECT_DIR, "data", "store")

KAKAO_REST_API_KEY = "cf242874425f9d4c02c28cd8ee90623e"


def geocode_kakao(address):
    if pd.isna(address) or str(address).strip() == "":
        return None, None

    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {"query": str(address)}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)

        if r.status_code != 200:
            print("API 오류:", r.status_code)
            return None, None

        data = r.json()
        docs = data.get("documents", [])

        if len(docs) == 0:
            return None, None

        lon = float(docs[0]["x"])
        lat = float(docs[0]["y"])

        return lon, lat

    except Exception as e:
        print("지오코딩 오류:", e)
        return None, None

def load_store_raw():
    files = glob.glob(os.path.join(STORE_DIR, "*.csv")) + glob.glob(os.path.join(STORE_DIR, "*.xlsx"))
    frames = []

    for f in files:
        df = read_table_auto(f)

        name_col = next((c for c in ["업소명", "상호명", "사업장명"] if c in df.columns), None)
        addr_col = next((c for c in ["소재지(지번)", "소재지전체주소", "소재지(도로명)", "도로명주소", "주소"] if c in df.columns), None)

        if name_col is None or addr_col is None:
            continue

        temp = pd.DataFrame()
        temp["store_name"] = df[name_col]
        temp["addr"] = df[addr_col]

        temp["legal_dong"] = temp["addr"].apply(extract_dong)
        temp["dong"] = temp["legal_dong"].apply(legal_to_admin_dong)
        temp["category"] = temp.apply(
            lambda row: classify_store_name(row["store_name"], row["addr"]),
            axis=1
        )

        frames.append(temp)

    if not frames:
        raise ValueError("업소 파일을 찾지 못했습니다.")

    stores = pd.concat(frames, ignore_index=True)
    stores = stores.dropna(subset=["dong"])
    stores = stores[stores["category"].isin(TARGET_CATEGORIES)].copy()
    stores = stores.drop_duplicates(subset=["store_name", "addr"])

    return stores


def assign_store_to_nearest_cell(stores):
    cell_path = os.path.join(OUT_DIR, "consumption_monthly_cell.csv")
    cell = pd.read_csv(cell_path, encoding="utf-8-sig")

    grid = (
        cell[["dong", "cell_id", "xcdn", "ycdn"]]
        .dropna()
        .drop_duplicates()
        .copy()
    )

    grid["xcdn"] = pd.to_numeric(grid["xcdn"], errors="coerce")
    grid["ycdn"] = pd.to_numeric(grid["ycdn"], errors="coerce")
    grid = grid.dropna(subset=["xcdn", "ycdn"])

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)

    xs = []
    ys = []

    for lon, lat in zip(stores["lon"], stores["lat"]):
        if pd.isna(lon) or pd.isna(lat):
            xs.append(np.nan)
            ys.append(np.nan)
        else:
            x, y = transformer.transform(lon, lat)
            xs.append(x)
            ys.append(y)

    stores["store_x"] = xs
    stores["store_y"] = ys
    stores = stores.dropna(subset=["store_x", "store_y"]).copy()

    grid_points = grid[["xcdn", "ycdn"]].to_numpy()
    store_points = stores[["store_x", "store_y"]].to_numpy()

    assigned_rows = []

    for i, point in enumerate(store_points):
        dists = np.sqrt(((grid_points - point) ** 2).sum(axis=1))
        min_idx = dists.argmin()
        min_dist = dists[min_idx]

        # 500m 격자 기준 중심에서 너무 멀면 제외
        if min_dist > 400:
            continue

        g = grid.iloc[min_idx]
        s = stores.iloc[i].copy()

        s["cell_id"] = g["cell_id"]
        s["xcdn"] = g["xcdn"]
        s["ycdn"] = g["ycdn"]
        s["grid_dong"] = g["dong"]
        s["grid_distance"] = min_dist

        assigned_rows.append(s)

    assigned = pd.DataFrame(assigned_rows)

    # 매칭된 업소가 하나도 없을 때도 컬럼 구조는 유지
    if assigned.empty:
        return pd.DataFrame(columns=[
            "store_name", "addr", "legal_dong", "dong", "category",
            "lon", "lat", "store_x", "store_y",
            "cell_id", "xcdn", "ycdn", "grid_dong", "grid_distance"
        ])

    return assigned


def main():
    stores = load_store_raw()

    cache_path = os.path.join(OUT_DIR, "store_geocode_cache.csv")

    if os.path.exists(cache_path):
        cache = pd.read_csv(cache_path, encoding="utf-8-sig")
    else:
        cache = pd.DataFrame(columns=["addr", "lon", "lat"])

    cache_dict = {
        str(row["addr"]): (row["lon"], row["lat"])
        for _, row in cache.iterrows()
    }

    lons = []
    lats = []

    for addr in stores["addr"]:
        addr_key = str(addr)

        if addr_key in cache_dict:
            lon, lat = cache_dict[addr_key]
        else:
            lon, lat = geocode_kakao(addr_key)
            cache_dict[addr_key] = (lon, lat)
            time.sleep(0.15)

        lons.append(lon)
        lats.append(lat)

    stores["lon"] = lons
    stores["lat"] = lats

    new_cache = pd.DataFrame([
        {"addr": k, "lon": v[0], "lat": v[1]}
        for k, v in cache_dict.items()
    ])

    new_cache.to_csv(cache_path, index=False, encoding="utf-8-sig")

    geocoded = assign_store_to_nearest_cell(stores)

    print("geocoded 행 수:", len(geocoded))
    print("geocoded 컬럼:", geocoded.columns.tolist())

    if geocoded.empty:
        raise ValueError(
            "격자에 매칭된 업소가 없습니다. "
            "store_geocode_cache.csv를 삭제하고 다시 실행하거나, "
            "주소 지오코딩 결과(lon/lat)를 확인하세요."
        )

    geocoded.to_csv(
        os.path.join(OUT_DIR, "store_classified_geocoded.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    store_grid_count = (
        geocoded.groupby(["category", "grid_dong", "cell_id", "xcdn", "ycdn"], as_index=False)
        .agg(store_count=("store_name", "count"))
        .rename(columns={"grid_dong": "dong"})
    )

    store_grid_count.to_csv(
        os.path.join(OUT_DIR, "store_grid_count.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    store_supply = (
        geocoded.groupby(["grid_dong", "category"], as_index=False)
        .agg(store_count=("store_name", "count"))
        .rename(columns={"grid_dong": "dong"})
    )

    store_supply.to_csv(
        os.path.join(OUT_DIR, "store_supply_geocoded.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    print("업소 지오코딩 완료")
    print("저장:", os.path.join(OUT_DIR, "store_classified_geocoded.csv"))
    print("저장:", os.path.join(OUT_DIR, "store_grid_count.csv"))
    print("저장:", os.path.join(OUT_DIR, "store_supply_geocoded.csv"))


if __name__ == "__main__":
    main()