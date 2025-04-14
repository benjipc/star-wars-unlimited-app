import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import requests
from io import BytesIO
from app.config import CONFIG


class CardDetailWindow:
    def __init__(self, parent, card_app, card):
        self.parent = parent
        self.card_app = card_app
        self.card = card
        self.is_front_image = True
        self.image_path = ""
        self.image_folder = "images"

        os.makedirs(self.image_folder, exist_ok=True)

        self.detail_window = tk.Toplevel(self.parent)
        self.detail_window.title(f"Card Info - {card.get('name', '')}")
        self.detail_window.geometry("600x700")

        self.create_ui()

    def create_ui(self):
        canvas = tk.Canvas(self.detail_window)
        scrollbar = ttk.Scrollbar(self.detail_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.add_image_section(scrollable_frame)
        self.add_card_info(scrollable_frame)

    def add_image_section(self, parent):
        image_frame = tk.Frame(parent)
        image_frame.pack(pady=10)

        self.image_label = tk.Label(image_frame)
        self.image_label.pack()

        self.load_image()

        if self.card.get("BackArt"):
            flip_button = tk.Button(parent, text="Flip Card", command=self.flip_image)
            flip_button.pack(pady=2)

        view_full_button = tk.Button(parent, text="View Full Art", command=self.open_full_art)
        view_full_button.pack(pady=5)

    def load_image(self):
        image_url = self.card.get("FrontArt") if self.is_front_image else self.card.get("BackArt")
        if not image_url:
            return

        image_name = f"{self.card['card_key']}_{'front' if self.is_front_image else 'back'}.jpg"
        self.image_path = os.path.join(self.image_folder, image_name)

        if os.path.exists(self.image_path):
            image_data = Image.open(self.image_path)
        else:
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                image_data = Image.open(BytesIO(response.content))
                image_data.save(self.image_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
                return

        card_type = self.card.get("type", "").lower()
        if not self.is_front_image or card_type not in ["leader", "base"]:
            image_data = image_data.resize((375, 525), Image.Resampling.LANCZOS)
        else:
            image_data = image_data.resize((525, 375), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(image_data)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

    def flip_image(self):
        self.is_front_image = not self.is_front_image
        self.load_image()

    def open_full_art(self):
        art_window = tk.Toplevel(self.parent)
        art_window.title("Full Art View")

        full_img = Image.open(self.image_path)
        photo = ImageTk.PhotoImage(full_img)

        img_label = tk.Label(art_window, image=photo)
        img_label.image = photo
        img_label.pack()

    def add_card_info(self, parent):
        tk.Label(parent, text=self.card.get("name", "Unknown Card"), font=("Arial", 14, "bold")).pack(pady=5)

        # Card Stats
        stats_text = (
            f"Type: {self.card.get('type', '')}\n"
            f"Arenas: {self.card.get('arenas', '')}\n"
            f"Aspect: {self.card.get('aspect', '')}\n"
            f"Cost: {self.card.get('cost', '')}   Power: {self.card.get('power', '')}   Health: {self.card.get('health', '')}\n"
            f"Traits: {', '.join(self.card.get('Traits', []))}\n"
        )

        tk.Label(parent, text=stats_text, font=("Arial", 10), justify="left").pack(pady=5, padx=10, anchor="w")

        # Card Text
        front_text = self.card.get("FrontText", "")
        if front_text:
            tk.Label(parent, text="Front Text:", font=("Arial", 12, "bold")).pack(pady=(5, 2), padx=10, anchor="w")
            tk.Label(parent, text=front_text, wraplength=550, justify="left", font=("Arial", 10, "italic")).pack(pady=(0, 10), padx=10, anchor="w")

        back_text = self.card.get("BackText", "")
        if back_text:
            tk.Label(parent, text="Back Text:", font=("Arial", 12, "bold")).pack(pady=(5, 2), padx=10, anchor="w")
            tk.Label(parent, text=back_text, wraplength=550, justify="left", font=("Arial", 10, "italic")).pack(pady=(0, 10), padx=10, anchor="w")