import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils import emotes
from utils.database import supabase

class Unitedle(commands.Cog):
    def __init__(self, bot, supabase):
        self.bot = bot
        self.supabase = supabase

    @app_commands.command(name="unitedle", description="Adivina el Pokémon del día.")
    async def unitedle(self, interaction: discord.Interaction, guess: str = None):
        today = datetime.now().strftime("%Y-%m-%d")
        
        daily = self.supabase.table("daily_pokemon").select("*, pokemon_unite(*)").eq("date", today).single().execute()
        
        if not daily.data:
            await interaction.response.send_message("⚠️ Aún no se ha seleccionado el Pokémon de hoy. Inténtalo más tarde.", ephemeral=True)
            return

        pokemon = daily.data['pokemon_unite']
        target_name = pokemon['name'].upper()

        if not guess:
            await interaction.response.send_message(f"{emotes.kase} **Unitedle**\nEl Pokémon de hoy tiene {len(target_name)} letras. Cada 3 intentos recibirás una pista adicional. ¡Buena suerte! {emotes.kase}", ephemeral=True)
            return

        check_exists = self.supabase.table("pokemon_unite").select("id").eq("name", guess.title()).execute()
        if not check_exists.data:
            await interaction.response.send_message(f"{emotes.tomatewn} '{guess}' no es un Pokémon válido en Unite.", ephemeral=True)
            return

        guess = guess.upper()
        attempts_data = self.supabase.table("user_attempts").select("*").eq("user_id", interaction.user.id).eq("date", today).execute()
        num_intentos = len(attempts_data.data) + 1
        
        feedback = self.generate_feedback(guess, target_name)
        
        self.supabase.table("user_attempts").insert({
            "user_id": interaction.user.id, 
            "attempt_number": num_intentos, 
            "guess": guess,
            "result_json": feedback
        }).execute()

        embed = discord.Embed(title=f"Unitedle - Intento {num_intentos}", description=f"Tu intento: `{guess}`\nResultado: `{feedback}`")
        
        if num_intentos >= 3:
            embed.add_field(name="Pista 1 (Rol)", value=pokemon['role'], inline=True)
        if num_intentos >= 6:
            evol = "Sí" if pokemon['evolves'] else "No"
            embed.add_field(name="Pista 2 (Evoluciona)", value=evol, inline=True)
        if num_intentos >= 9:
            mega = "Sí" if pokemon['has_mega'] else "No"
            embed.add_field(name="Pista 3 (Mega)", value=mega, inline=True)

        if guess == target_name:
            embed.title = f"¡Ganaste! {emotes.oshahappy}"
            embed.set_image(url=pokemon['image_url'])
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.channel.send(f"🎉 ¡{interaction.user.mention} ha acertado el Pokémon del día!")
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    def generate_feedback(self, guess, target):
        result = ["⬜"] * len(target)
        target_list = list(target)
        
        for i in range(min(len(guess), len(target))):
            if guess[i] == target[i]:
                result[i] = "🟩"
                target_list[i] = None

        for i in range(min(len(guess), len(target))):
            if result[i] == "⬜" and guess[i] in target_list:
                result[i] = "🟨"
                target_list[target_list.index(guess[i])] = None
        return "".join(result)

async def setup(bot):
    await bot.add_cog(Unitedle(bot, supabase))