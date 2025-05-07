import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from rapidfuzz import fuzz
from app.config import CONFIG
from app.validators import CardValidator
from app.data_manager import save_collection
from app.card_detail_window import CardDetailWindow
from app.deck_builder_ui import DeckBuilderTab
from app.app_interfaces import ICardApp

class UIComponents:
    def __init__(self, app: ICardApp):
        self.app = app
        self.root = app.root
        self.cards = app.cards
        self.collection = app.collection

        self.setup_menu()
        self.setup_tabs()

    def setup_menu(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        data_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Check for Card Data Update", command=self.app.update_card_data)

    def setup_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # All Cards Tab
        self.all_frame = tk.Frame(self.notebook)
        self.notebook.add(self.all_frame, text="All Cards")
        self.setup_search_frame(self.all_frame)
        self.setup_table(self.all_frame, is_owned=False)

        # Owned Cards Tab
        self.owned_frame = tk.Frame(self.notebook)
        self.notebook.add(self.owned_frame, text="Owned Cards")
        self.setup_search_frame(self.owned_frame, owned=True)
        self.setup_table(self.owned_frame, is_owned=True)

        # Deck Builder Tab
        self.deck_builder_frame = tk.Frame(self.notebook)
        self.notebook.add(self.deck_builder_frame, text="Deck Builder")
        self.deck_builder_tab = DeckBuilderTab(self.deck_builder_frame, self.app)
        self.deck_builder_tab.frame.pack(fill="both", expand=True)

    def setup_search_frame(self, parent, owned=False):
        var_prefix = "owned_" if owned else ""
        cards = [c for c in self.cards if self.collection.get(c["card_key"], 0) > 0] if owned else self.cards

        setattr(self.app, f"{var_prefix}search_var", tk.StringVar())
        setattr(self.app, f"{var_prefix}set_filter_var", tk.StringVar())
        setattr(self.app, f"{var_prefix}type_filter_var", tk.StringVar())
        setattr(self.app, f"{var_prefix}aspect_filter_var", tk.StringVar())
        setattr(self.app, f"{var_prefix}arena_filter_var", tk.StringVar())

        frame = tk.Frame(parent)
        frame.pack(pady=10, padx=10, fill="x")

        search_var = getattr(self.app, f"{var_prefix}search_var")
        set_var = getattr(self.app, f"{var_prefix}set_filter_var")
        type_var = getattr(self.app, f"{var_prefix}type_filter_var")
        aspect_var = getattr(self.app, f"{var_prefix}aspect_filter_var")
        arena_var = getattr(self.app, f"{var_prefix}arena_filter_var")

        tk.Entry(frame, textvariable=search_var, width=40).grid(row=1, column=0, padx=5)
        tk.Button(frame, text="Search", command=lambda: self.search_cards(owned)).grid(row=1, column=1, padx=5)
        tk.Button(frame, text="Reset Filters", command=lambda: self.reset_filters(owned)).grid(row=1, column=2, padx=5)

        for i, label in enumerate(["Set", "Type", "Aspect", "Arena"], start=3):
            tk.Label(frame, text=label).grid(row=0, column=i, padx=5)

        filter_data = {
            "Set": set_var,
            "Type": type_var,
            "Aspects": aspect_var,
            "Arenas": arena_var,
        }

        for i, (key, var) in enumerate(filter_data.items(), start=3):
            values = sorted(set(
                v for c in cards for v in (
                    c.get(key, []) if isinstance(c.get(key), list) else c.get(key, "").split(", ")
                ) if v
            ))
            cb = ttk.Combobox(frame, textvariable=var, state="readonly", width=12)
            cb["values"] = ["All"] + values
            cb.set("All")
            cb.grid(row=1, column=i, padx=5)

        # Attach filters after widgets exist
        search_var.trace_add("write", lambda *_: self.search_cards(owned))
        set_var.trace_add("write", lambda *_: self.search_cards(owned))
        type_var.trace_add("write", lambda *_: self.search_cards(owned))
        aspect_var.trace_add("write", lambda *_: self.search_cards(owned))
        arena_var.trace_add("write", lambda *_: self.search_cards(owned))

    def setup_table(self, parent, is_owned):
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        tree = ttk.Treeview(frame, columns=("CardKey", "Owned", "Name", "Set", "Number", "Type", "Aspect", "Arenas", "Cost", "Power", "Health"), show="headings")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        for col in tree["columns"]:
            tree.heading(col, text=col, command=lambda c=col, t=tree: self.sort_column(t, c, False))
            tree.column(col, width=80, stretch=True)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tree.bind("<Double-1>", lambda event, t=tree: self.on_double_click(event, t))

        if is_owned:
            self.app.owned_tree = tree
            self.load_table(owned_only=True)
        else:
            self.app.tree = tree
            self.load_table(owned_only=False)

    def load_table(self, owned_only=False):
        tree = self.app.owned_tree if owned_only else self.app.tree
        tree.delete(*tree.get_children())
        cards = [c for c in self.cards if self.collection.get(c["card_key"], 0) > 0] if owned_only else self.cards

        for card in cards:
            tree.insert("", "end", values=(
                card["card_key"],
                self.collection.get(card["card_key"], 0),
                card.get("Name", "Unknown"),
                card.get("Set", ""),
                card.get("Number", ""),
                card.get("Type", ""),
                ", ".join(card.get("Aspects")) if "Aspects" in card else card.get("Aspects", ""),
                ", ".join(card.get("Arenas")) if "Arenas" in card else card.get("Arenas", ""),
                card.get("Cost", ""),
                card.get("Power", ""),
                card.get("HP", "")
            ))

    def search_cards(self, owned=False):
        var_prefix = "owned_" if owned else ""
        query = getattr(self.app, f"{var_prefix}search_var").get().lower()
        s_set = getattr(self.app, f"{var_prefix}set_filter_var").get()
        s_type = getattr(self.app, f"{var_prefix}type_filter_var").get()
        s_aspect = getattr(self.app, f"{var_prefix}aspect_filter_var").get()
        s_arena = getattr(self.app, f"{var_prefix}arena_filter_var").get()
        tree = self.app.owned_tree if owned else self.app.tree

        data = [c for c in self.cards if self.collection.get(c["card_key"], 0) > 0] if owned else self.cards
        filtered = []

        for card in data:
            score = fuzz.partial_ratio(query, card.get("Name", "").lower()) if query else 100
            if score < CONFIG["search"]["fuzzy_threshold"]:
                continue
            if s_set != "All" and card.get("Set", "") != s_set:
                continue
            if s_type != "All" and card.get("Type", "") != s_type:
                continue
            aspects = card.get("Aspects") if "Aspects" in card else card.get("Aspects", "").split(", ")
            if s_aspect != "All" and s_aspect not in aspects:
                continue
            arenas = card.get("Arenas") if "Arenas" in card else card.get("Arenas", "").split(", ")
            if s_arena != "All" and s_arena not in arenas:
                continue
            filtered.append((score, card))

        filtered.sort(reverse=True, key=lambda x: x[0])
        tree.delete(*tree.get_children())
        for _, card in filtered:
            tree.insert("", "end", values=(
                card["card_key"],
                self.collection.get(card["card_key"], 0),
                card.get("Name", "Unknown"),
                card.get("Set", ""),
                card.get("Number", ""),
                card.get("Type", ""),
                ", ".join(card.get("Aspects")) if "Aspects" in card else card.get("Aspects", ""),
                ", ".join(card.get("Arenas")) if "Arenas" in card else card.get("Arenas", ""),
                card.get("Cost", ""),
                card.get("Power", ""),
                card.get("HP", "")
            ))

    def reset_filters(self, owned=False):
        prefix = "owned_" if owned else ""
        getattr(self.app, f"{prefix}search_var").set("")
        getattr(self.app, f"{prefix}set_filter_var").set("All")
        getattr(self.app, f"{prefix}type_filter_var").set("All")
        getattr(self.app, f"{prefix}aspect_filter_var").set("All")
        getattr(self.app, f"{prefix}arena_filter_var").set("All")
        self.load_table(owned_only=owned)

    def on_double_click(self, event, tree):
        region = tree.identify_region(event.x, event.y)
        if region == "heading":
            return

        col = tree.identify_column(event.x)
        if col == "#2":
            self.set_owned(tree)
        elif col in ("#1", "#3"):
            self.show_card_info(tree)

    def set_owned(self, tree):
        selected_item = tree.focus()
        if not selected_item:
            return

        values = tree.item(selected_item, "values")
        card_key, card_name = values[0], values[2]

        new_owned = simpledialog.askinteger("Set Owned", f"How many copies of {card_name} do you own?", minvalue=0, maxvalue=999)

        if new_owned is not None:
            valid, msg = CardValidator.validate_owned_quantity(new_owned)
            if not valid:
                messagebox.showerror("Validation Error", msg)
                return

            self.collection[card_key] = new_owned
            save_collection(self.collection)
            self.search_cards(owned=(tree == self.app.owned_tree))

    def show_card_info(self, tree):
        selected_item = tree.selection()
        if selected_item:
            card_key = tree.item(selected_item)['values'][0]
            card = next((c for c in self.cards if c["card_key"] == card_key), None)
            if card:
                CardDetailWindow(self.root, self.app, card)

    def sort_column(self, tree, col, reverse):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            data.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for index, (_, k) in enumerate(data):
            tree.move(k, "", index)
        tree.heading(col, command=lambda: self.sort_column(tree, col, not reverse))
