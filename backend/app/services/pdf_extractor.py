from pathlib import Path
from typing import Dict, Any, List

def extract_pdf_content(pdf_path: Path) -> Dict[str, Any]:
    """
    Extracts plain text and page metadata from PDF documentation reports using PyMuPDF (fitz).
    """
    if not pdf_path.exists() or not pdf_path.is_file():
        return {"pages": 0, "text": "", "page_texts": []}

    page_texts: List[Dict[str, Any]] = []
    full_text = ""

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        pages_count = len(doc)

        for page_num in range(pages_count):
            page = doc[page_num]
            text = page.get_text("text") or ""
            full_text += f"\n--- Page {page_num + 1} ---\n" + text
            page_texts.append({
                "page": page_num + 1,
                "text": text
            })
        doc.close()
    except Exception:
        # Fallback text extraction if fitz not installed
        try:
            full_text = pdf_path.read_text(encoding="utf-8", errors="ignore")
            pages_count = 1
            page_texts = [{"page": 1, "text": full_text}]
        except Exception:
            pages_count = 0
            full_text = ""

    return {
        "pages": pages_count,
        "text": full_text,
        "page_texts": page_texts,
    }
