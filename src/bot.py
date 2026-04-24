from discord.ext import tasks
import os
import discord
from discord import app_commands
from discord.ext import commands
from utils.database import supabase
from dotenv import load_dotenv
from classes.flip7 import *
from classes.watchlist import WatchlistView, VistoView, DeleteView
import asyncio
import random
from utils import emotes

# Configuración de Supabase
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
admin_id = int(os.getenv("ADMIN_ID"))

class Pascualkyu(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="p!", intents=intents)

    async def setup_hook(self):
        await self.load_extension('cogs.unitedle')
        print("✅ Módulo Unitedle cargado.")
        await self.tree.sync()

bot = Pascualkyu()

@bot.event
async def on_ready():
    keep_alive.start()
    emotes.setup_emotes(bot)
    print(f"✅ Bot conectado como {bot.user} y emotes cargados.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

ROSA_PALO = 0xF2C1D1

# --- COMANDOS ---
@bot.command()
@commands.is_owner()
async def sync(ctx):
    try:
        fmt = await bot.tree.sync()
        await ctx.send(f"¡Sincronizados {len(fmt)} comandos con éxito! {emotes.kase}", ephemeral=True)
    except Exception as e:
        await ctx.send(f"Error al sincronizar: {e}")

@bot.hybrid_command(name="add", description="Añade un anime a la lista")
@app_commands.describe(titulo="Nombre del anime")
@commands.has_role("purr")
async def add(ctx: commands.Context, *, titulo: str):
    data = {"title": titulo, "added_by": ctx.author.name, "status": False}
    supabase.table("watchlist").insert(data).execute()
    if emotes.kase:
        embed = discord.Embed(description=f"{emotes.kase} **{titulo}** añadido a la lista.", color=ROSA_PALO)
    else:
        embed = discord.Embed(description=f"**{titulo}** añadido a la lista.", color=ROSA_PALO)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="random", description="Elige un anime al azar")
async def ruleta(ctx: commands.Context):
    response = supabase.table("watchlist").select("*").eq("status", False).execute()
    if not response.data:
        return await ctx.send("No hay animes pendientes.")
    
    msg = await ctx.send(f"{emotes.mrtitties} Eligiendo.")
    await asyncio.sleep(0.5)
    await msg.edit(content=f"{emotes.mrpenis} Eligiendo..")
    await asyncio.sleep(0.5)
    await msg.edit(content=f"{emotes.mrballs} Eligiendo...")

    elegido = random.choice(response.data)
    embed = discord.Embed(title="Pascualito ha elegido...", description=f"**{elegido['title']}**", color=ROSA_PALO)
    await msg.edit(content=None, embed=embed)

@bot.hybrid_command(name="watched", description="Marca un anime como completado")
async def visto(ctx: commands.Context):
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
async def delete(ctx: commands.Context, *, titulo: str = None):
    if titulo:
        result = supabase.table("watchlist").delete().ilike("title", titulo).execute()
        
        if result.data:
            return await ctx.send(f"🗑️ ¡Listo! **{titulo}** borrado de la lista.")
        else:
            return await ctx.send(f"❌ No encontré ninguna serie llamada `{titulo}` en los pendientes.")

    
    response = supabase.table("watchlist").select("*").eq("status", False).execute()
    animes = response.data

    if not animes:
        return await ctx.send("No hay animes pendientes para eliminar.")

    view = DeleteView(animes)
    await ctx.send("Selecciona el anime que deseas eliminar de la lista:", view=view)

@bot.hybrid_command(name="roll", description="Lanza un dado (1-100 o 1-N)")
@app_commands.describe(maximo="El número máximo para el roll (por defecto 100)")
async def roll(ctx: commands.Context, maximo: int = 100):
    if maximo <= 1:
        return await ctx.send("El número debe ser mayor a 1, intenta de nuevo tonto de mrd")

    resultado = random.randint(1, maximo)

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
    await ctx.send(f"🎮 **{ctx.author.name}** ha iniciado un lobby de **Flip 7**. ¡Únanse con el botón de abajo! {emotes.happy}", view=lobby)

@add.error
@delete.error
async def delete_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("Ups, necesitas el rol `purr` para realizar esta acción.", ephemeral=True)

@tasks.loop(hours=48)
async def keep_alive():
    try:
        supabase.table("watchlist").select("id").limit(1).execute()
        print("✅ Heartbeat a Supabase enviado.")
    except Exception as e:
        print(f"❌ Error al enviar heartbeat a Supabase: {e}")
    
if __name__ == "__main__":
    bot.run(TOKEN)