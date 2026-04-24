import os
import discord
from discord.ext import commands
from datetime import datetime

from supabase import create_client

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase_client = create_client(URL, KEY)

class Unitedle(commands.Cog):
    def __init__(self, bot, supabase):
        self.bot = bot
        self.supabase = supabase

    @commands.hybrid_command(name="unitedle", description="Adivina el Pokémon del día.")
    async def unitedle(self, ctx, guess: str = None):
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 1. Obtener el Pokémon del día de la tabla daily_pokemon
        daily = self.supabase.table("daily_pokemon").select("*, pokemon_unite(*)").eq("date", today).single().execute()
        
        if not daily.data:
            await ctx.send("⚠️ Aún no se ha seleccionado el Pokémon de hoy. ¡Inténtalo más tarde!")
            return

        pokemon = daily.data['pokemon_unite']
        target_name = pokemon['name'].upper()

        # Si el usuario no envió un intento, mostrar estado actual
        if not guess:
            await ctx.send(f"🎮 **Unitedle Diario**\nEl Pokémon tiene {len(target_name)} letras. ¡Adivina!")
            return

        # 2. Validar que el Pokémon exista en tu lista
        check_exists = self.supabase.table("pokemon_unite").select("id").eq("name", guess.title()).execute()
        if not check_exists.data:
            await ctx.send(f"❌ '{guess}' no es un Pokémon válido en Unite.")
            return

        # 3. Registrar intento y calcular lógica
        guess = guess.upper()
        # Aquí guardas en user_attempts y obtienes el historial
        attempts_data = self.supabase.table("user_attempts").select("*").eq("user_id", ctx.author.id).eq("date", today).execute()
        num_intentos = len(attempts_data.data) + 1
        
        # Lógica de colores (Wordle)
        feedback = self.generate_feedback(guess, target_name)
        
        # Guardar intento en DB
        self.supabase.table("user_attempts").insert({
            "user_id": ctx.author.id, 
            "attempt_number": num_intentos, 
            "guess": guess,
            "result_json": feedback
        }).execute()

        # 4. Construir Embed con Pistas
        embed = discord.Embed(title=f"Unitedle - Intento {num_intentos}", description=f"Tu intento: `{guess}`\nResultado: `{feedback}`")
        
        # Lógica de pistas (al 3er, 6to y 9no intento)
        if num_intentos >= 3:
            embed.add_field(name="Pista 1 (Rol)", value=pokemon['role'], inline=True)
        if num_intentos >= 6:
            evol = "Sí" if pokemon['evolves'] else "No"
            embed.add_field(name="Pista 2 (Evoluciona)", value=evol, inline=True)
        if num_intentos >= 9:
            mega = "Sí" if pokemon['has_mega'] else "No"
            embed.add_field(name="Pista 3 (Mega)", value=mega, inline=True)

        if guess == target_name:
            embed.title = "¡Ganaste! 🎉"
            embed.set_image(url=pokemon['image_url']) # Usamos la URL del bucket

        await ctx.send(embed=embed)

    def generate_feedback(self, guess, target):
        # Lógica de colores (🟩, 🟨, ⬜)
        result = ["⬜"] * len(target)
        target_list = list(target)
        guess_list = list(guess)
        
        # Verdes
        for i in range(min(len(guess), len(target))):
            if guess[i] == target[i]:
                result[i] = "🟩"
                target_list[i] = None
        # Amarillos
        for i in range(min(len(guess), len(target))):
            if result[i] == "⬜" and guess[i] in target_list:
                result[i] = "🟨"
                target_list[target_list.index(guess[i])] = None
        return "".join(result)

# Para registrar el cog en tu bot principal
async def setup(bot):
    await bot.add_cog(Unitedle(bot, supabase_client))