"""
Tests for document upload endpoint.
"""

import io
import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from src.api.main import app, get_ollama_client, get_session_manager
from src.api.session_manager import SessionManager

class TestDocumentUpload(unittest.TestCase):
    def setUp(self):
        self.mock_ollama = MagicMock()
        # Mock model existence and chat response
        self.mock_ollama.is_server_online.return_value = True
        self.mock_ollama.is_model_available.return_value = True
        self.mock_ollama.model_name = "llama3.2:3b"
        self.mock_ollama.chat.return_value = {
            "content": "Processed document response",
            "latency_seconds": 0.1,
        }
        self.session_manager = SessionManager()
        app.dependency_overrides[get_ollama_client] = lambda: self.mock_ollama
        app.dependency_overrides[get_session_manager] = lambda: self.session_manager
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def _create_pdf(self, text: str) -> bytes:
        # Minimal PDF with one page containing text using pypdf
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        # Note: pypdf does not support adding text directly without extra libs; use a pre-made simple PDF.
        # Instead, we'll embed the text in a PDF annotation (simpler approach).
        # For test purposes, we can just create an empty PDF; extraction will return empty and raise error.
        # So we use a small pre-generated PDF binary with known text.
        # Here we use a minimal PDF containing the string "Hello PDF" via raw bytes.
        pdf_bytes = b'''%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 44 >> stream
BT
/F1 12 Tf
72 180 Td
(Hello PDF) Tj
ET
endstream
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000065 00000 n 
0000000121 00000 n 
0000000281 00000 n 
0000000382 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
460
%%EOF'''
        return pdf_bytes

    def test_upload_valid_pdf(self):
        pdf_bytes = self._create_pdf("Hello PDF")
        files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
        data = {"prompt": "Summarize", "model": "llama3.2:3b"}
        response = self.client.post("/chat/upload", files=files, data=data)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertIn("response", json)
        self.assertEqual(json["response"], "Processed document response")
        self.assertEqual(json["filename"], "test.pdf")
        self.assertGreater(json["extracted_characters"], 0)

    def test_upload_unsupported_extension(self):
        content = b"dummy"
        files = {"file": ("image.png", content, "image/png")}
        response = self.client.post("/chat/upload", files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported file extension", response.json()["detail"])

    def test_upload_oversized_file(self):
        # 11 MB payload
        large_content = b"0" * (11 * 1024 * 1024)
        files = {"file": ("big.pdf", large_content, "application/pdf")}
        response = self.client.post("/chat/upload", files=files)
        self.assertEqual(response.status_code, 413)
        self.assertIn("exceeds maximum allowed size", response.json()["detail"].lower())

    def test_upload_empty_file(self):
        files = {"file": ("empty.txt", b"", "text/plain")}
        response = self.client.post("/chat/upload", files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Uploaded file is empty", response.json()["detail"].lower())

    def test_upload_malformed_pdf(self):
        # PDF missing %PDF header
        bad_pdf = b"Not a PDF content"
        files = {"file": ("bad.pdf", bad_pdf, "application/pdf")}
        response = self.client.post("/chat/upload", files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn("valid PDF signature", response.json()["detail"].lower())

    def test_model_unavailable(selfn):
        # Simulate model not available
        self.mock_ollama.is_model_available.return_value = False
        pdf_bytes = self._create_pdf("Hello PDF")
        files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
        response = self.client.post("/chat/upload", files=files)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Model '" + self.mock_ollama.model_name + "' is not installed", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()

