from pathlib import Path
import re

from pypdf import PdfReader


PATHS = [
    "/Users/thomas/Downloads/S24-3500U20-1.pdf",
    "/Users/thomas/Downloads/S24-3500U20-1-ms.pdf",
    "/Users/thomas/Downloads/s23-3500u20-1.pdf",
    "/Users/thomas/Downloads/s23-3500u20-1-ms.pdf",
    "/Users/thomas/Downloads/s22-3500U20-1-ms.pdf",
    "/Users/thomas/Downloads/s19-3500-02.pdf",
    "/Users/thomas/Downloads/s19-3500u20-1 wjec gcse comp sci. - unit 2 ms s-ms.pdf",
]

PATTERN = re.compile(
    r"html|greenfoot|actor|world|css|tag|hyperlink|scenario|method|class|object|source code|code segment",
    re.IGNORECASE,
)


def main():
    for path in PATHS:
        print(f"### {Path(path).name}")
        if not Path(path).exists():
            print("missing")
            continue
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        lines = [line.strip() for line in text.splitlines() if PATTERN.search(line)]
        for line in lines[:120]:
            print(line[:240])
        print(f"lines={len(lines)} chars={len(text)}")


if __name__ == "__main__":
    main()
