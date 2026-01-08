import threading
import asyncio
import discord
from discord.ext import commands
import datetime
import os

class BotThread(threading.Thread):
    def __init__(self, token, log_queue, started_event):
        super().__init__()
        self.token = token
        self.log_queue = log_queue
        self.loop = None
        self.bot = None
        self.started_event = started_event

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        intents = discord.Intents.default()
        # Ensure we have what we need, even if we use Slash CMDs, sometimes guild intents help
        intents.guilds = True
        
        self.bot = commands.Bot(command_prefix="!", intents=intents)

        # Remove default help to avoid conflicts if we add one later, though Slash commands don't use it much
        self.bot.remove_command("help")

        self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Starte Bot...")

        @self.bot.event
        async def on_ready():
            self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Eingeloggt als: {self.bot.user}")
            self.started_event.set()
            
            # Load Cogs
            await self.load_extensions()

            # Sync Tree
            try:
                synced = await self.bot.tree.sync()
                self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {len(synced)} Slash-Commands synchronisiert.")
            except Exception as e:
                self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Sync Fehler: {e}")

        try:
            self.loop.run_until_complete(self.bot.start(self.token))
        except Exception as e:
            self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] CRITICAL ERROR: {e}")
        finally:
            self.cleanup()

    async def load_extensions(self):
        # We assume we are in root/bot/manager.py context? No, we are running from main.py in root.
        # So "bot.cogs.tickets" should work.
        initial_extensions = [
            'bot.cogs.tickets',
            'bot.cogs.general',
            'bot.cogs.moderation'
        ]
        
        for extension in initial_extensions:
            try:
                await self.bot.load_extension(extension)
                self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Modul geladen: {extension}")
            except Exception as e:
                self.log_queue.put(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Fehler beim Laden von {extension}: {e}")

    def stop(self):
        if self.bot and self.loop:
            future = asyncio.run_coroutine_threadsafe(self.bot.close(), self.loop)
            try:
                future.result(timeout=5)
            except:
                pass

    def cleanup(self):
        try:
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            self.loop.close()
        except:
            pass
