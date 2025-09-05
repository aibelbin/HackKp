import os
import requests
from datasets import load_dataset
from tqdm import tqdm

def download_hq50k_images():
    """
    Downloads images from the YangGeee/HQ-50K dataset on Hugging Face.
    """
    # 1. Define the dataset name and the folder to save images
    dataset_name = "YangQiee/HQ-50K"
    output_folder = "hq50k_images"
    
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    print(f"Loading dataset '{dataset_name}'...")
    try:
        # 2. Load the 'train' split of the dataset
        dataset = load_dataset(dataset_name, split="train")
    except Exception as e:
        print(f"Failed to load dataset. Error: {e}")
        return

    print("Dataset loaded successfully. Starting download...")

    # 3. Loop through each row in the dataset with a progress bar
    for item in tqdm(dataset):
        # The image URL is in the 'text' column
        image_url = item.get('text')
        
        if not image_url:
            continue

        try:
            # 4. Generate a unique local filename from the URL
            # This extracts the last part of the URL, e.g., 'Case1-1.jpg'
            filename = os.path.basename(image_url)
            save_path = os.path.join(output_folder, filename)

            # 5. Make the request to download the image
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status() # Raise an error for bad responses (4xx or 5xx)

            # 6. Save the image content to the file
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        except requests.exceptions.RequestException as e:
            # This will catch connection errors, timeouts, etc.
            print(f"\nFailed to download {image_url}. Reason: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred for {image_url}. Error: {e}")

    print(f"\nDownload complete. Images are saved in the '{output_folder}' directory.")

# --- Run the download function ---
if __name__ == "__main__":
    download_hq50k_images()

    
