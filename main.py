import tkinter as tk
from gui.app_window import BotManagerApp

def main():
    root = tk.Tk()
    # Setup global styles or configurations if needed here
    app = BotManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
