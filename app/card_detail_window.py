import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import json
from app.config import CONFIG
from pathlib import Path
from app.card import Card, ImageManager
from typing import Dict, Any

class CardDetailWindow:
    def __init__(self, parent, card_app, card: Dict[str, Any]):
        self.parent = parent
        self.card = card
        self.card_app = card_app
        self.is_front_image = True
        self.image_path = ""
        self.image_folder = "images"
        
        os.makedirs(self.image_folder, exist_ok=True)

        self.detail_window = tk.Toplevel(self.parent)
        self.detail_window.title(f"Card Info - {card.get('Name', '')}")
        self.detail_window.geometry("600x700")

        self.create_ui()

        self.detail_window.bind("<Enter>", self._bind_scroll)
        self.detail_window.bind("<Leave>", self._unbind_scroll)
        self.detail_window.protocol("WM_DELETE_WINDOW", self._on_close)


    def create_ui(self):
        self.canvas = tk.Canvas(self.detail_window)
        self.scrollbar = ttk.Scrollbar(self.detail_window, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mousewheel scroll binding
        self.scrollable_frame.bind("<Enter>", self._bind_scroll)
        self.scrollable_frame.bind("<Leave>", self._unbind_scroll)

        self.add_image_section(self.scrollable_frame)
        ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill='x', pady=10)
        self.add_card_info(self.scrollable_frame)

    def _bind_scroll(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)      # Windows/macOS
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)        # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)        # Linux scroll down

    def _unbind_scroll(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.delta:  # Windows/macOS
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:  # Linux scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview_scroll(1, "units")

    def _on_close(self):
        self._unbind_scroll()
        self.detail_window.destroy()


    def add_image_section(self, parent):
        image_frame = tk.Frame(parent)
        image_frame.pack(pady=10, fill="x")

        self.image_label = tk.Label(image_frame)
        self.image_label.pack(anchor="center")

        card_key = self.card.get("card_key", "")
        suffix = "back" if not self.is_front_image else "front"
        image_path = os.path.join(CONFIG["data"]["image_folder"], f"{card_key}_{suffix}.jpg")
        
        try:
            image_data = Image.open(image_path)
            self.image_path = image_path
            
            card_type = self.card.get("Type", "").lower()
            if not self.is_front_image or card_type not in ["leader", "base"]:
                image_data = image_data.resize((375, 525), Image.Resampling.LANCZOS)
            else:
                image_data = image_data.resize((525, 375), Image.Resampling.LANCZOS)
                
            photo = ImageTk.PhotoImage(image_data)
            self.image_label.configure(image=photo)
            self.image_label.image = photo  # Keep reference to prevent garbage collection
        except (FileNotFoundError, IOError):
            print(f"Image not found: {image_path}")
            self.image_label.configure(text="Image not found")

        button_frame = tk.Frame(parent)
        button_frame.pack(pady=2)

        if self.card.get("BackArt"):  
            flip_button = tk.Button(button_frame, text="Flip Card", command=self.flip_image)
            flip_button.pack(side="left", padx=5)

        view_full_button = tk.Button(button_frame, text="View Full Art", command=self.open_full_art)
        view_full_button.pack(side="left", padx=5)

        button_frame.pack(anchor="center")

    def flip_image(self):
        self.is_front_image = not self.is_front_image
        self.add_image_section(self.scrollable_frame)  # Reload the image section

    def open_full_art(self):
        try:
            art_window = tk.Toplevel(self.parent)
            art_window.title("Full Art View")

            card_key = self.card.get("card_key", "")
            suffix = "back" if not self.is_front_image else "front"
            image_path = os.path.join(CONFIG["data"]["image_folder"], f"{card_key}_{suffix}.jpg")
            
            try:
                full_img = Image.open(image_path)
                photo = ImageTk.PhotoImage(full_img)
                img_label = tk.Label(art_window, image=photo)
                img_label.image = photo  # Keep reference
                img_label.pack()
            except Exception as e:
                tk.Label(art_window, text=f"Error loading image: {e}").pack()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not open full art view: {e}")

    def add_card_info(self, parent):
        # Card Title
        tk.Label(parent, text=self.card.get("Name", "Unknown Card"),
                font=("Arial", 14, "bold")).pack(pady=2, anchor="center")

        # Subtitle
        tk.Label(parent, text=self.card.get("Subtitle", ""),
                font=("Arial", 12)).pack(pady=5, anchor="center")
        
        owned_qty = tk.IntVar(value=self.card_app.collection.get(self.card["card_key"], 0))

        def update_owned(new_qty):
            owned_qty.set(new_qty)
            self.card_app.collection[self.card["card_key"]] = new_qty
            self.card_app.save_collection()
            self.card_app.ui.load_table()
            self.card_app.ui.load_table(owned_only=True)

        owned_frame = tk.Frame(parent)
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        owned_frame.pack(pady=5, anchor="center")

        tk.Label(owned_frame, text="Owned:").pack(side="left", padx=5)
        tk.Button(owned_frame, text="-", command=lambda: update_owned(max(0, owned_qty.get() - 1))).pack(side="left")
        tk.Label(owned_frame, textvariable=owned_qty).pack(side="left", padx=5)
        tk.Button(owned_frame, text="+", command=lambda: update_owned(owned_qty.get() + 1)).pack(side="left")

        # Card Stats
        stats_text = (
            f"Type: {self.card.get('Type', '')}\n"
            f"Arenas: {self.card.get('Arenas', '')}\n"
            f"Aspect: {self.card.get('Aspects', '')}\n"
            f"Cost: {self.card.get('Cost', '')}   Power: {self.card.get('Power', '')}   Health: {self.card.get('HP', '')}\n"
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

        # Separator line
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)

        # Related cards (collapsible section)
        related_frame = tk.Frame(parent)
        related_frame.pack(fill="x", padx=10, pady=(0, 5))

        is_expanded = tk.BooleanVar(value=False)

        toggle_button = tk.Label(related_frame, text="▶ Related Cards", font=("Arial", 12, "bold"), cursor="hand2")
        toggle_button.pack(anchor="w")

        related_list_frame = tk.Frame(related_frame)
        related_list_frame.pack(fill="x", padx=20, anchor="w")
        related_list_frame.pack_forget()  # Start collapsed

        def toggle_related():
            if is_expanded.get():
                related_list_frame.pack_forget()
                toggle_button.config(text="▶ Related Cards")
                is_expanded.set(False)
            else:
                related_list_frame.pack(fill="x", padx=20, anchor="w")
                toggle_button.config(text="▼ Related Cards")
                is_expanded.set(True)

        toggle_button.bind("<Button-1>", lambda e: toggle_related())

        # Populate related cards
        current_words = set(self.card["Name"].lower().split())
        related_cards = []
        for other_card in self.card_app.cards:
            if other_card["card_key"] == self.card["card_key"]:
                continue
            other_words = set(other_card["Name"].lower().split())
            if current_words & other_words:
                related_cards.append(other_card)

        for related in related_cards:
            subtitle = related.get("Subtitle", "").strip()
            name = related["Name"]
            display = f"{name} - {subtitle}" if subtitle else name
            text = f"{display} - {related['Type']} ({related['card_key']})"
            link = tk.Label(related_list_frame, text=text, fg="blue", cursor="hand2", font=("Arial", 10, "underline"))
            link.pack(anchor="w")
            link.bind("<Button-1>", lambda e, c=related: CardDetailWindow(self.parent, self.card_app, c))

        # Separator before All Data
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)

        # All Data (collapsible)
        all_data_frame = tk.Frame(parent)
        all_data_frame.pack(fill="x", padx=10, pady=(0, 5))

        data_expanded = tk.BooleanVar(value=False)

        data_toggle = tk.Label(all_data_frame, text="▶ All Data", font=("Arial", 12, "bold"), cursor="hand2")
        data_toggle.pack(anchor="w")

        all_data_text_frame = tk.Frame(all_data_frame)
        all_data_text_frame.pack(fill="x", padx=20, anchor="w")
        all_data_text_frame.pack_forget()

        def toggle_all_data():
            if data_expanded.get():
                all_data_text_frame.pack_forget()
                data_toggle.config(text="▶ All Data")
                data_expanded.set(False)
            else:
                all_data_text_frame.pack(fill="x", padx=20, anchor="w")
                data_toggle.config(text="▼ All Data")
                data_expanded.set(True)

        data_toggle.bind("<Button-1>", lambda e: toggle_all_data())

        # Display all raw card data
        raw_text = tk.Text(all_data_text_frame, wrap="word", height=15, font=("Courier", 9))
        raw_text.pack(fill="x", pady=5)
        raw_text.insert("1.0", json.dumps(self.card, indent=2))
        raw_text.config(state="disabled")
