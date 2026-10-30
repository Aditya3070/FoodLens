from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

image = Image.open("test.jpg")  # Replace with your image filename

text = pytesseract.image_to_string(image)

print("Extracted Text:")
print(text)