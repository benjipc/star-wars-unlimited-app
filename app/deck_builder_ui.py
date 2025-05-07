import os
import json
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from rapidfuzz import fuzz

from app.config import CONFIG


class DeckBuilderTab:
    def __init__(self, parent, app):
        self.app = app
        self.root = app.root
        self.frame = tk.Frame(parent)

        self.deck_folder = CONFIG["data"]["deck_folder"]
        os.makedirs(self.deck_folder, exist_ok=True)

        self.decks = {}  # {folder: [deck names]}
        self.current_deck = None
        self.deck_data = {}  # Loaded deck data

        self.search_var = tk.StringVar()
        self.from_inventory_var = tk.BooleanVar(value=True)
        self.search_menu = tk.Menu(self.root, tearoff=0)
        self.search_popup = None
        self.dropdown_active_index = 0  # Track the active index for hover preview

        self.setup_layout()
        self.load_deck_tree()


    def get_frame(self):
        return self.frame

    def setup_layout(self):
        self.left_frame = tk.Frame(self.frame)
        self.left_frame.pack(side="left", fill="y", padx=5, pady=5)

        self.right_frame = tk.Frame(self.frame)
        self.right_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.deck_name_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.value_var = tk.StringVar(value="Estimated Value: $0")
        self.leader_var = tk.StringVar(value="Leader: None")
        self.base_var = tk.StringVar(value="Base: None")

        self.breakdown_frame = tk.Frame(self.right_frame)
        self.breakdown_frame.pack(fill="x", pady=5)

        # Deck Treeview
        self.deck_tree = ttk.Treeview(self.left_frame)
        self.deck_tree.pack(fill="y", expand=True)
        self.deck_tree.bind("<Double-1>", self.on_deck_select)
        self.deck_tree.bind("<Return>", self.on_deck_select)
        self.deck_tree.bind("<Delete>", self.delete_deck)

        # Right-click Menus
        self.deck_menu = tk.Menu(self.root, tearoff=0)
        self.deck_menu.add_command(label="Rename Deck", command=self.rename_deck)
        self.deck_menu.add_command(label="Delete Deck", command=self.delete_deck)
        self.deck_menu.add_command(label="Move to Folder...", command=self.move_deck_to_folder)

        self.folder_menu = tk.Menu(self.root, tearoff=0)
        self.folder_menu.add_command(label="Rename Folder", command=self.rename_folder)
        self.deck_tree.bind("<Button-3>", self.show_context_menu)

        button_frame = tk.Frame(self.left_frame)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Add Folder", command=self.add_folder).pack(side="left", padx=2)
        tk.Button(button_frame, text="Add Deck", command=self.add_deck).pack(side="left", padx=2)

        # Right Panel Layout
        self.info_frame = tk.Frame(self.right_frame)
        self.info_frame.pack(fill="x", pady=5)

        # Header Frame
        header_frame = tk.Frame(self.info_frame)
        header_frame.pack(fill="x", pady=5)

        # Deck Name + Rename
        name_frame = tk.Frame(header_frame)
        name_frame.grid(row=0, column=0, sticky="w", padx=5)

        tk.Label(name_frame, text="Deck Name:").pack(side="left")
        tk.Label(name_frame, textvariable=self.deck_name_var, font=("Arial", 14, "bold")).pack(side="left", padx=2)
        tk.Button(name_frame, text="Rename", command=self.rename_deck).pack(side="left", padx=5)

        # Status + Value
        status_frame = tk.Frame(header_frame)
        status_frame.grid(row=0, column=2, sticky="e", padx=5)

        tk.Label(status_frame, text="Status:").pack(side="left")
        status_options = ["Idea", "Testing", "Built"]
        status_combo = ttk.Combobox(status_frame, textvariable=self.status_var, values=status_options, state="readonly", width=10)
        status_combo.pack(side="left", padx=5)

        tk.Label(status_frame, textvariable=self.value_var).pack(side="left", padx=10)

        # Middle Row
        middle_frame = tk.Frame(self.info_frame)
        middle_frame.pack(fill="x", pady=5)

        # Type Breakdown on left
        self.type_breakdown_label = tk.Label(middle_frame, text="Type Breakdown: Units: 0, Events: 0, Upgrades: 0")
        self.type_breakdown_label.grid(row=0, column=0, sticky="w", padx=5)

        # Cost Curve on right
        self.cost_curve_label = tk.Label(middle_frame, text="Cost Curve: 0:0 | 1:0 | 2:0 | 3:0 | 4:0 | 5+:0")
        self.cost_curve_label.grid(row=0, column=1, sticky="e", padx=5)

        # Leader + Base
        bottom_frame = tk.Frame(self.info_frame)
        bottom_frame.pack(fill="x", pady=5)

        tk.Label(bottom_frame, textvariable=self.leader_var).grid(row=0, column=0, sticky="w", padx=5)
        tk.Label(bottom_frame, textvariable=self.base_var).grid(row=0, column=1, sticky="e", padx=5)

        # Search + Add Card Controls
        search_frame = tk.Frame(self.right_frame)
        search_frame.pack(fill="x", pady=5)

        tk.Label(search_frame, text="Add Card:").pack(side="left", padx=2)
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40, state="disabled")
        self.search_entry.pack(side="left", padx=2)
        self.search_entry.bind("<KeyRelease>", self.update_search_dropdown)

        tk.Checkbutton(search_frame, text="From Inventory Only", variable=self.from_inventory_var, command=self.update_search_dropdown).pack(side="left", padx=10)

        # Card Table
        self.table_frame = tk.Frame(self.right_frame)
        self.table_frame.pack(fill="both", expand=True)

        self.visible_columns = ["CardKey", "Owned", "In Deck", "Name", "Set", "Type", "Arenas", "Aspect"]
        self.card_tree = ttk.Treeview(self.table_frame, columns=self.visible_columns, show="headings")
        for col in self.card_tree["columns"]:
            self.card_tree.heading(col, text=col)
            self.card_tree.column(col, width=100, stretch=True)
        self.card_tree.pack(fill="both", expand=True)
        self.card_tree.column("CardKey", width=0, stretch=False)

        self.card_tree.bind("<Double-1>", self.on_card_table_double_click)

        # Right-click header menu
        self.card_tree.bind("<Button-3>", self._on_column_right_click)
        self.header_menu = tk.Menu(self.root, tearoff=0)
        self.header_menu.add_command(label="Configure Columns...", command=self._open_column_config)

    def _on_column_right_click(self, event):
        region = self.card_tree.identify_region(event.x, event.y)
        if region == "heading":
            self.header_menu.tk_popup(event.x_root, event.y_root)

    def _open_column_config(self):
        default_order = ["CardKey", "Owned", "In Deck", "Name", "Set", "Type", "Arenas", "Aspect"]

        # Get all possible keys from cards
        all_keys = set()
        for card in self.app.cards:
            all_keys.update(card.keys())
        all_keys.update(default_order)

        # Preserve default order and append any extras
        extra_keys = [k for k in sorted(all_keys) if k not in default_order]
        all_columns = default_order + extra_keys

        config_win = tk.Toplevel(self.root)
        config_win.title("Configure Visible Columns")
        config_win.geometry("500x600")

        tk.Label(config_win, text="Toggle columns to display:", font=("Arial", 12)).pack(pady=(10, 0))

        container = tk.Frame(config_win)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create checkboxes in two columns
        check_vars = {}
        for i, col in enumerate(all_columns):
            var = tk.BooleanVar(value=col in self.visible_columns)
            check_vars[col] = var
            cb = tk.Checkbutton(scrollable_frame, text=col, variable=var)
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=2)

        # Buttons underneath
        button_frame = tk.Frame(config_win)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="OK", width=10,
                command=lambda: self._apply_column_config(check_vars, config_win)).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancel", width=10, command=config_win.destroy).pack(side="right", padx=10)


    def _apply_column_config(self, check_vars, config_win):
        self.visible_columns = [col for col, var in check_vars.items() if var.get()]
        self.card_tree["columns"] = self.visible_columns
        self.card_tree["displaycolumns"] = self.visible_columns
        for col in self.visible_columns:
            self.card_tree.heading(col, text=col)
            self.card_tree.column(col, width=100, stretch=True)
        self.load_deck_table()
        config_win.destroy()

    def load_deck_tree(self):
        self.deck_tree.delete(*self.deck_tree.get_children())

        for folder_name in os.listdir(self.deck_folder):
            folder_path = os.path.join(self.deck_folder, folder_name)
            if os.path.isdir(folder_path):
                folder_id = self.deck_tree.insert("", "end", text=folder_name, open=True)
                for filename in os.listdir(folder_path):
                    if filename.endswith(".json"):
                        deck_name = filename[:-5]
                        self.deck_tree.insert(folder_id, "end", text=deck_name)

    def show_context_menu(self, event):
        selected = self.deck_tree.identify_row(event.y)
        if selected:
            self.deck_tree.selection_set(selected)
            parent = self.deck_tree.parent(selected)
            if parent:  # Only allow right-click menu on decks (not folders)
                self.deck_menu.tk_popup(event.x_root, event.y_root)

    def add_folder(self):
            name = simpledialog.askstring("New Folder", "Folder Name:")
            if not name:
                return
            os.makedirs(os.path.join(self.deck_folder, name), exist_ok=True)
            self.load_deck_tree()

    def add_deck(self):
            selected = self.deck_tree.focus()
            if not selected:
                messagebox.showerror("Error", "Select a folder to add a deck to.")
                return

            folder = self.deck_tree.item(selected, "text")
            folder_path = os.path.join(self.deck_folder, folder)
            if not os.path.isdir(folder_path):
                messagebox.showerror("Error", "Select a folder, not a deck.")
                return

            name = simpledialog.askstring("New Deck", "Deck Name:")
            if not name:
                return

            deck_path = os.path.join(folder_path, f"{name}.json")
            if os.path.exists(deck_path):
                messagebox.showerror("Error", "Deck already exists.")
                return

            deck_data = {"name": name, "status": "Idea", "cards": {}, "leader": None, "base": None}
            with open(deck_path, "w") as f:
                json.dump(deck_data, f, indent=2)

            self.load_deck_tree()

    def move_deck_to_folder(self):
        selected = self.deck_tree.focus()
        if not selected:
            return

        current_parent = self.deck_tree.parent(selected)
        deck_name = self.deck_tree.item(selected, "text")

        if not current_parent:
            return

        current_folder = self.deck_tree.item(current_parent, "text")
        current_path = os.path.join(self.deck_folder, current_folder, f"{deck_name}.json")

        # Prompt for destination folder
        folders = [f for f in os.listdir(self.deck_folder) if os.path.isdir(os.path.join(self.deck_folder, f)) and f != current_folder]
        if not folders:
            messagebox.showinfo("No Folders", "No other folders available.")
            return

        dest = simpledialog.askstring("Move Deck", f"Move to which folder?\nAvailable: {', '.join(folders)}")
        if dest not in folders:
            return

        new_path = os.path.join(self.deck_folder, dest, f"{deck_name}.json")
        if os.path.exists(new_path):
            messagebox.showerror("Error", "A deck with this name already exists in the target folder.")
            return

        os.rename(current_path, new_path)
        self.load_deck_tree()

    def rename_deck(self):
        # Get selected item and validate
        selected = self.deck_tree.selection()
        if not selected:
            messagebox.showerror("Error", "No deck selected.")
            return
        
        selected = selected[0]  # Get the first selected item
        parent = self.deck_tree.parent(selected)
        if not parent:
            messagebox.showerror("Error", "Please select a deck, not a folder.")
            return

        # Get current deck info
        deck_name = self.deck_tree.item(selected)["text"]
        folder = self.deck_tree.item(parent)["text"]

        # Get new name
        new_name = simpledialog.askstring("Rename Deck", "Enter new deck name:", initialvalue=deck_name)
        if not new_name or new_name == deck_name:
            return

        # Validate new name
        invalid_chars = '<>:"/\\|?*'
        if any(char in new_name for char in invalid_chars):
            messagebox.showerror("Error", f"Deck name contains invalid characters: {invalid_chars}")
            return

        # Setup paths
        old_path = os.path.join(self.deck_folder, folder, f"{deck_name}.json")
        new_path = os.path.join(self.deck_folder, folder, f"{new_name}.json")

        if os.path.exists(new_path):
            messagebox.showerror("Error", "A deck with this name already exists.")
            return

        # Load and update the deck data
        try:
            with open(old_path, 'r') as f:
                deck_data = json.load(f)
                deck_data['name'] = new_name
            
            # Write updated data to new file
            with open(new_path, 'w') as f:
                json.dump(deck_data, f, indent=2)
            
            # Remove old file
            os.remove(old_path)
            
        except FileNotFoundError:
            messagebox.showerror("Error", f"Deck file not found:\n{old_path}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename deck:\n{e}")
            return

    # Update loaded deck name if it's currently loaded
        if self.deck_data.get("name") == deck_name:
            # Reload the deck data from the new file
            with open(new_path, 'r') as f:
                self.deck_data = json.load(f)
            self.deck_name_var.set(new_name)
            self.current_deck = new_name  # Update current_deck reference

        # Refresh tree and reselect
        self.load_deck_tree()
        
        # Re-select the renamed deck
        for folder_id in self.deck_tree.get_children():
            if self.deck_tree.item(folder_id)["text"] == folder:
                for deck_id in self.deck_tree.get_children(folder_id):
                    if self.deck_tree.item(deck_id)["text"] == new_name:
                        self.deck_tree.selection_set(deck_id)
                        self.deck_tree.focus(deck_id)
                        self.on_deck_select(None)  # Trigger deck reload
                        break

    def delete_deck(self):
        selected = self.deck_tree.focus()
        parent = self.deck_tree.parent(selected)
        if not parent:
            messagebox.showerror("Error", "Select a deck to delete.")
            return  # It's a folder, not a deck.

        folder = self.deck_tree.item(parent, "text")
        deck_name = self.deck_tree.item(selected, "text")
        deck_path = os.path.join(self.deck_folder, folder, f"{deck_name}.json")

        if not os.path.exists(deck_path):
            messagebox.showerror("Error", "Deck file not found.")
            return

        confirm = messagebox.askyesno("Delete Deck", f"Are you sure you want to delete '{deck_name}'?")
        if not confirm:
            return

        try:
            os.remove(deck_path)
            self.load_deck_tree()
            self.deck_data = {}
            self.deck_name_var.set("")
            self.status_var.set("")
            self.value_var.set("")
            self.leader_var.set("Leader: None")
            self.base_var.set("Base: None")
            self.card_tree.delete(*self.card_tree.get_children())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete deck: {e}")


    def on_deck_select(self, event):
        selected = self.deck_tree.focus()
        parent = self.deck_tree.parent(selected)
        if not parent:
            return  # Folder

        folder = self.deck_tree.item(parent, "text")
        deck_name = self.deck_tree.item(selected, "text")

        deck_path = os.path.join(self.deck_folder, folder, f"{deck_name}.json")
        if not os.path.exists(deck_path):
            messagebox.showerror("Error", "Deck file not found.")
            return

        with open(deck_path) as f:
            self.deck_data = json.load(f)

        self.deck_name_var.set(self.deck_data["name"])
        self.status_var.set(self.deck_data.get("status", "Idea"))
        self.value_var.set("Estimated Value: $TODO")

        # Find all leaders and bases in the deck
        leaders = [k for k in self.deck_data.get("cards", {}) if next((c for c in self.app.cards if c["card_key"] == k and c["Type"] == "Leader"), None)]
        bases = [k for k in self.deck_data.get("cards", {}) if next((c for c in self.app.cards if c["card_key"] == k and c["Type"] == "Base"), None)]

        # Build Leader display
        if not leaders:
            leader_display = "Leader: None"
        elif len(leaders) == 1:
            leader_name = next(c["Name"] for c in self.app.cards if c["card_key"] == leaders[0])
            leader_display = f"Leader: {leader_name}"
        else:
            names = [next(c["Name"] for c in self.app.cards if c["card_key"] == k) for k in leaders]
            leader_display = f"Leader: {', '.join(names)} [ERROR: Too many Leaders]"

        # Same for Base
        if not bases:
            base_display = "Base: None"
        elif len(bases) == 1:
            base_name = next(c["Name"] for c in self.app.cards if c["card_key"] == bases[0])
            base_display = f"Base: {base_name}"
        else:
            names = [next(c["Name"] for c in self.app.cards if c["card_key"] == k) for k in bases]
            base_display = f"Base: {', '.join(names)} [ERROR: Too many Bases]"

        self.leader_var.set(leader_display)
        self.base_var.set(base_display)


        self.update_breakdown_charts()
        self.load_deck_table()
        self.search_entry.config(state="normal")
        self.search_var.set("")


    def load_deck_table(self):
        self.card_tree.delete(*self.card_tree.get_children())
        self.card_tree["displaycolumns"] = self.visible_columns

        for card_key, count in self.deck_data.get("cards", {}).items():
            card = next((c for c in self.app.cards if c["card_key"] == card_key), {})
            row_data = dict(card)
            row_data["CardKey"] = card_key
            row_data["Owned"] = self.app.collection.get(card_key, 0)
            row_data["In Deck"] = count

            # Make sure everything is converted to string for display
            values = [json.dumps(row_data.get(col, "")) if isinstance(row_data.get(col), (list, dict)) else str(row_data.get(col, "")) for col in self.card_tree["columns"]]
            self.card_tree.insert("", "end", values=values)

    def save_deck_status(self, event=None):
        if not self.deck_data:
            return
        self.deck_data["status"] = self.status_var.get()
        self.save_current_deck()

    def save_current_deck(self):
        folder = self.deck_tree.item(self.deck_tree.parent(self.deck_tree.focus()), "text")
        deck_name = self.deck_data["name"]
        deck_path = os.path.join(self.deck_folder, folder, f"{deck_name}.json")
        with open(deck_path, "w") as f:
            json.dump(self.deck_data, f, indent=2)

    def rename_folder(self):
        selected = self.deck_tree.focus()
        if not selected:
            return

        old_name = self.deck_tree.item(selected, "text")
        new_name = simpledialog.askstring("Rename Folder", "Enter new folder name:", initialvalue=old_name)
        if not new_name or new_name == old_name:
            return

        old_path = os.path.join(self.deck_folder, old_name)
        new_path = os.path.join(self.deck_folder, new_name)

        if os.path.exists(new_path):
            messagebox.showerror("Error", "Folder with this name already exists.")
            return

        os.rename(old_path, new_path)
        self.load_deck_tree()

    def update_breakdown_charts(self):
        # Clear previous content
        for widget in self.breakdown_frame.winfo_children():
            widget.destroy()


    def update_search_dropdown(self, event=None):
        if not self.deck_data:
            return

        query = self.search_var.get().lower()
        if getattr(self, "last_query", None) == query:
            return  # Prevent rebuild if query hasn't changed
        self.last_query = query

        cards = self.app.cards
        if self.from_inventory_var.get():
            cards = [c for c in cards if self.app.collection.get(c["card_key"], 0) > 0]

        matches = sorted(
            [(fuzz.partial_ratio(query, c.get("Name", "").lower()), c) for c in cards],
            key=lambda x: x[0],
            reverse=True
        )
        self.matching_cards = [c for score, c in matches if score > CONFIG["search"]["fuzzy_threshold"]]

        if not self.matching_cards:
            if hasattr(self, "search_popup") and self.search_popup:
                self.search_popup.destroy()
                self.search_popup = None
            return

        if not hasattr(self, "search_popup") or not self.search_popup:
            self.search_popup = tk.Toplevel(self.root)
            self.search_popup.wm_overrideredirect(True)
            x = self.search_entry.winfo_rootx()
            y = self.search_entry.winfo_rooty() + self.search_entry.winfo_height()
            self.search_popup.geometry(f"+{x}+{y}")

            self.search_listbox = tk.Listbox(self.search_popup, width=50)
            self.search_listbox.pack()

            self.search_listbox.bind("<Double-1>", self._on_listbox_select)
            self.search_listbox.bind("<Return>", self._on_listbox_select)
            self.search_listbox.bind("<Motion>", self._show_preview)
            self.search_listbox.bind("<Leave>", self._hide_preview)
        else:
            self.search_listbox.delete(0, tk.END)

        for idx, card in enumerate(self.matching_cards[:20]):
            subtitle = card.get("Subtitle", "").strip()
            if subtitle:
                display = f'{card["Name"]} — {subtitle} ({card["Set"]} #{card["Number"]})'
            else:
                display = f'{card["Name"]} ({card["Set"]} #{card["Number"]})'
            self.search_listbox.insert(tk.END, display)

        if not hasattr(self, "dropdown_active_index") or self.dropdown_active_index >= self.search_listbox.size():
            self.dropdown_active_index = 0

        self.search_listbox.select_clear(0, tk.END)
        self.search_listbox.select_set(self.dropdown_active_index)
        self.search_listbox.activate(self.dropdown_active_index)
        self.search_listbox.see(self.dropdown_active_index)
        self.search_entry.focus_set()

        def close_all():
            if self.search_popup:
                self.search_popup.destroy()
                self.search_popup = None
            if hasattr(self, "hover_preview") and self.hover_preview:
                self.hover_preview.destroy()
                self.hover_preview = None
            self.last_query = ""
            self.dropdown_active_index = 0
            self.search_entry.focus_set()

        def on_click_outside(event):
            widget = event.widget
            if widget not in (self.search_popup, self.search_entry, self.search_listbox) and not str(widget).startswith(str(self.search_popup)):
                close_all()

        self.root.after(100, lambda: setattr(self, "outside_click_id", self.root.bind("<Button-1>", on_click_outside)))

        def navigate_dropdown(event):
            if not self.search_popup or not hasattr(self, "matching_cards"):
                return "break"

            listbox_size = self.search_listbox.size()

            if event.keysym == "Up":
                self.dropdown_active_index = max(0, self.dropdown_active_index - 1)
            elif event.keysym == "Down":
                self.dropdown_active_index = min(listbox_size - 1, self.dropdown_active_index + 1)
            elif event.keysym == "Return":
                self.add_card_from_dropdown(self.dropdown_active_index)
                close_all()
                return "break"
            elif event.keysym == "Escape":
                close_all()
                return "break"

            self.search_listbox.select_clear(0, tk.END)
            self.search_listbox.select_set(self.dropdown_active_index)
            self.search_listbox.activate(self.dropdown_active_index)
            self.search_listbox.see(self.dropdown_active_index)
            return "break"

        self.search_entry.bind("<Up>", navigate_dropdown)
        self.search_entry.bind("<Down>", navigate_dropdown)
        self.search_entry.bind("<Return>", navigate_dropdown)
        self.search_entry.bind("<Escape>", navigate_dropdown)

    def _on_listbox_select(self, event):
        if not hasattr(self, "search_listbox"):
            return
        selection = self.search_listbox.curselection()
        if selection:
            self.root.unbind("<Button-1>", self.outside_click_id)
            self.add_card_from_dropdown(selection[0])

    def _show_preview(self, event):
        if not hasattr(self, "search_listbox"):
            return
        index = self.search_listbox.nearest(event.y)
        if index < 0 or index >= len(self.matching_cards):
            return

        card = self.matching_cards[index]
        art_url = card.get("FrontArt", "")
        if not art_url:
            return

        from PIL import Image, ImageTk
        import requests

        card_key = card["card_key"]
        cache_path = os.path.join(CONFIG["data"]["image_folder"], f"{card_key}_front.jpg")
        os.makedirs(CONFIG["data"]["image_folder"], exist_ok=True)

        try:
            if not os.path.exists(cache_path):
                img_data = requests.get(art_url).content
                with open(cache_path, "wb") as f:
                    f.write(img_data)

            img = Image.open(cache_path)
            card_type = card.get("Type", "").lower()
            if card_type in ["leader", "base"]:
                img = img.resize((420, 300), Image.Resampling.LANCZOS)
            else:
                img = img.resize((300, 420), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)

            # Destroy previous preview if it exists
            if hasattr(self, "hover_preview") and self.hover_preview:
                for widget in self.hover_preview.winfo_children():
                    widget.destroy()
                self.hover_preview.destroy()
                self.hover_preview = None

            self.hover_preview = tk.Toplevel(self.root)
            self.hover_preview.wm_overrideredirect(True)
            self.hover_preview.geometry(f"+{event.x_root+20}+{event.y_root+10}")

            img_label = tk.Label(self.hover_preview, image=photo)
            img_label.image = photo  # Keep reference
            img_label.pack()

        except Exception as e:
            print("Image preview error:", e)

    def _hide_preview(self, event):
        if hasattr(self, "hover_preview") and self.hover_preview:
            for widget in self.hover_preview.winfo_children():
                widget.destroy()
            self.hover_preview.destroy()
            self.hover_preview = None

    def add_card_from_dropdown(self, index):
        card = self.matching_cards[index]

        if not self.deck_data or "name" not in self.deck_data:
            messagebox.showerror("Error", "Please select a deck before adding cards.")
            return

        card_key = card["card_key"]
        self.deck_data.setdefault("cards", {})
        self.deck_data["cards"][card_key] = self.deck_data["cards"].get(card_key, 0) + 1

        self.save_current_deck()
        self.load_deck_table()
        self.update_breakdown_charts()

        self.search_var.set("")

        if self.search_popup:
            self.search_popup.destroy()
            self.search_popup = None

    def on_card_table_double_click(self, event):
        region = self.card_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.card_tree.identify_column(event.x)
        row = self.card_tree.identify_row(event.y)

        if not row or column != "#3":  # "#3" is the "In Deck" column (since #1 is CardKey, #2 is Owned)
            return

        item = self.card_tree.item(row)
        old_value = item["values"][2]  # In Deck count
        bbox = self.card_tree.bbox(row, column)

        entry = tk.Entry(self.card_tree)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.insert(0, old_value)
        entry.focus()

        def save_edit(event=None):
            try:
                new_value = int(entry.get())
                if new_value < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Please enter a non-negative integer.")
                entry.destroy()
                return

            card_key = item["values"][0]  # CardKey is in the first column

            if new_value == 0:
                self.deck_data["cards"].pop(card_key, None)
            else:
                self.deck_data["cards"][card_key] = new_value

            self.save_current_deck()
            self.load_deck_table()
            self.update_breakdown_charts()

            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)

    def debounce_search(self, event=None):
        if hasattr(self, "search_after_id"):
            self.root.after_cancel(self.search_after_id)
        self.search_after_id = self.root.after(150, self.update_search_dropdown)

