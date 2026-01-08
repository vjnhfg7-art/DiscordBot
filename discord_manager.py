import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import asyncio
import discord
from discord.ext import commands
import datetime
import queue

# ------------------------------------------------------------------------------
# DISCORD BOT LOGIC
# ------------------------------------------------------------------------------

class TicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view

    @discord.ui.button(label="Ticket öffnen", style=discord.ButtonStyle.green, custom_id="ticket_open_btn", emoji="📩")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Notify user instantly
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Create private channel
        channel_name = f"ticket-{interaction.user.name}"
        try:
            ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        except Exception as e:
            await interaction.followup.send(f"Fehler beim Erstellen des Channels: {e}", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Willkommen, {interaction.user.display_name}!",
            description="Ein Teammitglied wird sich bald um dich kümmern.\nDrücke auf den Button unten, um das Ticket zu schließen.",
            color=discord.Color.blue()
        )
        
        await ticket_channel.send(content=f"{interaction.user.mention}", embed=embed, view=TicketControls())
        await interaction.followup.send(f"Dein Ticket wurde erstellt: {ticket_channel.mention}", ephemeral=True)


class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket schließen", style=discord.ButtonStyle.red, custom_id="ticket_close_btn", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Das Ticket wird in 5 Sekunden gelöscht...", ephemeral=True)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass # Channel might already be deleted

class BotThread(threading.Thread):
    def __init__(self, token, log_queue, started_event):
        super().__init__()
        self.token = token
        self.log_queue = log_queue
        self.loop = None
        self.bot = None
        self.started_event = started_event # To signal GUI we started loop

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Standard Intents (ohne Message Content, um Fehler zu vermeiden)
        intents = discord.Intents.default()
        
        self.bot = commands.Bot(command_prefix="!", intents=intents)

        # Signal log
        self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Bot Thread gestartet. Versuche Login...")

        @self.bot.event
        async def on_ready():
            msg = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Eingeloggt als: {self.bot.user} (ID: {self.bot.user.id})"
            self.log_queue.put(msg)
            self.started_event.set()
            
            # Register Views for persistence
            self.bot.add_view(TicketLauncher())
            self.bot.add_view(TicketControls())

            # Sync Slash Commands
            try:
                synced = await self.bot.tree.sync()
                self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {len(synced)} Slash-Commands synchronisiert.")
                self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Nutze '/ticketpanel' im Discord.")
            except Exception as e:
                self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Fehler beim Sync: {e}")

        # Slash Command Definition
        @self.bot.tree.command(name="ticketpanel", description="Sende das Ticket-Panel in diesen Kanal")
        async def ticketpanel(interaction: discord.Interaction):
            # Check permissions if needed, here just basic
            embed = discord.Embed(
                title="Ticket Support",
                description="Klicke auf den Button unten, um ein privates Ticket zu erstellen.",
                color=discord.Color.green()
            )
            
            # Send to channel and confirm to user ephemerally
            await interaction.response.send_message("Panel wird erstellt...", ephemeral=True)
            await interaction.channel.send(embed=embed, view=TicketLauncher())
            
            self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Ticket-Panel Command ausgeführt in '{interaction.channel.name}'.")

        try:
            self.loop.run_until_complete(self.bot.start(self.token))
        except discord.LoginFailure:
            self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] FEHLER: Ungültiger Token!")
        except Exception as e:
            self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] FEHLER: {e}")
        finally:
            self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Bot Loop beendet.")
            # Ensure proper cleanup
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            self.loop.close()

    def stop(self):
        if self.bot and self.loop:
            future = asyncio.run_coroutine_threadsafe(self.bot.close(), self.loop)
            try:
                future.result(timeout=5)
            except:
                pass

# ------------------------------------------------------------------------------
# GUI LOGIC
# ------------------------------------------------------------------------------

class BotManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Bot Manager v1.0")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Style configuration
        style = ttk.Style()
        style.theme_use('clam') # Clean standard theme
        
        # Colors & Fonts
        bg_color = "#2b2b2b"
        fg_color = "#ffffff"
        accent_color = "#7289da" # Discord blurple-ish
        
        # Apply dark theme to main window
        self.root.configure(bg=bg_color)
        
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        
        # Custom button styles
        style.map("Start.TButton", background=[('active', '#43b581')], foreground=[('active', 'white')])
        style.configure("Start.TButton", background="#43b581", foreground="white") # Green
        
        style.map("Stop.TButton", background=[('active', '#f04747')], foreground=[('active', 'white')])
        style.configure("Stop.TButton", background="#f04747", foreground="white") # Red

        # --- Variables ---
        self.bot_thread = None
        self.log_queue = queue.Queue()
        self.is_running = False

        # --- Layout ---
        
        # Header
        header_frame = ttk.Frame(root, padding=20)
        header_frame.pack(fill="x")
        
        title_lbl = ttk.Label(header_frame, text="Discord Bot Manager", font=("Segoe UI", 18, "bold"))
        title_lbl.pack(side="left")

        # Input Area
        input_frame = ttk.Frame(root, padding=20)
        input_frame.pack(fill="x")

        ttk.Label(input_frame, text="Bot Token:").pack(anchor="w", pady=(0, 5))
        
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(input_frame, textvariable=self.token_var, width=60, font=("Consolas", 10))
        self.token_entry.pack(fill="x", pady=5)
        # self.token_entry.config(show="*") # Uncomment to mask token if desired

        # Buttons
        btn_frame = ttk.Frame(root, padding=20)
        btn_frame.pack(fill="x")

        self.start_btn = ttk.Button(btn_frame, text="Start Bot", style="Start.TButton", command=self.start_bot)
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ttk.Button(btn_frame, text="Stop Bot", style="Stop.TButton", command=self.stop_bot, state="disabled")
        self.stop_btn.pack(side="left")

        # Log Area
        log_frame = ttk.Frame(root, padding=10)
        log_frame.pack(fill="both", expand=True)

        ttk.Label(log_frame, text="Log Output:").pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state="disabled", font=("Consolas", 9), bg="#1e1e1e", fg="#00ff00")
        self.log_text.pack(fill="both", expand=True, pady=5)

        # Polling for logs
        self.root.after(100, self.process_logs)

    def log(self, message):
        """Insert message into log widget safely."""
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def process_logs(self):
        """Check queue for new log messages."""
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
        
        self.log("Stopping Bot... bitte warten...")
        self.stop_btn.config(state="disabled")
        
        # Run shutdown in a separate thread to avoid freezing GUI while waiting for future
        threading.Thread(target=self._shutdown_thread).start()

    def _shutdown_thread(self):
        self.bot_thread.stop()
        self.bot_thread.join()
        
        # Reset GUI state from main thread
        self.root.after(0, self._reset_gui)

    def _reset_gui(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.token_entry.config(state="normal")
        self.is_running = False
        self.log("Bot wurde beendet.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BotManagerApp(root)
    root.mainloop()
