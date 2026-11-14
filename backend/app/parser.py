import re 
from collections.abc import Iterator

import pymupdf

def clean_text(text: str) -> str:
    text = re.sub(r"-\n(\w)",r"\1", text)
    text = re.sub(r"[ \t]+"," ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text

def parse_pdf(path:str) -> Iterator[tuple[int, str]]:
    with pymupdf.open(path) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = clean_text(page.get_text())
            if text:
                yield page_number, text