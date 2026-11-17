"""Hybrid PDF checks; OCR engine calls are mocked, with real PDF rendering."""
import os
import unittest
from io import BytesIO
from unittest.mock import patch

import fitz
import pytesseract
from PIL import Image, ImageDraw

from app.services.pdf_extraction import PdfExtractionError, extract_pdf


def make_pdf(kinds):
    doc = fitz.open()
    for kind in kinds:
        page = doc.new_page(width=300, height=300)
        if kind == 'text':
            page.insert_text((25, 50), 'A selectable page of project text.')
        elif kind == 'scan':
            image = Image.new('RGB', (500, 100), 'white')
            ImageDraw.Draw(image).text((15, 30), 'Scanned page text', fill='black')
            image_data = BytesIO()
            image.save(image_data, format='PNG')
            image.close()
            page.insert_image(fitz.Rect(20, 20, 270, 70), stream=image_data.getvalue())
    data = doc.tobytes()
    doc.close()
    return data


class HybridPdfTests(unittest.TestCase):
    def test_text_pdf_uses_no_ocr(self):
        with patch('pytesseract.image_to_string', side_effect=AssertionError('OCR should not run')):
            result = extract_pdf(make_pdf(['text']))
        self.assertIn('selectable', result['extracted_text'])
        self.assertEqual(result['extraction_method'], 'direct')
        self.assertEqual(result['ocr_page_count'], 0)

    def test_scanned_page_mocked_ocr(self):
        with patch('pytesseract.image_to_string', return_value='Scanned page text'):
            result = extract_pdf(make_pdf(['scan']))
        self.assertEqual(result['extracted_text'], 'Scanned page text')
        self.assertEqual(result['extraction_method'], 'ocr')
        self.assertEqual(result['ocr_page_count'], 1)

    def test_mixed_pages_preserve_order_and_warn(self):
        with patch('pytesseract.image_to_string', side_effect=['Scan text', '']):
            result = extract_pdf(make_pdf(['text', 'scan', 'scan']))
        self.assertLess(result['extracted_text'].index('selectable'), result['extracted_text'].index('Scan text'))
        self.assertEqual(result['extraction_method'], 'mixed')
        self.assertEqual(result['ocr_page_count'], 2)
        self.assertIn('Page 3', result['warnings'][0])

    def test_blank_and_corrupt_files(self):
        with patch('pytesseract.image_to_string', return_value=''):
            with self.assertRaisesRegex(PdfExtractionError, 'No text'):
                extract_pdf(make_pdf(['scan']))
        with self.assertRaises(PdfExtractionError):
            extract_pdf(b'not a PDF')

    def test_missing_ocr_and_timeout(self):
        with patch('pytesseract.image_to_string', side_effect=pytesseract.TesseractNotFoundError()):
            with self.assertRaisesRegex(PdfExtractionError, 'unavailable'):
                extract_pdf(make_pdf(['scan']))
        with patch('pytesseract.image_to_string', side_effect=RuntimeError('timeout')):
            with self.assertRaisesRegex(PdfExtractionError, 'timed out'):
                extract_pdf(make_pdf(['scan']))

    def test_page_and_ocr_page_limits(self):
        with patch.dict(os.environ, {'PDF_MAX_PAGES': '1'}):
            with self.assertRaisesRegex(PdfExtractionError, 'too many pages'):
                extract_pdf(make_pdf(['text', 'text']))
        with patch.dict(os.environ, {'PDF_MAX_OCR_PAGES': '1'}):
            with patch('pytesseract.image_to_string', return_value='Page text'):
                with self.assertRaisesRegex(PdfExtractionError, 'OCR page limit'):
                    extract_pdf(make_pdf(['scan', 'scan']))


if __name__ == '__main__':
    unittest.main()
