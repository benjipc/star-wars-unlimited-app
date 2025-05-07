from typing import *  # noqa: F403
import tkinter as tk
from tkinter import messagebox
import os
import json
import time
import requests
import logging

from app.config import CONFIG
from app.data_manager import load_cards, load_collection, save_collection
from app.validators import CardValidator
from app.card_detail_window import CardDetailWindow
from app.ui_components import UIComponents
from app.card import ImageManager
from app.app_interfaces import ICardApp


class CardApp(ICardApp):
    def __init__(self, root):
        self.root = root
        self.root.title(CONFIG["window"]["title"])
        self.image_manager = ImageManager(CONFIG["data"]["image_folder"])
        
        # Dynamic window size
        self.setup_window()
        
        # Initialize private attributes for properties
        self._cards = []
        self._collection = {}
        
        # Load data
        self._cards = load_cards()
        self._collection = load_collection()
        os.makedirs(CONFIG["data"]["image_folder"], exist_ok=True)

        self.default_sets = CONFIG["default_sets"]

        # Initialize UI
        self.ui = UIComponents(self)

        # Clean exit handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    @property
    def cards(self) -> List[Dict[str, Any]]:
        return self._cards
    
    @cards.setter
    def cards(self, value: List[Dict[str, Any]]) -> None:
        self._cards = value
    
    @property
    def collection(self) -> Dict[str, Any]:
        return self._collection
    
    @collection.setter
    def collection(self, value: Dict[str, Any]) -> None:
        self._collection = value

    def setup_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = int(screen_width * CONFIG["window"]["width_ratio"])
        height = int(screen_height * CONFIG["window"]["height_ratio"])
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        font_cfg = CONFIG["window"]["font"]
        self.root.option_add("*Font", f"{font_cfg['family']} {font_cfg['size']}")

    def save_collection(self):
        save_collection(self.collection)

    def on_exit(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.save_collection()
            self.root.destroy()

    def display_card_info(self, card):
        CardDetailWindow(self.root, self, card)

    def update_card_data(self):
        sets:str = self.get_set_codes_dialog(self.default_sets)

        valid, message = CardValidator.validate_set_codes(sets)
        if not valid:
            messagebox.showerror("Validation Error", message)
            return

        all_cards = []
        api_config = CONFIG["api"]
        progress_window = None

        try:
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Updating Card Data")
            progress_window.geometry("300x150")
            progress_window.transient(self.root)
            progress_window.grab_set()

            progress_label = tk.Label(progress_window, text="Fetching card data...")
            progress_label.pack(pady=10)
            progress_bar = tk.ttk.Progressbar(progress_window, mode='determinate')
            progress_bar.pack(fill='x', padx=20, pady=10)
            progress_bar['maximum'] = len(sets)
            status_label = tk.Label(progress_window, text="")
            status_label.pack(pady=5)

            for index, set_code in enumerate(sets):
                status_label.config(text=f"Processing set: {set_code}")
                progress_bar['value'] = index
                progress_window.update()

                url = f"{api_config['base_url']}/cards/{set_code}?format=json"
                response_data = None

                for attempt in range(api_config["retry_attempts"]):
                    try:
                        response = requests.get(url, headers=api_config["headers"], timeout=api_config["timeout"])
                        response.raise_for_status()
                        response_data = response.json()
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt < api_config["retry_attempts"] - 1:
                            time.sleep(2 ** attempt)
                            status_label.config(text=f"Retrying {set_code} (attempt {attempt + 2})")
                            progress_window.update()
                        else:
                            raise ConnectionError(f"Failed to fetch data for {set_code}: {e}")

                if "data" in response_data:
                    set_cards:List[Dict[str:Any]] = response_data["data"]
                    normalized_cards = []
                    for card in set_cards:
                        valid, error_message = CardValidator.validate_card_data(card)
                        if not valid:
                            logging.warning(f"Skipping invalid card in {set_code}: {error_message}")
                            continue

                        # Add internal key without discarding other data
                        card_key = f"{card.get('Set', '')}-{card.get('Number', '')}-{card.get('VariantType', 'Normal')}"
                        card["card_key"] = card_key
                        normalized_cards.append(card)

                    all_cards.extend(normalized_cards)
            if not all_cards:
                raise ValueError("No valid cards were found")

            with open(CONFIG["data"]["cards_file"], 'w', encoding='utf-8') as f:
                json.dump(all_cards, f, indent=2, ensure_ascii=False)

            self.cards = all_cards
            self.ui.cards = all_cards
            self.ui.load_table()
            self.ui.load_table(owned_only=True)
            messagebox.showinfo("Success", f"Card data updated successfully.\nTotal cards: {len(all_cards)}")
        except Exception as e:
            logging.error("Failed to update card data", exc_info=True)
            messagebox.showerror("Error", str(e))
        finally:
            if progress_window:
                progress_window.destroy()

    def get_set_codes_dialog(self, default_sets):
        dialog = tk.Toplevel(self.root)
        dialog.title("Set Codes to Update")
        dialog.geometry("400x400")

        tk.Label(dialog, text="Enter Set Codes (one per line):").pack(pady=(10, 5))
        text_box = tk.Text(dialog, wrap="word", height=15, width=40)
        text_box.pack(padx=10, pady=5, fill="both", expand=True)
        text_box.insert("1.0", "\n".join(default_sets))

        result = {"sets": None}
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        def on_ok():
            result["sets"] = text_box.get("1.0", "end").strip().splitlines()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        tk.Button(button_frame, text="Update", command=on_ok, width=12).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=12).pack(side="right", padx=10)

        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

        return result["sets"]
