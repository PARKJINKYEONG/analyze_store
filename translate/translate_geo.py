import geopandas as gpd
from pathlib import Path

# 원본 shp 폴더
input_folder = Path(
    r"C:\Users\A\Desktop\데이터\행정구역경계\bnd_dong_37050_2025_2Q"
)

# 변환 저장 폴더
output_folder = input_folder / "변환완료"
output_folder.mkdir(exist_ok=True)

# shp 파일 찾기
shp_files = list(input_folder.glob("*.shp"))

if len(shp_files) == 0:
    raise FileNotFoundError("shp 파일을 찾지 못했습니다.")

for shp_path in shp_files:

    print(f"\n처리 중: {shp_path.name}")

    gdf = None

    # 가능한 인코딩 시도
    encodings = ["cp949", "euc-kr", "utf-8"]

    for enc in encodings:
        try:
            gdf = gpd.read_file(shp_path, encoding=enc)

            print(f"읽기 성공 인코딩: {enc}")
            print("컬럼:", gdf.columns.tolist())

            break

        except Exception as e:
            print(f"실패: {enc} / {e}")

    if gdf is None:
        print("읽기 실패")
        continue

    # UTF-8 shapefile로 다시 저장
    out_shp = output_folder / f"{shp_path.stem}_utf8.shp"

    gdf.to_file(
        out_shp,
        encoding="utf-8"
    )

    print(f"UTF-8 저장 완료: {out_shp.name}")

print("\n전체 변환 완료")