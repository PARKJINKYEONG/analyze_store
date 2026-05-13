import pandas as pd

df = pd.read_csv(
    r"C:\Users\A\Desktop\Proj\store analysis\output_2023_2024\store_classified.csv",
    encoding="utf-8-sig"
)

goa = df[df["dong"] == "옥성면"].copy()

print("옥성면 전체 업소 수:", len(goa))
print(goa["category"].value_counts())

print("\옥성면 일식으로 분류된 업소")
print(goa[goa["category"] == "일식"][["store_name", "addr", "category"]])

print("\옥성면 일식 후보인데 다른 카테고리로 간 업소")
keywords = "돈까스|돈카츠|카츠|파스타|스파게티|스테이크|브런치|레스토랑|양식|피자|버거|샐러드|포케|토스트|샌드위치"
print(
    goa[
        goa["store_name"].astype(str).str.contains(keywords, na=False)
    ][["store_name", "addr", "category"]]
)