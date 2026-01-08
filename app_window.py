import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import queue
import threading
from bot.manager import BotThread

class BotManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Bot Manager v2.0 (Pro)")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Style configuration
        self.setup_styles()

        # --- Variables ---
        self.bot_thread = None
        self.log_queue = queue.Queue()
        self.is_running = False

        # --- Layout ---
        self.create_widgets()

        # Polling for logs
        self.root.after(100, self.process_logs)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        bg_dark = "#2b2b2b"
        fg_white = "#ffffff"
        
        self.root.configure(bg=bg_dark)
        
        style.configure("TFrame", background=bg_dark)
        style.configure("TLabel", background=bg_dark, foreground=fg_white, font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        
        style.map("Start.TButton", background=[('active', '#43b581')], foreground=[('active', 'white')])
        style.configure("Start.TButton", background="#43b581", foreground="white")
        
        style.map("Stop.TButton", background=[('active', '#f04747')], foreground=[('active', 'white')])
        style.configure("Stop.TButton", background="#f04747", foreground="white")

    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root, padding=20)
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="Discord Bot Manager Pro", font=("Segoe UI", 20, "bold")).pack(side="left")

        # Input
        input_frame = ttk.Frame(self.root, padding=20)
        input_frame.pack(fill="x")
        ttk.Label(input_frame, text="Bot Token:").pack(anchor="w", pady=(0, 5))
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(input_frame, textvariable=self.token_var, width=70, font=("Consolas", 10))
        self.token_entry.pack(fill="x", pady=5)

        # Buttons
        btn_frame = ttk.Frame(self.root, padding=20)
        btn_frame.pack(fill="x")
        self.start_btn = ttk.Button(btn_frame, text="Start Bot", style="Start.TButton", command=self.start_bot)
        self.start_btn.pack(side="left", padx=(0, 10))
        self.stop_btn = ttk.Button(btn_frame, text="Stop Bot", style="Stop.TButton", command=self.stop_bot, state="disabled")
        self.stop_btn.pack(side="left")

        # Log
        log_frame = ttk.Frame(self.root, padding=10)
        log_frame.pack(fill="both", expand=True)
        ttk.Label(log_frame, text="Console Output:").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state="disabled", font=("Consolas", 9), bg="#1e1e1e", fg="#00ff00")
        self.log_text.pack(fill="both", expand=True, pady=5)

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def process_logs(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log(msg)
        except queue.Empty:
            pass
        self.root.after(100, self.process_logs)

    def start_bot(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("Fehler", "Bitte gib erst einen Token ein!")
            return

        if self.is_running:
            return

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.token_entry.config(state="disabled")
        self.is_running = True

        start_event = threading.Event()
        self.bot_thread = BotThread(token, self.log_queue, start_event)
        self.bot_thread.start()

    def stop_bot(self):
        if not self.is_running or not self.bot_thread:
            return
        
        self.log("Stopping Bot...")
        self.stop_btn.config(state="disabled")
        threading.Thread(target=self._shutdown_thread).start()

    def _shutdown_thread(self):
        self.bot_thread.stop()
        self.bot_thread.join()
        self.root.after(0, self._reset_gui)

    def _reset_gui(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.token_entry.config(state="normal")
        self.is_running = False
        self.log("Bot beendet.")
