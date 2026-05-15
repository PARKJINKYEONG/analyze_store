import os
import pandas as pd

OUT_DIR = r"C:\Users\A\Desktop\Proj\store analysis\output_2023_2024"

cell_path = os.path.join(OUT_DIR, "consumption_monthly_cell.csv")
consume = pd.read_csv(cell_path, encoding="utf-8-sig")

grid_store = consume.groupby(
    ["year_month", "dong_code", "dong", "category", "cell_id"],
    as_index=False
).agg(
    store_count=("store_count", "max")
)

store_supply = grid_store.groupby(
    ["year_month", "dong_code", "dong", "category"],
    as_index=False
).agg(
    store_count=("store_count", "sum")
)

store_supply["store_count"] = store_supply["store_count"].fillna(0).astype(int)

store_supply.to_csv(
    os.path.join(OUT_DIR, "store_supply.csv"),
    index=False,
    encoding="utf-8-sig"
)

dong_monthly = consume.groupby(
    ["year_month", "dong_code", "dong", "category"],
    as_index=False
).agg(
    amount=("amount", "sum"),
    count=("count", "sum"),
    customer=("customer", "sum")
)

dong_monthly = dong_monthly.merge(
    store_supply,
    on=["year_month", "dong_code", "dong", "category"],
    how="left"
)

dong_monthly["store_count"] = dong_monthly["store_count"].fillna(0).astype(int)

dong_monthly.to_csv(
    os.path.join(OUT_DIR, "consumption_monthly_dong.csv"),
    index=False,
    encoding="utf-8-sig"
)

print("이어쓰기 완료")
print("store_supply.csv 저장 완료")
print("consumption_monthly_dong.csv 저장 완료")