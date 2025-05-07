from PIL import Image
from pathlib import Path
from typing import *
import requests
import io

class ImageManager:
    def __init__(self, image_folder: str):
        self.image_folder = Path(image_folder)
        if not (self.image_folder.exists() and self.image_folder.is_dir()):
            self.image_folder.mkdir(parents=True)

    def get_image(self, image_key: str, download_url: str) -> Optional[Image.Image]:
        image_path = self.image_folder.joinpath(image_key)
        
        # If image doesn't exist, try to download it
        if not image_path.exists():
            try:
                response = requests.get(download_url, stream=True)
                if response.status_code == 200:
                    # Save the image file
                    with open(image_path, 'wb') as out_file:
                        out_file.write(response.content)
                else:
                    print(f"Failed to download image: {download_url}")
                    return None
            except requests.RequestException as e:
                print(f"An error occurred while downloading the image: {e}")
                return None
        
        try:
            # Open and return the image
            return Image.open(str(image_path))
        except Exception as e:
            print(f"Error opening image {image_path}: {e}")
            return None

class Card:
    def __init__(self, card_data, image_manager: ImageManager):
        self.card_data = card_data
        self.image_manager = image_manager

    def __str__(self):
        return f"{self.name} ({self.set_code})"
    
    def name(self) -> str:
        return self.card_data.get("Name", "Unknown Card")
    
    def uid(self) -> str:
        return self.card_data.get("card_key", "Unknown card_key")

    def get_image(self, back: bool = False) -> Optional[Image.Image]:
        image_key = f"{self.uid()}_{'back' if back else 'front'}.jpg"
        image_url = self.card_data.get("BackArtUri" if back else "ArtUri", "")
        
        return self.image_manager.get_image(
            image_key=image_key,
            download_url=image_url
        )