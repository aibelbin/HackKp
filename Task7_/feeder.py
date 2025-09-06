from supabase import create_client
import os 
from dotenv import load_dotenv
import ollama
import requests

load_dotenv()

objecttosearch = 'objecttosearch'
imagestoupload = 'images'
filename = os.path.basename(objecttosearch)
DESCRIPTION_URL = "http://127.0.0.1:8000/upload_image"
API_URL_DOWNLOAD="http://127.0.0.1:8000/imagesearch"
download_folder = 'download'

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)
table_name = 'objects'

response = (supabase.table(table_name).select("*").execute())

filename_description_map = {item['file_name']: item['Description'] for item in response.data}

# print(filename_description_map)



def openfile():
     for image in os.listdir(objecttosearch):
        image_path = os.path.join(objecttosearch, image)
        return [image, objecttosearch, image_path]


def object_identification():
    path = []
    path = openfile()
    with open(path[2], 'rb') as file_content:
        
        payload = {'image':(path[0], file_content)}
        res = requests.post(DESCRIPTION_URL,files = payload )
        data = res.json()
        return data

data = object_identification()

def listofsimilar(singleimagedata, setofdescriptions):
    similar_files = []
    for file_name, description in setofdescriptions.items():
        prompt = f"Compare these two image descriptions and determine if they show the same or very similar objects. Answer only 'yes' or 'no'.\n\nDescription 1: {singleimagedata}\nDescription 2: {description}"
        response = ollama.chat(model="gpt-oss", messages=[{"role": "user", "content": prompt}])
        answer = response.get("message", {}).get("content", "").strip().lower()
        if "yes" in answer:
            similar_files.append(file_name)
    return similar_files



imagestodownload = []
imagestodownload = listofsimilar(data, filename_description_map)





def image_downloader(image_name):
    response = requests.get(API_URL_DOWNLOAD, params={"image_name": data})

    if response.status_code == 200:
        os.makedirs(download_folder, exist_ok=True)
        save_path = os.path.join(download_folder, data)

        with open(save_path, "wb") as f:
            f.write(response.content)

            print(f" Downloaded: {save_path}")
    else:
        print(f" Failed to download: {response.status_code}")



for i in imagestodownload:
    image_downloader(imagestodownload[i])





#code for creating the database rag system

# def image_uploader():
#     errored = []
#     for image in os.listdir(imagestoupload):
#         image_path = os.path.join(imagestoupload, image)
#         with open(image_path, 'rb') as file_content:
#             payload = {'image': (image, file_content)}
#             response = requests.post(DESCRIPTION_URL, files=payload)
#             print(response)
#             if response.status_code != 200: 
#                 errored.append(image)
            


# image_downloader(best_file)
# image_uploader() for initializing the rag

