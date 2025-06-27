import os
from PIL import Image, ImageTk
import requests
from io import BytesIO
from app.config import CONFIG
from typing import Dict, Any, Tuple, Optional
import logging

class CardImageFetcher:
    @staticmethod
    def get_card_image_path(card: Dict[str, Any], is_front_image: bool) -> str:
        """Get the path to a card image file."""
        card_key = card.get("card_key", "")
        suffix = "front" if is_front_image else "back"
        
        # Make sure the image directory exists
        os.makedirs(CONFIG["data"]["image_folder"], exist_ok=True)
        
        return os.path.join(CONFIG["data"]["image_folder"], f"{card_key}_{suffix}.jpg")
    
    @staticmethod
    def load_card_image(card: Dict[str, Any], is_front_image: bool) -> Tuple[Optional[Image.Image], str]:
        """Load a card image and return both the image object and path.
        Will try to download the image if not found locally."""
        image_path = CardImageFetcher.get_card_image_path(card, is_front_image)
        
        # Try to load local image
        try:
            image_data = Image.open(image_path)
            return image_data, image_path
        except (FileNotFoundError, IOError):
            # If image doesn't exist locally, try to download it
            try:
                image_url = card.get("FrontArt" if is_front_image else "BackArt")
                if not image_url:
                    print(f"No image URL found for card: {card.get('Name')} ({card.get('card_key')})")
                    return None, image_path
                
                print(f"Downloading image from {image_url}")
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    image_data = Image.open(BytesIO(response.content))
                    # Save to local path for future use
                    image_data.save(image_path)
                    print(f"Image saved to {image_path}")
                    return image_data, image_path
                else:
                    print(f"Failed to download image: HTTP {response.status_code}")
                    return None, image_path
            except Exception as e:
                print(f"Error downloading image: {e}")
                return None, image_path
    
    @staticmethod
    def resize_card_image(image_data: Image.Image, card: Dict[str, Any], is_front_image: bool) -> Image.Image:
        """Resize the card image based on card type."""
        card_type = card.get("Type", "").lower()
        
        try:
            # For back images, we need to check if it's horizontal
            if not is_front_image:
                # Most back sides are vertical (375x525)
                return image_data.resize((375, 525), Image.Resampling.LANCZOS)
            
            # For front images, check card type
            if card_type in ["leader", "base"]:
                # Horizontal cards (525x375)
                return image_data.resize((525, 375), Image.Resampling.LANCZOS)
            else:
                # Vertical cards (375x525)
                return image_data.resize((375, 525), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Error resizing image: {e}")
            # Return original if resize fails
            return image_data
    
    @staticmethod
    def create_tk_photo(image_data: Image.Image) -> ImageTk.PhotoImage:
        """Convert PIL image to Tkinter PhotoImage."""
        try:
            return ImageTk.PhotoImage(image_data)
        except Exception as e:
            print(f"Error creating photo: {e}")
            return None