import os
import json
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

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

        self.setup_layout()
        self.load_deck_tree()

    def get_frame(self):
        return self.frame

    def setup_layout(self):
        self.left_frame = tk.Frame(self.frame)
        self.left_frame.pack(side="left", fill="y", padx=5, pady=5)

        self.right_frame = tk.Frame(self.frame)
        self.right_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Deck Treeview
        self.deck_tree = ttk.Treeview(self.left_frame)
        self.deck_tree.pack(fill="y", expand=True)
        self.deck_tree.bind("<Double-1>", self.on_deck_select)

        button_frame = tk.Frame(self.left_frame)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Add Folder", command=self.add_folder).pack(side="left", padx=2)
        tk.Button(button_frame, text="Add Deck", command=self.add_deck).pack(side="left", padx=2)

        # Right Panel Layout
        self.info_frame = tk.Frame(self.right_frame)
        self.info_frame.pack(fill="x", pady=5)

        # Deck Name
        self.deck_name_var = tk.StringVar()
        tk.Label(self.info_frame, textvariable=self.deck_name_var, font=("Arial", 14, "bold")).pack()

        # Deck Status
        status_frame = tk.Frame(self.info_frame)
        status_frame.pack()
        tk.Label(status_frame, text="Status:").pack(side="left")
        self.status_var = tk.StringVar()
        status_options = ["Built", "Testing", "Idea"]
        status_combo = ttk.Combobox(status_frame, textvariable=self.status_var, values=status_options, state="readonly", width=10)
        status_combo.pack(side="left")
        status_combo.bind("<<ComboboxSelected>>", self.save_deck_status)

        # Estimated Value
        self.value_var = tk.StringVar(value="Estimated Value: $0")
        tk.Label(self.info_frame, textvariable=self.value_var).pack()

        # Leader & Base Info
        self.leader_var = tk.StringVar(value="Leader: None")
        self.base_var = tk.StringVar(value="Base: None")
        tk.Label(self.info_frame, textvariable=self.leader_var).pack()
        tk.Label(self.info_frame, textvariable=self.base_var).pack()

        # Placeholder for deck breakdowns
        self.breakdown_frame = tk.Frame(self.right_frame)
        self.breakdown_frame.pack(fill="x", pady=5)

        # Card Table
        self.table_frame = tk.Frame(self.right_frame)
        self.table_frame.pack(fill="both", expand=True)

        self.card_tree = ttk.Treeview(self.table_frame, columns=("Owned", "In Deck", "Name", "Set", "Type", "Arenas", "Aspect"), show="headings")
        for col in self.card_tree["columns"]:
            self.card_tree.heading(col, text=col)
            self.card_tree.column(col, width=100, stretch=True)
        self.card_tree.pack(fill="both", expand=True)

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

        leader_key = self.deck_data.get("leader")
        base_key = self.deck_data.get("base")

        leader_name = next((c["name"] for c in self.app.cards if c["card_key"] == leader_key), "None")
        base_name = next((c["name"] for c in self.app.cards if c["card_key"] == base_key), "None")

        self.leader_var.set(f"Leader: {leader_name}")
        self.base_var.set(f"Base: {base_name}")

        self.update_breakdown_charts()
        self.load_deck_table()

    def load_deck_table(self):
        self.card_tree.delete(*self.card_tree.get_children())

        for card_key, count in self.deck_data.get("cards", {}).items():
            card = next((c for c in self.app.cards if c["card_key"] == card_key), None)
            if not card:
                continue

            self.card_tree.insert("", "end", values=(
                self.app.collection.get(card_key, 0),
                count,
                card.get("name", "Unknown"),
                card.get("set_code", ""),
                card.get("type", ""),
                card.get("arenas", ""),
                card.get("aspect", "")
            ))

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

    def update_breakdown_charts(self):
        # Clear previous content
        for widget in self.breakdown_frame.winfo_children():
            widget.destroy()

        # Placeholder Labels
        tk.Label(self.breakdown_frame, text="Cost Breakdown: TODO").pack()
        tk.Label(self.breakdown_frame, text="Type Breakdown: TODO").pack()
