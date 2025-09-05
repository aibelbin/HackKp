from supabase import create_client
import os 
from dotenv import load_dotenv
import ollama
import requests

load_dotenv()

imagetosearch = 'imagetosearch/lotofthings.jpg'
filename = os.path.basename(imagetosearch)
DESCRIPTION_URL = "http://127.0.0.1:8000/upload_image"

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)
table_name = 'images'

response = (supabase.table(table_name).select("*").execute())

filename_description_map = {item['file_name']: item['Description'] for item in response.data}

print(filename_description_map)



with open(imagetosearch, 'rb') as file_content:
    payload = {'image': (filename, file_content)}
    response = requests.post(DESCRIPTION_URL, files=payload )
    data =  response.json()
    best_file = None
    best_score = -1.0
    for fname, desc in filename_description_map.items():
        prompt = (
            "Rate the similarity between these two image descriptions on a scale of 0 to 10 (0 = not similar, 10 = identical). "
            "Return only the number.\n\n"
            f"A: {data}\n"
            f"B: {desc}"
        )
        res = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
        content = res.get("message", {}).get("content", "").strip()
        s = ''.join(ch for ch in content if (ch.isdigit() or ch == '.'))
        try:
            score = float(s) if s else 0.0
        except:
            score = 0.0
        if score > best_score:
            best_score = score
            best_file = fname
    print(best_file)






