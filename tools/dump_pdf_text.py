from pathlib import Path
import sys

from pypdf import PdfReader


def main():
    for raw_path in sys.argv[1:]:
        path = Path(raw_path)
        print(f"\n===== {path.name} =====")
        if not path.exists():
            print("MISSING")
            continue
        reader = PdfReader(path)
        for index, page in enumerate(reader.pages, start=1):
            print(f"\n--- page {index} ---")
            print(page.extract_text() or "")


if __name__ == "__main__":
    main()
