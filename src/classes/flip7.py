import discord
import random

class MultiFlip7View(discord.ui.View):
    def __init__(self, jugadores):
        super().__init__(timeout=120)
        self.jugadores = jugadores # Lista de objetos Member
        self.index_actual = 0
        self.mazo = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        # Diccionario para guardar las cartas de cada uno {user_id: [cartas]}
        self.tableros = {j.id: [] for j in jugadores}
        self.puntuaciones_finales = {} # Para los que se plantan

    def obtener_jugador_actual(self):
        return self.jugadores[self.index_actual]

    def create_embed(self):
        jugador = self.obtener_jugador_actual()
        cartas = self.tableros[jugador.id]
        
        embed = discord.Embed(
            title="✨ Flip 7 Multiplayer ✨",
            description=f"Turno de: **{jugador.mention}**",
            color=0xF2C1D1
        )
        
        # Mostrar estado de todos
        status_text = ""
        for j in self.jugadores:
            score = sum(self.tableros[j.id])
            emoji = "✅" if j.id in self.puntuaciones_finales else "🎲"
            status_text += f"{emoji} **{j.name}**: {score} pts\n"
        
        embed.add_field(name="Estadísticas de la mesa", value=status_text, inline=False)
        embed.add_field(name="🃏 Cartas en tu mano", value=f"`{cartas if cartas else 'Vacío'}`", inline=True)
        return embed

    async def pasar_turno(self, interaction):
        # Buscamos al siguiente jugador que no se haya plantado
        original_index = self.index_actual
        while True:
            self.index_actual = (self.index_actual + 1) % len(self.jugadores)
            if self.jugadores[self.index_actual].id not in self.puntuaciones_finales:
                break
            if self.index_actual == original_index: # Todos se plantaron
                await self.finalizar_juego(interaction)
                return

        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def finalizar_juego(self, interaction):
        self.stop()
        ganador_id = max(self.puntuaciones_finales, key=self.puntuaciones_finales.get, default=None)
        
        desc = "🏆 **Resultados Finales:**\n"
        for j_id, score in self.puntuaciones_finales.items():
            user = discord.utils.get(self.jugadores, id=j_id)
            desc += f"• {user.name}: {score} pts\n"

        embed = discord.Embed(title="🏁 Fin del Juego", description=desc, color=0xF2C1D1)
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Flip", style=discord.ButtonStyle.primary, emoji="🎲")
    async def flip(self, interaction: discord.Interaction, button: discord.ui.Button):
        jugador = self.obtener_jugador_actual()
        if interaction.user != jugador:
            return await interaction.response.send_message("🎀 No es tu turno, espera un poquito.", ephemeral=True)

        carta = random.choice(self.mazo)
        mano = self.tableros[jugador.id]

        if carta in mano: # BUST
            self.puntuaciones_finales[jugador.id] = 0
            await interaction.channel.send(f"💥 ¡BUST! {jugador.mention} sacó un {carta} repetido y perdió sus puntos.")
            await self.pasar_turno(interaction)
        else:
            mano.append(carta)
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Stay", style=discord.ButtonStyle.success, emoji="✅")
    async def stay(self, interaction: discord.Interaction, button: discord.ui.Button):
        jugador = self.obtener_jugador_actual()
        if interaction.user != jugador:
            return await interaction.response.send_message("No es tu turno.", ephemeral=True)

        self.puntuaciones_finales[jugador.id] = sum(self.tableros[jugador.id])
        await self.pasar_turno(interaction)

class Flip7Lobby(discord.ui.View):
    def __init__(self, creador):
        super().__init__(timeout=60)
        self.creador = creador
        self.jugadores = [creador]

    @discord.ui.button(label="Unirse", style=discord.ButtonStyle.secondary, emoji="✨")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.jugadores:
            return await interaction.response.send_message("Ya estás en la lista, ¡espera a que empiece! 🌸", ephemeral=True)
        
        self.jugadores.append(interaction.user)
        await interaction.response.edit_message(content=f"📝 **Jugadores anotados:** {', '.join([j.name for j in self.jugadores])}")

    @discord.ui.button(label="Iniciar Juego", style=discord.ButtonStyle.success, emoji="🚀")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.creador:
            return await interaction.response.send_message("Solo quien inició el lobby puede empezar el juego. 🎀", ephemeral=True)
        
        game_view = MultiFlip7View(self.jugadores)
        await interaction.response.edit_message(content=None, embed=game_view.create_embed(), view=game_view)