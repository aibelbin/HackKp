import os 
import requests 

API_URL_UPLOAD = "http://127.0.0.1:8000/upload_image"
API_URL_SEARCH = "http://127.0.0.1:8000/search"
API_URL_DOWNLOAD = "http://127.0.0.1:8000/imagesearch"

sourcefolder = 'images'
word = input("Word: ")

def uploadimage():
    for filename in os.listdir(sourcefolder): 
        image_path = os.path.join(sourcefolder, filename)
        with open(image_path, 'rb') as image_binary:
            upload_data = {'image': (filename, image_binary)}
            response = requests.post(API_URL_UPLOAD, files=upload_data)
            print(response)

def downloadImage(word):
    response =  requests.get(API_URL_SEARCH, word)
    data = response.json()
    image_urls = data['image_urls']
    possible_list = []
    for i in image_urls:
        new = os.path.basename(i)
        possible_list.append(new)
        # print(possible_list)
    
    for i in possible_list:
        download_folder = "download"
        reponse = requests.post(API_URL_DOWNLOAD, params={'image_name': i})
        save_path = os.path.join(download_folder, i)
        with open(save_path, 'wb') as f:
            f.write(response.content)
            print("File Saved")



        
    
    
    # word_to_send = os.path.basename(response)
    # print(word_to_send)


downloadImage(word)
# uploadimage()