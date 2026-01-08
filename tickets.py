import discord
from discord.ext import commands
from discord import app_commands
import datetime
import io

class TicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket erstellen", style=discord.ButtonStyle.blurple, custom_id="ticket_create_main", emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Give the user a Selection Menu to choose category
        await interaction.response.send_message("Bitte wähle eine Kategorie:", view=CategorySelect(), ephemeral=True)

class CategorySelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # We might want this short lived actually, but ephemeral cleans itself visually

    @discord.ui.select(
        placeholder="Wähle einen Grund...",
        options=[
            discord.SelectOption(label="Allgemeiner Support", value="support", description="Fragen zum Server oder Bot", emoji="❓"),
            discord.SelectOption(label="Fehler melden", value="bug", description="Du hast einen Bug gefunden?", emoji="🐛"),
            discord.SelectOption(label="Benutzer melden", value="report", description="Verstoß gegen Regeln melden", emoji="👮"),
            discord.SelectOption(label="Abrechnung / Spenden", value="billing", description="Fragen zu Geld", emoji="💸"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        category_name = select.values[0]
        guild = interaction.guild
        
        # Permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel_name = f"ticket-{category_name}-{interaction.user.name}"
        
        try:
            # Maybe find a category to put it in? For now just top level
            ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        except Exception as e:
            await interaction.response.edit_message(content=f"Fehler: {e}", view=None)
            return

        embed = discord.Embed(
            title=f"Ticket: {category_name.capitalize()}",
            description=f"Hallo {interaction.user.mention}!\nEin Teammitglied wird sich bald um dein Anliegen kümmern.\n\nKategorie: **{category_name}**",
            color=discord.Color.gold()
        )
        
        await ticket_channel.send(content=f"{interaction.user.mention}", embed=embed, view=TicketControls())
        await interaction.response.edit_message(content=f"Dein Ticket wurde erstellt: {ticket_channel.mention}", view=None)

class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Schließen", style=discord.ButtonStyle.red, custom_id="ticket_close", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # Generate Transcript
        messages = [message async for message in interaction.channel.history(limit=500, oldest_first=True)]
        
        transcript_text = f"Transcript for {interaction.channel.name}\nGenerated at {datetime.datetime.now()}\n\n"
        for msg in messages:
            transcript_text += f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.author.name}: {msg.content}\n"
        
        transcript_file = discord.File(io.BytesIO(transcript_text.encode('utf-8')), filename=f"transcript-{interaction.channel.name}.txt")
        
        # Try to DM user
        try:
            await interaction.user.send("Dein Ticket wurde geschlossen. Hier ist der Verlauf:", file=transcript_file)
        except:
            pass # DM closed
            
        await interaction.channel.send("Ticket wird in 5 Sekunden gelöscht...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Beanspruchen", style=discord.ButtonStyle.green, custom_id="ticket_claim", emoji="👋")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.set_footer(text=f"Bearbeitet von: {interaction.user.display_name}")
        button.disabled = True
        button.label = "In Bearbeitung"
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.channel.send(f"{interaction.user.mention} hat dieses Ticket übernommen.")
        
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketLauncher())
        self.bot.add_view(TicketControls())

    @app_commands.command(name="ticketpanel", description="Sende das erweiterte Ticket-Panel")
    async def ticketpanel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Nur Admins dürfen das!", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="🎫 Support Center",
            description="Benötigst du Hilfe? Klicke unten auf den Button um ein Ticket zu öffnen.",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.channel.send(embed=embed, view=TicketLauncher())
        await interaction.response.send_message("Panel gesendet!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
