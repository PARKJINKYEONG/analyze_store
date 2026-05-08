import pandas as pd
from pathlib import Path

input_folder = Path("C:\\Users\\A\\Desktop\\데이터\\3. 구미 소비데이터\\2024년\\2024_09월_소비")
output_folder = Path("C:\\Users\\A\\Desktop\\데이터\\3. 구미 소비데이터\\2024년\\변환완료\\ 2024_09월_소비")
output_folder.mkdir(exist_ok=True)

encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"]

for csv_file in input_folder.glob("*.csv"):
    print(f"\n처리 중: {csv_file.name}")

    success = False

    for enc in encodings:
        try:
            df = pd.read_csv(csv_file, encoding=enc)

            output_path = output_folder / f"{csv_file.stem}_엑셀용.csv"

            df.to_csv(
                output_path,
                index=False,
                encoding="utf-8-sig"
            )

            print(f"성공: {enc}")
            print(f"저장 완료: {output_path.name}")

            success = True
            break

        except UnicodeDecodeError:
            print(f"인코딩 실패: {enc}")

        except Exception as e:
            print(f"오류: {enc} / {e}")

    if not success:
        print(f"변환 실패: {csv_file.name}")

print("\n전체 변환 완료")