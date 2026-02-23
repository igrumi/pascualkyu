import os
import discord
from discord import app_commands
from discord.ext import commands
from supabase import create_client, Client
from dotenv import load_dotenv
from classes.flip7 import Flip7Lobby
import asyncio
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
        intents.message_content = True  # ¡ESTO ES VITAL PARA EL PREFIJO!
        super().__init__(command_prefix="p!", intents=intents)

    async def setup_hook(self):
        # Sincroniza ambos tipos de comandos
        await self.tree.sync()

bot = Pascualkyu()

@bot.event
async def on_message(message):
    # 1. Si el autor del mensaje es un bot, lo ignoramos por completo
    if message.author.bot:
        return

    await bot.process_commands(message)

ROSA_PALO = 0xF2C1D1

# --- COMANDOS ---
class WatchlistView(discord.ui.View):
    def __init__(self, data, titulo_lista, per_page=5):
        super().__init__(timeout=60)
        self.data = data
        self.titulo_lista = titulo_lista 
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = (len(data) - 1) // per_page + 1

        # Lógica de visibilidad:
        # Si solo hay una página, removemos los botones de la vista
        if self.total_pages <= 1:
            self.remove_item(self.previous)
            self.remove_item(self.next)

    def create_embed(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        items = self.data[start:end]

        embed = discord.Embed(
            title=f"{self.titulo_lista}",
            color=0xF2C1D1
        )

        for i, anime in enumerate(items, start=start + 1):
            embed.add_field(
                name=f"{i}. {anime['title']}",
                value="", # Un pequeño detalle para que no esté vacío
                inline=False
            )
        
        # Opcional: Solo mostrar el footer de paginación si hay más de una página
        if self.total_pages > 1:
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

class DeleteSelect(discord.ui.Select):
    def __init__(self, animes):
        # Creamos las opciones del menú con los animes pendientes
        options = [
            discord.SelectOption(label=a['title'], description="Eliminar permanentemente de la lista 🗑️") 
            for a in animes[:25]
        ]
        super().__init__(placeholder="Elige el anime que quieres eliminar...", options=options)

    async def callback(self, interaction: discord.Interaction):
        titulo = self.values[0]
        # Eliminamos de la base de datos
        result = supabase.table("watchlist").delete().eq("title", titulo).execute()
        
        if result.data:
            await interaction.response.send_message(f"¡Listo! He borrado **{titulo}** de la lista.")
        else:
            await interaction.response.send_message(f"❌ Hubo un error al intentar borrar **{titulo}**.", ephemeral=True)

class DeleteView(discord.ui.View):
    def __init__(self, animes):
        super().__init__(timeout=60)
        self.add_item(DeleteSelect(animes))

@bot.command()
@commands.is_owner() # Solo tú puedes usarlo
async def sync(ctx):
    try:
        # Sincroniza los comandos con el servidor actual
        fmt = await bot.tree.sync()
        await ctx.send(f"¡Sincronizados {len(fmt)} comandos con éxito!")
    except Exception as e:
        await ctx.send(f"Error al sincronizar: {e}")

@bot.hybrid_command(name="add", description="Añade un anime a la lista")
@app_commands.describe(titulo="Nombre del anime")
@commands.has_role("purr")
async def add(ctx: commands.Context, *, titulo: str):
    # ctx.author.name funciona tanto en mensaje como en slash
    data = {"title": titulo, "added_by": ctx.author.name, "status": False}
    supabase.table("watchlist").insert(data).execute()
    emote = discord.utils.get(bot.emojis, name="kase")
    if emote:
        embed = discord.Embed(description=f"{emote} **{titulo}** añadido a la lista.", color=ROSA_PALO)
    else:
        embed = discord.Embed(description=f"**{titulo}** añadido a la lista.", color=ROSA_PALO)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="random", description="Elige un anime al azar")
async def ruleta(ctx: commands.Context):
    response = supabase.table("watchlist").select("*").eq("status", False).execute()
    if not response.data:
        return await ctx.send("No hay animes pendientes.")
    
    # Aquí añadimos un pequeño efecto de suspenso
    msg = await ctx.send("🔍 Eligiendo")
    await asyncio.sleep(0.5) # Espera 2 segundos
    await msg.edit(content="🔍 Eligiendo.")
    await asyncio.sleep(0.5)
    await msg.edit(content="🔍 Eligiendo..")
    await asyncio.sleep(0.5)
    await msg.edit(content="🔍 Eligiendo...")

    elegido = random.choice(response.data)
    embed = discord.Embed(title="Pascualito ha elegido...", description=f"**{elegido['title']}**", color=ROSA_PALO)
    await msg.edit(content=None, embed=embed)

