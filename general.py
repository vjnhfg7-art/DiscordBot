import discord
from discord.ext import commands
from discord import app_commands
import random

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Zeige Infos über einen User")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        embed = discord.Embed(title=f"User Info: {member.display_name}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Account erstellt", value=member.created_at.strftime("%d.%m.%Y"), inline=True)
        embed.add_field(name="Beigetreten", value=member.joined_at.strftime("%d.%m.%Y"), inline=True)
        
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        embed.add_field(name=f"Rollen ({len(roles)})", value=" ".join(roles) if roles else "Keine", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Zeige Infos über den Server")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"Server Info: {guild.name}", color=discord.Color.blue())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Mitglieder", value=guild.member_count, inline=True)
        embed.add_field(name="Erstellt am", value=guild.created_at.strftime("%d.%m.%Y"), inline=True)
        embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier} ({guild.premium_subscription_count} Boosts)", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Frag die magische Miesmuschel")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "Ja, absolut!", "Sieht gut aus.", "Definitiv.", 
            "Frag später nochmal.", "Ich weiß es nicht...", "Eher nicht.",
            "Auf keinen Fall!", "Träum weiter."
        ]
        answer = random.choice(responses)
        
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=discord.Color.purple())
        embed.add_field(name="Frage", value=question, inline=False)
        embed.add_field(name="Antwort", value=answer, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Wirf eine Münze")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Kopf", "Zahl"])
        await interaction.response.send_message(f"🪙 Die Münze zeigt... **{result}**!")

async def setup(bot):
    await bot.add_cog(General(bot))
