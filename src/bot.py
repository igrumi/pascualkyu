import os
import discord
from discord import app_commands
from discord.ext import commands
from supabase import create_client, Client
from dotenv import load_dotenv
import random

# Configuración de Supabase
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(URL, KEY)

class Pascualkyu(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="p!", intents=intents)

    async def setup_hook(self):
        # Esto sincroniza los slash commands
        await self.tree.sync()

bot = Pascualkyu()
ROSA_PALO = 0xF2C1D1

# --- COMANDOS ---
class WatchlistView(discord.ui.View):
    def __init__(self, data, titulo_lista, per_page=5): # Añadimos titulo_lista
        super().__init__(timeout=60)
        self.data = data
        self.titulo_lista = titulo_lista 
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = (len(data) - 1) // per_page + 1

    def create_embed(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        items = self.data[start:end]

        embed = discord.Embed(
            title=f"{self.titulo_lista}",
            color=0xF2C1D1
        )

        for i, anime in enumerate(items, start=start + 1):
            # En la lista de vistos ya no necesitamos el estado, quizá la fecha o quién lo añadió
            embed.add_field(
                name=f"{i}. {anime['title']}",
                value="",
                inline=False
            )
        
        embed.set_footer(text=f"Página {self.current_page + 1} de {self.total_pages}")
        return embed

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Siguiente", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

class VistoSelect(discord.ui.Select):
    def __init__(self, animes):
        # Creamos las opciones del menú basadas en los animes de la DB
        options = [
            discord.SelectOption(label=a['title'], description="Marcar como visto") 
            for a in animes[:25] # Limitamos a los primeros 25
        ]
        super().__init__(placeholder="Elige un anime de la lista...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Lo que pasa cuando eligen un anime
        titulo = self.values[0]
        supabase.table("watchlist").update({"status": True}).eq("title", titulo).execute()
        
        await interaction.response.send_message(f"✅ ¡Listo! **{titulo}** ahora está en la lista de vistos.")

class VistoView(discord.ui.View):
    def __init__(self, animes):
        super().__init__()
        self.add_item(VistoSelect(animes))

@bot.command()
@commands.is_owner() # Solo tú puedes usarlo
async def sync(ctx):
    try:
        # Sincroniza los comandos con el servidor actual
        fmt = await bot.tree.sync()
        await ctx.send(f"¡Sincronizados {len(fmt)} comandos con éxito!")
    except Exception as e:
        await ctx.send(f"Error al sincronizar: {e}")

@bot.tree.command(name="add", description="Añade un anime a la lista")
@app_commands.checks.has_role("purr") # Cambia por el nombre de tu rol
async def add(interaction: discord.Interaction, titulo: str):
    data = {"title": titulo, "added_by": interaction.user.name, "status": False}
    supabase.table("watchlist").insert(data).execute()
    
    embed = discord.Embed(description=f"**{titulo}** ha sido añadido a la lista.", color=ROSA_PALO)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ruleta", description="Elige un anime al azar para ver")
async def ruleta(interaction: discord.Interaction):
    # Traemos solo los no vistos
    response = supabase.table("watchlist").select("*").eq("status", False).execute()
    anime_list = response.data
    
    if not anime_list:
        return await interaction.response.send_message("No hay animes pendientes en la lista.")
    
    elegido = random.choice(anime_list)
    embed = discord.Embed(
        title="",
        description=f"**{elegido['title']}**",
        color=ROSA_PALO
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="visto", description="Selecciona un anime que ya hayas visto")
async def visto(interaction: discord.Interaction):
    # Traemos solo los que NO están vistos para el menú
    response = supabase.table("watchlist").select("*").eq("status", False).execute()
    animes = response.data

    if not animes:
        return await interaction.response.send_message("No hay animes pendientes para marcar.")

    view = VistoView(animes)
    await interaction.response.send_message("¿Cuál de estos animes terminaron de ver?", view=view)

@bot.tree.command(name="pendientes", description="Muestra los animes por ver")
async def pendientes(interaction: discord.Interaction):
    response = supabase.table("watchlist").select("*").eq("status", False).execute()
    
    if not response.data:
        return await interaction.response.send_message("No hay nada pendiente. ¡Estamos al día!", ephemeral=True)
    
    view = WatchlistView(response.data, "Lista de Pendientes")
    await interaction.response.send_message(embed=view.create_embed(), view=view)

@bot.tree.command(name="vistos", description="Muestra los animes que ya completamos")
async def vistos(interaction: discord.Interaction):
    response = supabase.table("watchlist").select("*").eq("status", True).execute()
    
    if not response.data:
        return await interaction.response.send_message("Aún no hemos terminado ningún anime de la lista.", ephemeral=True)
    
    view = WatchlistView(response.data, "Animes Completados")
    await interaction.response.send_message(embed=view.create_embed(), view=view)
    
@bot.tree.command(name="delete", description="Elimina un anime de la watchlist")
@app_commands.checks.has_role("purr")
async def delete(interaction: discord.Interaction, titulo: str):
    # Avisamos que estamos procesando
    await interaction.response.defer()
    
    # Intentamos eliminarlo de Supabase
    # .execute() devolverá los datos de la fila eliminada
    result = supabase.table("watchlist").delete().eq("title", titulo).execute()
    
    if result.data:
        embed = discord.Embed(
            description=f"Se ha eliminado **{titulo}** de la lista.",
            color=ROSA_PALO
        )
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"No encontré ningún anime llamado `{titulo}` en la lista.")

# Tip: Manejo de error por si alguien sin el rol intenta borrar
@delete.error
async def delete_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("Ups, necesitas el rol `purr` para borrar cosas.", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)