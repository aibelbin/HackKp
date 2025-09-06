"""
================= proper working of the code ===================

1. Take an image from assets.  
2. Extract text using two methods in parallel:
   - pytesseract (OCR)  
   - Ollama (AI vision model)  
3. Compare both results to catch any missed text.  
4. Detect language for each text snippet.  
5. Send merged text to Ollama for cleanup & formatting.  
6. Return final text as JSON: { "text": "language" }  

===========================================================
"""



import os
import pytesseract
from PIL import Image
from langdetect import detect
import subprocess
import json

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
IMAGE_NAME = "#"
IMAGE_PATH = os.path.join(ASSETS_DIR, IMAGE_NAME)

def extract_with_tesseract(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return text.strip()
    except Exception as e:
        return f"[Tesseract Error: {str(e)}]"

def extract_with_ollama(image_path):
    try:
        result = subprocess.run(
            ["ollama", "run", "llava", "--image", image_path],
            input="Extract all visible text from this image. Return only the raw text, no explanation.",
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"[Ollama Error: {str(e)}]"

def merge_texts(text1, text2):
    chunks = set()
    for t in [text1, text2]:
        for line in t.splitlines():
            line = line.strip()
            if line:
                chunks.add(line)
    return list(chunks)

def detect_languages(text_chunks):
    result = {}
    for chunk in text_chunks:
        try:
            lang = detect(chunk)
            result[chunk] = lang
        except:
            result[chunk] = "unknown"
    return result

def format_with_ollama(text_dict):
    raw_json = json.dumps(text_dict, ensure_ascii=False, indent=2)
    prompt = f"""
    Clean and correct this OCR output if needed, but keep the structure the same.
    Return only valid JSON in the format:
    {{
      "text": "language"
    }}
    Input JSON:
    {raw_json}
    """
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3"],
            input=prompt,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"[Ollama Correction Error: {str(e)}]"

if __name__ == "__main__":
    print(f"Reading image: {IMAGE_PATH}")

    tesseract_text = extract_with_tesseract(IMAGE_PATH)
    ollama_text = extract_with_ollama(IMAGE_PATH)

    merged_chunks = merge_texts(tesseract_text, ollama_text)
    detected = detect_languages(merged_chunks)

    final_json = format_with_ollama(detected)

    print("\n=== FINAL JSON OUTPUT ===")
    print(final_json)
