from fastapi import FastAPI, File, UploadFile, HTTPException
import os 
from dotenv import load_dotenv
from supabase import create_client, Client
from groq import Groq
import base64
import uuid

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
table_name = 'images'

app = FastAPI()

image_directory = ""

@app.get('/')
def root():
    return("Root")

@app.get('/health')
def health():
    return "healthy"

@app.post('/upload_image')
async def upload_image(image: UploadFile  = File, prompt: str = "You are an expert image cataloger. Your task is to provide a detailed, single-paragraph description of the following image. Focus on creating a description rich with searchable keywords. In your description, identify and include: The main subject and any prominent figures or objects. The setting and environment (e.g., indoor, outdoor, city, forest, beach). Specific details and smaller objects in the background and foreground. Key colors, lighting, and textures. The overall mood, atmosphere, and any actions taking place. Combine these elements into a fluid, descriptive paragraph. Do not use lists or bullet points in your final output" ):
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

    


    

