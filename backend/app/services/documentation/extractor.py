import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

import pymupdf
import docx

MAX_DOC_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
MAX_PDF_PAGES = 50
MAX_EXTRACTED_CHARS = 250_000

IGNORED_SUBDIRS = {
    "node_modules",
    "venv",
    ".venv",
    "env",
    "dist",
    "build",
    "out",
    "target",
    "bin",
    "obj",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".git",
    ".svn",
    ".idea",
    ".vscode",
}

SUPPORTED_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".pdf",
    ".docx",
}


@dataclass
class DocumentSection:
    heading: str
    content: str
    page_number: Optional[int] = None
    line_number: Optional[int] = None


@dataclass
class ExtractedDocument:
    relative_path: str
    filename: str
    file_format: str  # "markdown" | "text" | "rst" | "pdf" | "docx"
    text: str
    char_count: int
    word_count: int
    page_count: int
    status: str  # "success" | "partial" | "empty_scanned_image" | "corrupt_or_encrypted" | "unsupported"
    warning: Optional[str] = None
    headings: List[str] = field(default_factory=list)
    sections: List[DocumentSection] = field(default_factory=list)
    pages: List[Dict[str, Any]] = field(default_factory=list)


class DocumentExtractor:
    """
    Safely reads and extracts structured text from documentation files
    (Markdown, TXT, RST, PDF, DOCX) in a submitted project.
    Strictly avoids executing or importing any student code.
    Enforces file size, page count, and character limits.
    """

    @classmethod
    def discover_documents(
        cls, project_dir: Path, relative_paths: Optional[List[str]] = None
    ) -> List[Tuple[Path, str]]:
        """
        Discovers valid documentation files in the project directory.
        Returns a deduplicated list of (full_path, relative_path).
        """
        discovered: Dict[str, Tuple[Path, str]] = {}

        if relative_paths:
            for rel in relative_paths:
                norm_rel = rel.replace("\\", "/").strip("/")
                full_p = (project_dir / norm_rel).resolve()
                if not str(full_p).startswith(str(project_dir.resolve())):
                    continue
                if full_p.is_file():
                    ext = full_p.suffix.lower()
                    if ext in SUPPORTED_EXTENSIONS or full_p.stem.lower() in {"readme", "srs", "report", "license"}:
                        discovered[norm_rel] = (full_p, norm_rel)

        # Also walk project directory to catch files not in database or freshly extracted
        if project_dir.exists():
            for root, dirs, files in os.walk(project_dir):
                dirs[:] = [d for d in dirs if d not in IGNORED_SUBDIRS and not d.startswith(".")]
                for f in files:
                    full_p = Path(root) / f
                    try:
                        rel = str(full_p.relative_to(project_dir)).replace("\\", "/")
                    except ValueError:
                        continue
                    ext = full_p.suffix.lower()
                    base = full_p.stem.lower()
                    if ext in SUPPORTED_EXTENSIONS or base in {"readme", "srs", "report"}:
                        if rel not in discovered:
                            discovered[rel] = (full_p, rel)

        return sorted(list(discovered.values()), key=lambda x: (0 if "readme" in x[1].lower() else 1, x[1]))

    @classmethod
    def extract(cls, full_path: Path, relative_path: str) -> ExtractedDocument:
        """
        Extract text, headings, and structure from a single documentation file.
        """
        filename = full_path.name
        ext = full_path.suffix.lower()

        # 1. Format classification
        if ext in {".md", ".markdown"}:
            fmt = "markdown"
        elif ext == ".rst":
            fmt = "rst"
        elif ext == ".pdf":
            fmt = "pdf"
        elif ext == ".docx":
            fmt = "docx"
        elif ext == ".txt" or full_path.stem.lower() in {"readme", "srs", "report"}:
            fmt = "text"
        else:
            fmt = "unsupported"

        # 2. Check existence and file size
        if not full_path.exists():
            return ExtractedDocument(
                relative_path=relative_path,
                filename=filename,
                file_format=fmt,
                text="",
                char_count=0,
                word_count=0,
                page_count=0,
                status="corrupt_or_encrypted",
                warning=f"Document file '{filename}' was not found on disk.",
            )

        try:
            file_size = full_path.stat().st_size
        except Exception as e:
            return ExtractedDocument(
                relative_path=relative_path,
                filename=filename,
                file_format=fmt,
                text="",
                char_count=0,
                word_count=0,
                page_count=0,
                status="corrupt_or_encrypted",
                warning=f"Could not access file metadata: {str(e)}",
            )

        if file_size > MAX_DOC_FILE_SIZE_BYTES:
            return ExtractedDocument(
                relative_path=relative_path,
                filename=filename,
                file_format=fmt,
                text="",
                char_count=0,
                word_count=0,
                page_count=0,
                status="partial",
                warning=f"File exceeds maximum size limit ({MAX_DOC_FILE_SIZE_BYTES // (1024*1024)}MB). Skipped for safety.",
            )

        # 3. Format-specific extraction
        if fmt == "markdown":
            return cls._extract_markdown(full_path, relative_path)
        elif fmt == "text":
            return cls._extract_text(full_path, relative_path)
        elif fmt == "rst":
            return cls._extract_rst(full_path, relative_path)
        elif fmt == "pdf":
            return cls._extract_pdf(full_path, relative_path)
        elif fmt == "docx":
            return cls._extract_docx(full_path, relative_path)
        else:
            return ExtractedDocument(
                relative_path=relative_path,
                filename=filename,
                file_format="unsupported",
                text="",
                char_count=0,
                word_count=0,
                page_count=0,
                status="unsupported",
                warning=f"File format '{ext}' is not supported for documentation text extraction.",
            )

    @classmethod
    def _extract_markdown(cls, full_path: Path, relative_path: str) -> ExtractedDocument:
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return ExtractedDocument(
                relative_path=relative_path,
                filename=full_path.name,
                file_format="markdown",
                text="",
                char_count=0,
                word_count=0,
                page_count=1,
                status="corrupt_or_encrypted",
                warning=f"Failed to read markdown file: {str(e)}",
            )

        warning = None
        if len(content) > MAX_EXTRACTED_CHARS:
            content = content[:MAX_EXTRACTED_CHARS]
            warning = f"Content truncated to {MAX_EXTRACTED_CHARS} characters."

        lines = content.splitlines()
        headings: List[str] = []
        sections: List[DocumentSection] = []

        current_heading = "Preamble"
        current_lines: List[str] = []
        heading_line_num = 1

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Check markdown heading: # Heading
            match = re.match(r"^(#{1,6})\s+(.+)$", line_stripped)
            is_underline_h1 = (
                i + 1 < len(lines)
                and re.match(r"^={3,}\s*$", lines[i + 1].strip())
                and len(line_stripped) > 0
                and not line_stripped.startswith("#")
            )
            is_underline_h2 = (
                i + 1 < len(lines)
                and re.match(r"^-{3,}\s*$", lines[i + 1].strip())
                and len(line_stripped) > 0
                and not line_stripped.startswith("#")
            )

            if match:
                if current_lines:
                    sections.append(
                        DocumentSection(
                            heading=current_heading,
                            content="\n".join(current_lines).strip(),
                            line_number=heading_line_num,
                        )
                    )
                    current_lines = []
                h_title = match.group(2).strip()
                headings.append(h_title)
                current_heading = h_title
                heading_line_num = i + 1
            elif is_underline_h1 or is_underline_h2:
                if current_lines:
                    sections.append(
                        DocumentSection(
                            heading=current_heading,
                            content="\n".join(current_lines).strip(),
                            line_number=heading_line_num,
                        )
                    )
                    current_lines = []
                h_title = line_stripped
                headings.append(h_title)
                current_heading = h_title
                heading_line_num = i + 1
            else:
                current_lines.append(line)

        if current_lines:
            sections.append(
                DocumentSection(
                    heading=current_heading,
                    content="\n".join(current_lines).strip(),
                    line_number=heading_line_num,
                )
            )

        words = len(content.split())
        return ExtractedDocument(
            relative_path=relative_path,
            filename=full_path.name,
            file_format="markdown",
            text=content,
            char_count=len(content),
            word_count=words,
            page_count=1,
            status="success" if not warning else "partial",
            warning=warning,
            headings=headings,
            sections=sections,
            pages=[{"page_number": 1, "text": content[:5000], "headings": headings}],
        )

    @classmethod
    def _extract_text(cls, full_path: Path, relative_path: str) -> ExtractedDocument:
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return ExtractedDocument(
                relative_path=relative_path,
                filename=full_path.name,
                file_format="text",
                text="",
                char_count=0,
                word_count=0,
                page_count=1,
                status="corrupt_or_encrypted",
                warning=f"Failed to read text file: {str(e)}",
            )

        warning = None
        if len(content) > MAX_EXTRACTED_CHARS:
            content = content[:MAX_EXTRACTED_CHARS]
            warning = f"Content truncated to {MAX_EXTRACTED_CHARS} characters."

        lines = content.splitlines()
        headings: List[str] = []
        sections: List[DocumentSection] = []

        current_heading = "Header / Preamble"
        current_lines: List[str] = []
        heading_line_num = 1

        heading_regex = re.compile(
            r"^(?:\d+[\.\)]\s+)?([A-Z][A-Za-z0-9\s\-_:]{3,60})$"
        )

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Underline headings
            is_underlined = (
                i + 1 < len(lines)
                and re.match(r"^[=\-~_]{3,}\s*$", lines[i + 1].strip())
                and len(line_stripped) > 0
            )
            # Section keywords like "1. Introduction", "2. Architecture"
            is_numbered = bool(re.match(r"^(?:Section\s+)?\d+(?:\.\d+)*\s+[A-Z]", line_stripped))
            is_all_caps = (
                len(line_stripped) >= 4
                and len(line_stripped) <= 60
                and line_stripped.isupper()
                and not any(c in line_stripped for c in "{};()[]<>=")
            )

            if is_underlined or is_numbered or is_all_caps:
                if current_lines:
                    sections.append(
                        DocumentSection(
                            heading=current_heading,
                            content="\n".join(current_lines).strip(),
                            line_number=heading_line_num,
                        )
                    )
                    current_lines = []
                headings.append(line_stripped)
                current_heading = line_stripped
                heading_line_num = i + 1
            else:
                current_lines.append(line)

        if current_lines:
            sections.append(
                DocumentSection(
                    heading=current_heading,
                    content="\n".join(current_lines).strip(),
                    line_number=heading_line_num,
                )
            )

        words = len(content.split())
        return ExtractedDocument(
            relative_path=relative_path,
            filename=full_path.name,
            file_format="text",
            text=content,
            char_count=len(content),
            word_count=words,
            page_count=1,
            status="success" if not warning else "partial",
            warning=warning,
            headings=headings,
            sections=sections,
            pages=[{"page_number": 1, "text": content[:5000], "headings": headings}],
        )

    @classmethod
    def _extract_rst(cls, full_path: Path, relative_path: str) -> ExtractedDocument:
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return ExtractedDocument(
                relative_path=relative_path,
                filename=full_path.name,
                file_format="rst",
                text="",
                char_count=0,
                word_count=0,
                page_count=1,
                status="corrupt_or_encrypted",
                warning=f"Failed to read rst file: {str(e)}",
            )

        warning = None
        if len(content) > MAX_EXTRACTED_CHARS:
            content = content[:MAX_EXTRACTED_CHARS]
            warning = f"Content truncated to {MAX_EXTRACTED_CHARS} characters."

        lines = content.splitlines()
        headings: List[str] = []
        sections: List[DocumentSection] = []

        current_heading = "Preamble"
        current_lines: List[str] = []
        heading_line_num = 1

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            is_underlined = (
                i + 1 < len(lines)
                and re.match(r"^[=\-~`'^" + r'"]{3,}\s*$', lines[i + 1].strip())
                and len(line_stripped) > 0
            )

            if is_underlined:
                if current_lines:
                    sections.append(
                        DocumentSection(
                            heading=current_heading,
                            content="\n".join(current_lines).strip(),
                            line_number=heading_line_num,
                        )
                    )
                    current_lines = []
                headings.append(line_stripped)
                current_heading = line_stripped
                heading_line_num = i + 1
            else:
                current_lines.append(line)

        if current_lines:
            sections.append(
                DocumentSection(
                    heading=current_heading,
                    content="\n".join(current_lines).strip(),
                    line_number=heading_line_num,
                )
            )

        words = len(content.split())
        return ExtractedDocument(
            relative_path=relative_path,
            filename=full_path.name,
            file_format="rst",
            text=content,
            char_count=len(content),
            word_count=words,
            page_count=1,
            status="success" if not warning else "partial",
            warning=warning,
            headings=headings,
            sections=sections,
            pages=[{"page_number": 1, "text": content[:5000], "headings": headings}],
        )

    @classmethod
    def _extract_docx(cls, full_path: Path, relative_path: str) -> ExtractedDocument:
        try:
            doc = docx.Document(str(full_path))
        except Exception as e:
            return ExtractedDocument(
                relative_path=relative_path,
                filename=full_path.name,
                file_format="docx",
                text="",
                char_count=0,
                word_count=0,
                page_count=1,
                status="corrupt_or_encrypted",
                warning=f"Failed to open DOCX document: {str(e)}",
            )

        text_parts: List[str] = []
        headings: List[str] = []
        sections: List[DocumentSection] = []

        current_heading = "Introduction / Overview"
        current_lines: List[str] = []

        for p in doc.paragraphs:
            p_text = p.text.strip()
            if not p_text:
                continue

            style_name = p.style.name.lower() if p.style else ""
            is_heading_style = "heading" in style_name or "title" in style_name
            is_bold_short = (
                len(p_text) <= 80
                and any(r.bold for r in p.runs)
                and len(p.runs) > 0
                and all(r.bold for r in p.runs if r.text.strip())
            )

            if is_heading_style or is_bold_short:
                if current_lines:
                    sections.append(
                        DocumentSection(
                            heading=current_heading,
                            content="\n".join(current_lines).strip(),
                        )
                    )
                    current_lines = []
                headings.append(p_text)
                current_heading = p_text
            else:
                current_lines.append(p_text)

            text_parts.append(p_text)

        # Include table contents
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    table_rows.append(" | ".join(row_cells))
            if table_rows:
                current_lines.extend(table_rows)
                text_parts.extend(table_rows)

        if current_lines:
            sections.append(
                DocumentSection(
                    heading=current_heading,
                    content="\n".join(current_lines).strip(),
                )
            )

        full_text = "\n\n".join(text_parts)
        warning = None
        if len(full_text) > MAX_EXTRACTED_CHARS:
            full_text = full_text[:MAX_EXTRACTED_CHARS]
            warning = f"Content truncated to {MAX_EXTRACTED_CHARS} characters."

        words = len(full_text.split())
        return ExtractedDocument(
            relative_path=relative_path,
            filename=full_path.name,
            file_format="docx",
            text=full_text,
            char_count=len(full_text),
            word_count=words,
            page_count=1,
            status="success" if not warning else "partial",
            warning=warning,
            headings=headings,
            sections=sections,
            pages=[{"page_number": 1, "text": full_text[:5000], "headings": headings}],
        )

    @classmethod
    def _extract_pdf(cls, full_path: Path, relative_path: str) -> ExtractedDocument:
        try:
            doc = pymupdf.open(str(full_path))
        except Exception as e:
            return ExtractedDocument(
                relative_path=relative_path,
                filename=full_path.name,
                file_format="pdf",
                text="",
                char_count=0,
                word_count=0,
                page_count=0,
                status="corrupt_or_encrypted",
                warning=f"Failed to open PDF document: {str(e)}",
            )

        if doc.is_encrypted:
            doc.close()
            return ExtractedDocument(
                relative_path=relative_path,
                filename=full_path.name,
                file_format="pdf",
                text="",
                char_count=0,
                word_count=0,
                page_count=0,
                status="corrupt_or_encrypted",
                warning="PDF document is password protected / encrypted.",
            )

        total_pages = len(doc)
        pages_to_read = min(total_pages, MAX_PDF_PAGES)
        warnings: List[str] = []

        if total_pages > MAX_PDF_PAGES:
            warnings.append(
                f"PDF has {total_pages} pages; extraction limited to first {MAX_PDF_PAGES} pages."
            )

        all_page_texts: List[str] = []
        headings: List[str] = []
        sections: List[DocumentSection] = []
        page_records: List[Dict[str, Any]] = []

        current_heading = "Document Header"
        current_lines: List[str] = []
        current_page_num = 1

        for page_idx in range(pages_to_read):
            page_num = page_idx + 1
            try:
                page = doc.load_page(page_idx)
                page_text = page.get_text("text") or ""
            except Exception as e:
                warnings.append(f"Failed to extract page {page_num}: {str(e)}")
                page_text = ""

            all_page_texts.append(page_text)
            page_headings: List[str] = []

            lines = page_text.splitlines()
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue

                # Heading detection in PDF:
                # 1. Numbered section heading: "1. Introduction", "2.1 System Architecture"
                is_numbered_heading = bool(
                    re.match(r"^(?:[0-9]{1,2}(?:\.[0-9]{1,2})*\s+)[A-Z][A-Za-z0-9\s\-_:]{3,60}$", line_str)
                )
                # 2. All-caps short line: "SYSTEM ARCHITECTURE", "CONCLUSION AND FUTURE WORK"
                is_all_caps = (
                    len(line_str) >= 4
                    and len(line_str) <= 60
                    and line_str.isupper()
                    and not any(c in line_str for c in "{};()[]<>=")
                )
                # 3. Leading keyword headers: "Abstract", "References", "Methodology"
                is_keyword_header = bool(
                    re.match(
                        r"^(?:Abstract|Introduction|Objectives?|Requirements?|Methodology|Architecture|System Design|Implementation|Testing|Results|Evaluation|Conclusion|References?|Bibliography)$",
                        line_str,
                        re.IGNORECASE,
                    )
                )

                if is_numbered_heading or is_all_caps or is_keyword_header:
                    if current_lines:
                        sections.append(
                            DocumentSection(
                                heading=current_heading,
                                content="\n".join(current_lines).strip(),
                                page_number=current_page_num,
                            )
                        )
                        current_lines = []
                    headings.append(line_str)
                    page_headings.append(line_str)
                    current_heading = line_str
                    current_page_num = page_num
                else:
                    current_lines.append(line_str)

            page_records.append({
                "page_number": page_num,
                "text": page_text[:2000],
                "headings": page_headings,
            })

        if current_lines:
            sections.append(
                DocumentSection(
                    heading=current_heading,
                    content="\n".join(current_lines).strip(),
                    page_number=current_page_num,
                )
            )

        doc.close()

        full_text = "\n\n".join(all_page_texts)
        if len(full_text) > MAX_EXTRACTED_CHARS:
            full_text = full_text[:MAX_EXTRACTED_CHARS]
            warnings.append(f"Content truncated to {MAX_EXTRACTED_CHARS} characters.")

        word_count = len(full_text.split())

        # Check for scanned image / empty text layer
        if word_count < 10 and total_pages > 0:
            return ExtractedDocument(
                relative_path=relative_path,
                filename=full_path.name,
                file_format="pdf",
                text="",
                char_count=0,
                word_count=0,
                page_count=total_pages,
                status="empty_scanned_image",
                warning="PDF contains scanned images or no extractable text layer. Text extraction is unavailable without OCR.",
                headings=[],
                sections=[],
                pages=page_records,
            )

        return ExtractedDocument(
            relative_path=relative_path,
            filename=full_path.name,
            file_format="pdf",
            text=full_text,
            char_count=len(full_text),
            word_count=word_count,
            page_count=total_pages,
            status="partial" if warnings else "success",
            warning="; ".join(warnings) if warnings else None,
            headings=headings,
            sections=sections,
            pages=page_records,
        )
