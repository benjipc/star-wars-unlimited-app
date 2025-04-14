# main.py

import tkinter as tk
from app.card_app import CardApp


def main():
    root = tk.Tk()
    app = CardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