@bot.hybrid_command(name="watched", description="Marca un anime como completado")
async def visto(ctx: commands.Context):
    # El menú desplegable solo funciona bien en interacciones, 
    # pero ctx lo maneja decentemente en ambos
    response = supabase.table("watchlist").select("*").eq("status", False).execute()
    if not response.data:
        return await ctx.send("No hay pendientes.")

    view = VistoView(response.data)
    await ctx.send("Elige la serie a marcar como vista:", view=view)

@bot.hybrid_command(name="watchlist", description="Lista de series por ver")
async def pendientes(ctx: commands.Context):
    response = supabase.table("watchlist").select("*").eq("status", False).execute()
    if not response.data:
        return await ctx.send("¡Todo al día!")
    
    view = WatchlistView(response.data, "Lista de Pendientes <:kase:1466627470949089301>")
    await ctx.send(embed=view.create_embed(), view=view)

@bot.hybrid_command(name="completed", description="Lista de completados")
async def vistos(ctx: commands.Context):
    response = supabase.table("watchlist").select("*").eq("status", True).execute()
    if not response.data:
        return await ctx.send("Aún no hay vistos.")
    
    view = WatchlistView(response.data, "Animes Completados")
    await ctx.send(embed=view.create_embed(), view=view)
    
@bot.hybrid_command(name="delete", description="Elimina un anime (escribe el nombre o usa el menú)")
@app_commands.describe(titulo="Nombre del anime a borrar (opcional)")
@commands.has_role("purr")
async def delete(ctx: commands.Context, *, titulo: str = None): # Ponemos el título como opcional (None)
    # 1. CASO: El usuario escribió un nombre (p!delete Naruto)
    if titulo:
        # Intentamos borrar directamente usando .ilike para evitar líos con mayúsculas
        result = supabase.table("watchlist").delete().ilike("title", titulo).execute()
        
        if result.data:
            return await ctx.send(f"🗑️ ¡Listo! **{titulo}** borrado de la lista.")
        else:
            return await ctx.send(f"❌ No encontré ninguna serie llamada `{titulo}` en los pendientes.")

    # 2. CASO: El usuario no escribió nada (p!delete o /delete sin parámetros)
    # Buscamos los pendientes para el menú desplegable
    response = supabase.table("watchlist").select("*").eq("status", False).execute()
    animes = response.data

    if not animes:
        return await ctx.send("No hay animes pendientes para eliminar.")

    # Mostramos el menú que ya habías creado
    view = DeleteView(animes)
    await ctx.send("Selecciona el anime que deseas eliminar de la lista:", view=view)

@bot.hybrid_command(name="roll", description="Lanza un dado (1-100 o 1-N)")
@app_commands.describe(maximo="El número máximo para el roll (por defecto 100)")
async def roll(ctx: commands.Context, maximo: int = 100):
    # Validamos que el número no sea negativo o cero para evitar errores
    if maximo <= 1:
        return await ctx.send("El número debe ser mayor a 1, intenta de nuevo tonto de mrd")

    # Caso 1 y 2 unificados: elegimos entre 1 y el valor de 'maximo'
    resultado = random.randint(1, maximo)
    
    # Creamos un embed bonito para el resultado
    embed = discord.Embed(
        title="🎲 ¡Roll!",
        description=f"El número elegido es: **{resultado}**",
        color=ROSA_PALO
    )
    embed.set_footer(text=f"Rango: 1 - {maximo}")
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="flip7", description="Inicia un lobby de Flip 7 multijugador")
async def flip7(ctx: commands.Context):
    lobby = Flip7Lobby(ctx.author)
    await ctx.send(f"🎮 **{ctx.author.name}** ha iniciado un lobby de **Flip 7**. ¡Únanse con el botón de abajo! ✨", view=lobby)

# Tip: Manejo de error por si alguien sin el rol intenta borrar
@add.error
@delete.error
async def delete_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("Ups, necesitas el rol `purr` para realizar esta acción.", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)