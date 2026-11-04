"""
Secure document text extraction and validation utility.

Supports:
- PDF (.pdf)
- Plain Text (.txt)
- Microsoft Word (.docx)

Security & Integrity Guarantees:
- Enforces strict file size limits (default 10 MB).
- Validates file extensions, MIME types, and binary magic signatures.
- Processes files in-memory without persistent disk writes or arbitrary filesystem execution.
- Validates extracted text is non-empty and handles corrupted/malformed files safely.
"""

import io
import os
import zipfile
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from pypdf import PdfReader
from docx import Document

# Maximum allowed file upload size: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

# Magic number signatures
# PDF starts with %PDF- (0x25 0x50 0x44 0x46 0x2D)
PDF_MAGIC = b"%PDF-"
# DOCX is a ZIP archive, starting with PK\x03\x04
ZIP_MAGIC = b"PK\x03\x04"

ALLOWED_MIME_TYPES = {
    ".pdf": {"application/pdf", "application/x-pdf", "application/octet-stream"},
    ".txt": {"text/plain", "text/plain; charset=utf-8", "application/octet-stream"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/x-zip-compressed",
        "application/octet-stream",
    },
}


def validate_file_metadata(filename: str, content_type: str | None) -> str:
    """
    Validate file extension and MIME type.
    Returns normalized lowercase extension (e.g. '.pdf').
    """
    if not filename or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing or has no file extension.",
        )

    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file extension '{ext}'. "
                f"Allowed extensions are: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            ),
        )

    # Validate content_type if provided
    if content_type:
        clean_content_type = content_type.split(";")[0].strip().lower()
        allowed_mimes = ALLOWED_MIME_TYPES.get(ext, set())
        # Check if MIME matches or is generic stream
        if clean_content_type not in allowed_mimes and "text/" not in clean_content_type:
            # Let's verify if MIME is definitely mismatched
            # E.g. image/jpeg for a .pdf or video/mp4 for .txt
            if not clean_content_type.startswith("application/") and not clean_content_type.startswith("text/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"MIME type '{content_type}' is invalid for extension '{ext}'.",
                )

    return ext


def validate_file_signature(ext: str, content: bytes) -> None:
    """
    Validate magic bytes for binary formats (PDF and DOCX).
    For plain text, ensure it decodes as valid text and is not binary executable.
    """
    if ext == ".pdf":
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match a valid PDF signature (missing %PDF header).",
            )
    elif ext == ".docx":
        if not content.startswith(ZIP_MAGIC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match a valid DOCX signature (missing ZIP magic bytes).",
            )
    elif ext == ".txt":
        # Check for null bytes or executable headers (e.g., ELF, Mach-O, PE)
        if b"\x00" in content[:1024]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TXT file contains binary null bytes and is not valid text.",
            )


def extract_text_from_pdf(content: bytes) -> str:
    """Extract readable text from PDF bytes."""
    try:
        reader = PdfReader(io.BytesIO(content))
        if len(reader.pages) == 0:
            raise ValueError("PDF document has no pages.")

        extracted_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                extracted_parts.append(page_text.strip())

        text = "\n\n".join(extracted_parts).strip()
        if not text:
            raise ValueError("PDF contains no extractable text (it may be scanned images or empty).")
        return text
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from PDF: {str(e)}",
        ) from e


def extract_text_from_txt(content: bytes) -> str:
    """Extract text from plain text file bytes using UTF-8 / latin-1 fallback."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to decode text file: {str(e)}",
            ) from e

    cleaned = text.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TXT file is empty or contains only whitespace.",
        )
    return cleaned


def extract_text_from_docx(content: bytes) -> str:
    """Extract text from DOCX file bytes."""
    try:
        stream = io.BytesIO(content)
        # Verify it's a valid zip archive first
        if not zipfile.is_zipfile(stream):
            raise ValueError("File is not a valid zip archive.")

        stream.seek(0)
        doc = Document(stream)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        # Also extract table text if present
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)

        text = "\n\n".join(paragraphs).strip()
        if not text:
            raise ValueError("DOCX document contains no text content.")
        return text
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from DOCX document: {str(e)}",
        ) from e


async def process_uploaded_document(
    file: UploadFile,
    max_size: int = MAX_FILE_SIZE_BYTES,
) -> Tuple[str, str, int]:
    """
    Validate, read, and extract text from an uploaded document.
    Returns: (extracted_text, filename, file_size_bytes)
    """
    filename = file.filename or ""
    content_type = file.content_type

    ext = validate_file_metadata(filename, content_type)

    # Read file content safely in chunks to enforce size limit in-memory
    content = bytearray()
    chunk_size = 64 * 1024  # 64 KB chunks

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {max_size // (1024 * 1024)} MB.",
            )

    raw_bytes = bytes(content)
    file_size = len(raw_bytes)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # Validate file magic signatures
    validate_file_signature(ext, raw_bytes)

    # Extract text based on file format
    if ext == ".pdf":
        extracted_text = extract_text_from_pdf(raw_bytes)
    elif ext == ".txt":
        extracted_text = extract_text_from_txt(raw_bytes)
    elif ext == ".docx":
        extracted_text = extract_text_from_docx(raw_bytes)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{ext}'.",
        )

    return extracted_text, filename, file_size

