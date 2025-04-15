import tkinter as tk
from tkinter import ttk

class DeckBuilderTab:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.frame = tk.Frame(parent)

        self.setup_layout()

    def setup_layout(self):
        # Split the layout into left (deck list) and right (deck details)
        self.left_frame = tk.Frame(self.frame, width=250, bd=1, relief="sunken")
        self.right_frame = tk.Frame(self.frame, bd=1, relief="sunken")

        self.left_frame.pack(side="left", fill="y")
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.setup_deck_list()
        self.setup_deck_details()

    def setup_deck_list(self):
        label = tk.Label(self.left_frame, text="Decks", font=("Arial", 12, "bold"))
        label.pack(pady=5)

        self.deck_tree = ttk.Treeview(self.left_frame)
        self.deck_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # TODO: Add folder and deck organization logic

        btn_frame = tk.Frame(self.left_frame)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="New Deck").pack(fill="x", pady=2)
        tk.Button(btn_frame, text="New Folder").pack(fill="x", pady=2)
        tk.Button(btn_frame, text="Delete").pack(fill="x", pady=2)

    def setup_deck_details(self):
        header = tk.Label(self.right_frame, text="Deck Details", font=("Arial", 14, "bold"))
        header.pack(pady=10)

        # Placeholder frames for header info and deck table
        self.header_info = tk.Frame(self.right_frame)
        self.header_info.pack(fill="x", padx=10, pady=5)

        self.deck_table_frame = tk.Frame(self.right_frame)
        self.deck_table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # TODO: Implement header info section (deck status, value, breakdowns, leader/base info)
        # TODO: Implement deck table (with live search input and editable cells)

    def get_frame(self):
        return self.frame
