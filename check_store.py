import pandas as pd

path = r"C:\Users\GAENG2\Desktop\analyze_store_main\output_2023_2024\consumption_monthly_cell.csv"
df = pd.read_csv(path, encoding="utf-8-sig")

df["category"] = df["category"].astype(str).str.strip()

print(df["category"].value_counts())
print(df[df["category"] == "일식"].head(20))
print(df[df["category"] == "일식"].groupby("dong")["amount"].sum().sort_values(ascending=False))