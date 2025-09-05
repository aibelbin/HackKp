import os 
import requests 

API_URL = "http://127.0.0.1:8000/upload_image"

sourcefolder = 'images'

def uploadimage():
    for filename in os.listdir(sourcefolder): 
        image_path = os.path.join(sourcefolder, filename)
        with open(image_path, 'rb') as image_binary:
            upload_data = {'image': (filename, image_binary)}
            response = requests.post(API_URL, files=upload_data)
            print(response)

uploadimage()