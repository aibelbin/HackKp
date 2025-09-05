import os 
import requests 

API_URL_UPLOAD = "http://127.0.0.1:8000/upload_image"
API_URL_SEARCH = "http://127.0.0.1:8000/search"
API_URL_DOWNLOAD = "http://127.0.0.1:8000/imagesearch"

sourcefolder = 'images'
word = input("Word: ")
download_folder = "download"

def uploadimage():
    for filename in os.listdir(sourcefolder): 
        image_path = os.path.join(sourcefolder, filename)
        with open(image_path, 'rb') as image_binary:
            upload_data = {'image': (filename, image_binary)}
            response = requests.post(API_URL_UPLOAD, files=upload_data)
            print(response)

def downloadImage(word):
    response = requests.get(API_URL_SEARCH, params={"word": word})
    data = response.json()
    print(data)
    
    response = requests.get(API_URL_DOWNLOAD, params={"image_name": data})

    if response.status_code == 200:
        os.makedirs(download_folder, exist_ok=True)
        save_path = os.path.join(download_folder, data)

        with open(save_path, "wb") as f:
            f.write(response.content)

            print(f" Downloaded: {save_path}")
    else:
        print(f" Failed to download: {response.status_code}")

    





downloadImage(word)
# uploadimage()