from supabase import Client, create_client
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
supabase: Client = create_client(url, key)
table_name = 'images'

response = (supabase.table(table_name).select("*").execute())

filename_description_map = {item['file_name']: item['Description'] for item in response.data}

print(filename_description_map)



with open(imagetosearch, 'rb') as file_content:
    payload = {'image': (filename, file_content)}
    response = requests.post(DESCRIPTION_URL, files=payload )
    data =  response.json()
    
# set 0 to 10 grade of sentiment analysis to find the image






