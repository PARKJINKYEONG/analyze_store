import os
import glob
import pandas as pd

BASE_DIR = r"E:\데이터"
CONSUME_ROOT = os.path.join(BASE_DIR, "구미 소비데이터")

PROJECT_DIR = r"C:\Users\GAENG2\Desktop\analyze_store_main"
OUT_DIR = os.path.join(PROJECT_DIR, "output_2023_2024")

YEARS = [2023, 2024]

JAPAN_KEYS = [
    "일식", "초밥", "스시", "참치", "라멘", "우동",
    "돈까스", "돈가스", "돈카츠", "카츠", "가츠",
    "덮밥", "소바", "메밀", "텐동", "이자카야",
    "오마카세", "사케", "야키", "야끼"
]


def read_table_auto(path):
    for enc in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    raise ValueError(f"읽기 실패: {path}")


def get_month_folders():
    folders = []
    for year in YEARS:
        year_dir = os.path.join(CONSUME_ROOT, f"{year}년")
        folders.extend(glob.glob(os.path.join(year_dir, f"{year}_*월_소비")))
    return sorted(folders)


def main():
    rows = []

    for folder in get_month_folders():
        files = glob.glob(os.path.join(folder, "*DD_R_2*"))

        for f in files:
            if "DD2" in os.path.basename(f):
                continue

            df = read_table_auto(f)

            # 원본 컬럼 확인용
            cols = df.columns.tolist()

            for _, row in df.iterrows():
                text = " ".join([
                    str(row.get("mc_bzc1_nm", "")),
                    str(row.get("mc_bzc2_nm", "")),
                    str(row.get("mc_bzc3_nm", "")),
                    str(row.get("store_name", "")),
                    str(row.get("업소명", "")),
                    str(row.get("가맹점명", "")),
                    str(row.get("addr", "")),
                    str(row.get("주소", "")),
                    str(row.get("소재지", "")),
                ])

                compact = text.replace(" ", "").lower()

                hit_keys = [k for k in JAPAN_KEYS if k in compact]

                if hit_keys:
                    rows.append({
                        "file": os.path.basename(f),
                        "folder": os.path.basename(folder),
                        "hit_keys": ",".join(hit_keys),
                        "mc_bzc1_nm": row.get("mc_bzc1_nm", ""),
                        "mc_bzc2_nm": row.get("mc_bzc2_nm", ""),
                        "mc_bzc3_nm": row.get("mc_bzc3_nm", ""),
                        "store_name": row.get("store_name", row.get("업소명", row.get("가맹점명", ""))),
                        "addr": row.get("addr", row.get("주소", row.get("소재지", ""))),
                        "cell_id": row.get("cell_id", ""),
                        "xcdn": row.get("xcdn", ""),
                        "ycdn": row.get("ycdn", ""),
                    })

    result = pd.DataFrame(rows)

    save_path = os.path.join(OUT_DIR, "일식_원본후보_확인.csv")
    result.to_csv(save_path, index=False, encoding="utf-8-sig")

    print("저장 완료:", save_path)
    print("후보 개수:", len(result))

    if not result.empty:
        print(result[["hit_keys", "mc_bzc1_nm", "mc_bzc2_nm", "mc_bzc3_nm", "store_name", "cell_id"]].head(30))


if __name__ == "__main__":
    main()