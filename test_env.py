from dotenv import load_dotenv
import os

loaded = load_dotenv()

print("Loaded:", loaded)
print("SECRET_KEY:", os.getenv("SECRET_KEY"))
print("GEMINI_API_KEY:", os.getenv("GEMINI_API_KEY"))