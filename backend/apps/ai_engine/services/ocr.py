import pytesseract
from PIL import Image
import os

def perform_ocr(file_path):
    """
    Extracts text from an image file using Tesseract.
    """
    try:
        if not os.path.exists(file_path):
            return ""
        
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""
