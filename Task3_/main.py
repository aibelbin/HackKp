from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os 
from dotenv import load_dotenv
from supabase import create_client, Client
from groq import Groq
import base64
import uuid
import re
import requests

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
table_name = 'images'

app = FastAPI()

image_directory = ""
API_URL = "http://127.0.0.1:8000/images/{image_name}"


def find_images_by_word(response_object, search_word):
    matching_files = []
    image_data_list = []

    if hasattr(response_object, 'data') and isinstance(response_object.data, list):
        image_data_list = response_object.data
    elif isinstance(response_object, list):
        image_data_list = response_object
    else:
        return None
    
    clean_search_word = search_word.lower()

    for item in image_data_list:
        description = ""
        file_name = ""

        if isinstance(item, dict):
            description = item.get('Description', '').lower()
            file_name = item.get('file_name')
        elif isinstance(item, tuple) and len(item) >= 2:
            file_name = item[0]
            description = str(item[1]).lower()

        if clean_search_word in description:
            if file_name and file_name not in matching_files:
                matching_files.append(file_name)

    return matching_files if matching_files else None


@app.get('/')
def root():
    return("Root")

@app.get('/health')
def health():
    return "healthy"

@app.post('/upload_image')
async def upload_image(image: UploadFile  = File(...), prompt: str = "You are an expert image cataloger. Your task is to provide a detailed, single-paragraph description of the following image. Focus on creating a description rich with searchable keywords. In your description, identify and include: The main subject and any prominent figures or objects. The setting and environment (e.g., indoor, outdoor, city, forest, beach). Specific details and smaller objects in the background and foreground. Key colors, lighting, and textures. The overall mood, atmosphere, and any actions taking place. Combine these elements into a fluid, descriptive paragraph. Do not use lists or bullet points in your final output" ):
    image_byte = await image.read()
    base64_image = base64.b64encode(image_byte).decode('utf-8')
    content_type = image.content_type

    filename = image.filename

    chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                               
                                "url": f"data:{content_type};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            max_tokens=1024,
        )
    response_content = chat_completion.choices[0].message.content
    random_uuid = uuid.uuid4()

    response = (supabase.table(table_name).insert
                ({"id": str(random_uuid), "file_name":filename, "Description": response_content }).execute())
    
    return(response)
    # return {"analysis": response_content}

@app.get("/search")
async def search(word: str = ""):
    responsefromsupa = supabase.table(table_name).select('file_name,Description').execute()
    matching_files = find_images_by_word(responsefromsupa, word)

    if not matching_files:
        raise HTTPException(status_code=404, detail="No matching images found.")
    
    image_urls = [f"/images/{filename}" for filename in matching_files]
    # matching_name = []
    # for f in matching_files:
    #     matching_name.append(f)    
    # for i in matching_name:    
    #     response = requests.post(API_URL,i)
    #     responselist = []
    #     responselist.append(response)   #for use later
    
    return JSONResponse(content={"image_urls": image_urls})

@app.get("/imagesearch")
async def get_image(image_name: str):
    image_path = os.path.join('images', image_name)
    
    if os.path.exists(image_path):
        return FileResponse(image_path)
    else:
        raise HTTPException(status_code=404, detail="Image not found.")

    

