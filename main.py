import tkinter as tk
from app.card_app import CardApp
import sys

def main():
    try:
        root = tk.Tk()
        root.title("Star Wars Unlimited Card App")
        root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
        
        app = CardApp(root)
        root.mainloop()
    except ModuleNotFoundError as e:
        print(f"Error: Failed to load required module - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def on_closing(root):
    """Handle cleanup when closing the application"""
    try:
        root.destroy()
    except Exception as e:
        print(f"Error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
