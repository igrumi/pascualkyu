import os
import discord
from discord.ext import commands
from datetime import datetime
from utils import emotes
from utils.database import supabase

class Unitedle(commands.Cog):
    def __init__(self, bot, supabase):
        self.bot = bot
        self.supabase = supabase

    @commands.hybrid_command(name="unitedle", description="Adivina el Pokémon del día.")
    async def unitedle(self, ctx, guess: str = None):
        today = datetime.now().strftime("%Y-%m-%d")
        
        daily = self.supabase.table("daily_pokemon").select("*, pokemon_unite(*)").eq("date", today).single().execute()
        
        if not daily.data:
            await ctx.send("⚠️ Aún no se ha seleccionado el Pokémon de hoy. Inténtalo más tarde.")
            return

        pokemon = daily.data['pokemon_unite']
        target_name = pokemon['name'].upper()

        if not guess:
            await ctx.send(f"{emotes.kase} **Unitedle**\nEl Pokémon de hoy tiene {len(target_name)} letras. Cada 3 intentos recibirás una pista adicional. ¡Buena suerte! {emotes.kase}")
            return

        check_exists = self.supabase.table("pokemon_unite").select("id").eq("name", guess.title()).execute()
        if not check_exists.data:
            await ctx.send(f"{emotes.tomatewn} '{guess}' no es un Pokémon válido en Unite.")
            return

        guess = guess.upper()
        attempts_data = self.supabase.table("user_attempts").select("*").eq("user_id", ctx.author.id).eq("date", today).execute()
        num_intentos = len(attempts_data.data) + 1
        
        feedback = self.generate_feedback(guess, target_name)
        
        self.supabase.table("user_attempts").insert({
            "user_id": ctx.author.id, 
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
            embed.title = "¡Ganaste! emotes.oshahappy"
            embed.set_image(url=pokemon['image_url'])

        await ctx.send(embed=embed)

    def generate_feedback(self, guess, target):
        result = ["⬜"] * len(target)
        target_list = list(target)
        guess_list = list(guess)
        
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