import time
from dotenv import load_dotenv
load_dotenv()

print("1. Testing OCR...")
start = time.time()
from utils.ocr import extract_text
text = extract_text("test.jpg")  # uses the test.jpg you already have
print(f"OCR done in {time.time()-start:.1f}s")
print("Extracted text:", text[:200])

print("\n2. Testing Groq AI call...")
start = time.time()
from utils.groq_ai import analyze_ingredients
result = analyze_ingredients(text if text else "sugar, salt, olive oil")
print(f"AI call done in {time.time()-start:.1f}s")
print(result)