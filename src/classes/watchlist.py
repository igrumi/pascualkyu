import discord
from discord.ext import commands
from utils.database import supabase

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