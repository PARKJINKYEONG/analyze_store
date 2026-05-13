import pandas as pd

path = r"C:\Users\A\Desktop\Proj\store analysis\output_2023_2024\consumption_monthly_cell.csv"

df = pd.read_csv(path, encoding="utf-8-sig")

for cat in ["한식", "중식", "일식", "양식"]:
    temp = df[df["category"] == cat]

    print("\n====================")
    print(cat)

    print("행 개수:", len(temp))
    print("격자 개수:", temp["cell_id"].nunique())
    print("행정동 개수:", temp["dong"].nunique())

    print(temp["dong"].value_counts().head(20))