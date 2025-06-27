import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import json
from app.config import CONFIG
from app.image_fetcher import CardImageFetcher
from typing import Dict, Any, Optional, List, Set, Callable

class CardDetailWindow:
    # Font constants
    TITLE_FONT = ("Arial", 14, "bold")
    SUBTITLE_FONT = ("Arial", 12)
    NORMAL_FONT = ("Arial", 10)
    ITALIC_FONT = ("Arial", 10, "italic")
    HEADER_FONT = ("Arial", 12, "bold")
    CODE_FONT = ("Courier", 9)
    
    def __init__(self, parent, card_app, card: Dict[str, Any]):
        self.parent = parent
        self.card = card
        self.card_app = card_app
        self.is_front_image = True
        self.image_path = ""
        self.image_folder = "images"
        
        # Create image directory if it doesn't exist
        Path(self.image_folder).mkdir(exist_ok=True)

        self.detail_window = tk.Toplevel(self.parent)
        self.detail_window.title(f"Card Info - {card.get('Name', '')}")
        self.detail_window.geometry("600x700")

        self.create_ui()

        self.detail_window.bind("<Enter>", self._bind_scroll)
        self.detail_window.bind("<Leave>", self._unbind_scroll)
        self.detail_window.protocol("WM_DELETE_WINDOW", self._on_close)

    def create_ui(self) -> None:
        """Create the scrollable UI for card details."""
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

    def _bind_scroll(self, event=None) -> None:
        """Bind mousewheel events for scrolling."""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)      # Windows/macOS
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)        # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)        # Linux scroll down

    def _unbind_scroll(self, event=None) -> None:
        """Unbind mousewheel events."""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Handle mousewheel scrolling."""
        if hasattr(event, "delta") and event.delta:  # Windows/macOS
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif hasattr(event, "num"):
            if event.num == 4:  # Linux scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux scroll down
                self.canvas.yview_scroll(1, "units")

    def _on_close(self) -> None:
        """Clean up and close the window."""
        self._unbind_scroll()
        self.detail_window.destroy()

    def _load_and_display_image(self) -> None:
        """Helper method to load and display the current card image."""
        try:
            print(f"Loading image for card: {self.card.get('Name')} ({self.card.get('card_key')})")
            print(f"Using front image: {self.is_front_image}")
            
            image_data, image_path = CardImageFetcher.load_card_image(self.card, self.is_front_image)
            self.image_path = image_path
            
            if image_data:
                # Resize the image based on card type
                resized_image = CardImageFetcher.resize_card_image(image_data, self.card, self.is_front_image)
                
                # Convert to Tkinter PhotoImage
                photo = CardImageFetcher.create_tk_photo(resized_image)
                
                if photo:
                    self.image_label.configure(image=photo)
                    self.image_label.image = photo  # type: ignore # Keep reference to prevent garbage collection
                else:
                    self.image_label.configure(text="Error processing image")
            else:
                self.image_label.configure(text=f"Image not found\n{self.card.get('Name')}\n{image_path}")
                print(f"Image not found at {image_path}")
        except FileNotFoundError:
            self.image_label.configure(text=f"Image file not found: {self.image_path}")
            print(f"Image file not found: {self.image_path}")
        except (IOError, OSError) as e:
            self.image_label.configure(text=f"I/O error loading image: {str(e)}")
            print(f"I/O error loading image: {e}")
        except Exception as e:
            self.image_label.configure(text=f"Error loading image: {str(e)}")
            print(f"Unexpected error in image loading: {e}")

    def add_image_section(self, parent) -> None:
        """Add the card image section to the UI."""
        image_frame = tk.Frame(parent)
        image_frame.pack(pady=10, fill="x")

        self.image_label = tk.Label(image_frame)
        self.image_label.pack(anchor="center")

        # Load and display the card image
        self._load_and_display_image()

        button_frame = tk.Frame(parent)
        button_frame.pack(pady=2)

        if self.card.get("BackArt"):  
            flip_button = tk.Button(button_frame, text="Flip Card", command=self.flip_image)
            flip_button.pack(side="left", padx=5)

        view_full_button = tk.Button(button_frame, text="View Full Art", command=self.open_full_art)
        view_full_button.pack(side="left", padx=5)

        button_frame.pack(anchor="center")

    def flip_image(self) -> None:
        """Toggle between front and back card images."""
        self.is_front_image = not self.is_front_image
        print(f"Flipping card to {'front' if self.is_front_image else 'back'} side")
        self._load_and_display_image()

    def open_full_art(self) -> None:
        """Open a new window showing the full card art."""
        try:
            art_window = tk.Toplevel(self.parent)
            art_window.title("Full Art View")

            # Use image fetcher to get the path
            image_path = CardImageFetcher.get_card_image_path(self.card, self.is_front_image)
            
            try:
                full_img = Image.open(image_path)
                photo = ImageTk.PhotoImage(full_img)
                img_label = tk.Label(art_window, image=photo)
                img_label.image = photo  # type: ignore # Keep reference to prevent garbage collection
                img_label.pack()
            except Exception as e:
                tk.Label(art_window, text=f"Error loading image: {e}").pack()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not open full art view: {e}")

    def _create_collapsible_section(self, parent, title: str, content_creator: Callable[[tk.Frame], None]) -> tk.Frame:
        """Create a collapsible section with the given title and content creator function."""
        frame = tk.Frame(parent)
        frame.pack(fill="x", padx=10, pady=(0, 5))

        is_expanded = tk.BooleanVar(value=False)
        
        toggle_button = tk.Label(frame, text=f"▶ {title}", font=self.HEADER_FONT, cursor="hand2")
        toggle_button.pack(anchor="w")

        content_frame = tk.Frame(frame)
        content_frame.pack(fill="x", padx=20, anchor="w")
        content_frame.pack_forget()  # Start collapsed

        # Call the function that creates the content in the frame
        content_creator(content_frame)

        def toggle() -> None:
            if is_expanded.get():
                content_frame.pack_forget()
                toggle_button.config(text=f"▶ {title}")
                is_expanded.set(False)
            else:
                content_frame.pack(fill="x", padx=20, anchor="w")
                toggle_button.config(text=f"▼ {title}")
                is_expanded.set(True)

        def on_toggle_click(event: tk.Event) -> None:
            toggle()

        toggle_button.bind("<Button-1>", on_toggle_click)
        
        return frame

    def _find_related_cards(self) -> List[Dict[str, Any]]:
        """Find cards that share words in their names with the current card."""
        current_words = set(self.card["Name"].lower().split())
        related_cards = []
        
        for other_card in self.card_app.cards:
            if other_card["card_key"] == self.card["card_key"]:
                continue
            other_words = set(other_card["Name"].lower().split())
            if current_words & other_words:
                related_cards.append(other_card)
                
        return related_cards

    def add_card_info(self, parent) -> None:
        """Add the card information section to the UI."""
        # Card Title
        tk.Label(parent, text=self.card.get("Name", "Unknown Card"),
                font=self.TITLE_FONT).pack(pady=2, anchor="center")

        # Subtitle
        tk.Label(parent, text=self.card.get("Subtitle", ""),
                font=self.SUBTITLE_FONT).pack(pady=5, anchor="center")
        
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

        tk.Label(parent, text=stats_text, font=self.NORMAL_FONT, justify="left").pack(pady=5, padx=10, anchor="w")

        # Card Text
        front_text = self.card.get("FrontText", "")
        if front_text:
            tk.Label(parent, text="Front Text:", font=self.HEADER_FONT).pack(pady=(5, 2), padx=10, anchor="w")
            tk.Label(parent, text=front_text, wraplength=550, justify="left", font=self.ITALIC_FONT).pack(pady=(0, 10), padx=10, anchor="w")

        back_text = self.card.get("BackText", "")
        if back_text:
            tk.Label(parent, text="Back Text:", font=self.HEADER_FONT).pack(pady=(5, 2), padx=10, anchor="w")
            tk.Label(parent, text=back_text, wraplength=550, justify="left", font=self.ITALIC_FONT).pack(pady=(0, 10), padx=10, anchor="w")

        # Separator line
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)

        # Related cards (collapsible section)
        def create_related_content(frame):
            related_cards = self._find_related_cards()
            for related in related_cards:
                subtitle = related.get("Subtitle", "").strip()
                name = related["Name"]
                display = f"{name} - {subtitle}" if subtitle else name
                text = f"{display} - {related['Type']} ({related['card_key']})"
                link = tk.Label(frame, text=text, fg="blue", cursor="hand2", font=self.NORMAL_FONT, underline=1)
                link.pack(anchor="w")
                link.bind("<Button-1>", lambda e, c=related: CardDetailWindow(self.parent, self.card_app, c))
                
        self._create_collapsible_section(parent, "Related Cards", create_related_content)

        # Separator before All Data
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)

        # All Data (collapsible)
        def create_raw_data_content(frame):
            raw_text = tk.Text(frame, wrap="word", height=15, font=self.CODE_FONT)
            raw_text.pack(fill="x", pady=5)
            raw_text.insert("1.0", json.dumps(self.card, indent=2))
            raw_text.config(state="disabled")
            
        self._create_collapsible_section(parent, "All Data", create_raw_data_content)
