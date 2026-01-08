import discord
from discord.ext import commands
from discord import app_commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Lösche eine bestimmte Anzahl an Nachrichten")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1:
            await interaction.response.send_message("Menge muss > 0 sein.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Habe {len(deleted)} Nachrichten gelöscht.", ephemeral=True)

    @app_commands.command(name="kick", description="Kicke einen User vom Server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Kein Grund angegeben"):
        try:
            await user.kick(reason=reason)
            embed = discord.Embed(title="User Gekickt", description=f"{user.mention} wurde gekickt.", color=discord.Color.orange())
            embed.add_field(name="Grund", value=reason)
            embed.set_footer(text=f"Mod: {interaction.user.name}")
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("Ich habe nicht genug Rechte, um diesen User zu kicken.", ephemeral=True)

    @app_commands.command(name="ban", description="Banne einen User vom Server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Kein Grund angegeben"):
        try:
            await user.ban(reason=reason)
            embed = discord.Embed(title="User Gebannt", description=f"{user.mention} wurde gebannt.", color=discord.Color.red())
            embed.add_field(name="Grund", value=reason)
            embed.set_footer(text=f"Mod: {interaction.user.name}")
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("Ich habe nicht genug Rechte, um diesen User zu bannen.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
