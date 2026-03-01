import discord
import random
from utils import emotes

class MultiFlip7View(discord.ui.View):
    def __init__(self, players):
        super().__init__(timeout=120)
        random.shuffle(players)
        self.players = players # Lista de objetos Member
        self.current_index = 0
        self.deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        self.boards = {j.id: [] for j in players}
        self.final_scores = {} # Para los que se plantan

    def get_current_player(self):
        return self.players[self.current_index]

    def create_embed(self):
        player = self.get_current_player()
        cards = self.boards[player.id]
        
        embed = discord.Embed(
            title=f"{emotes.kase} Flip 7 Multiplayer {emotes.kasen}",
            description=f"Turno de: **{player.mention}** {emotes.oshahappy}",
            color=0xF2C1D1
        )
        
        # Mostrar estado de todos
        status_text = ""
        for j in self.players:
            score = sum(self.boards[j.id])
            emoji = "✅" if j.id in self.final_scores else "🎲"
            status_text += f"{emoji} **{j.name}**: {score} pts\n"
        
        embed.add_field(name="Estadísticas de la mesa", value=status_text, inline=False)
        embed.add_field(name="🃏 Cartas en tu mano", value=f"`{cards if cards else 'Vacío'}`", inline=True)
        return embed

    async def stay_turn(self, interaction):
        # Buscamos al siguiente player que no se haya plantado
        original_index = self.current_index
        while True:
            self.current_index = (self.current_index + 1) % len(self.players)
            if self.players[self.current_index].id not in self.final_scores:
                break
            if self.current_index == original_index: # Todos se plantaron
                await self.end_game(interaction)
                return

        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def end_game(self, interaction):
        self.stop()
        
        # 1. Convertimos el diccionario en una lista de tuplas (user_id, score) 
        # y la ordenamos de mayor a menor puntuación
        sorted_results = sorted(self.final_scores.items(), key=lambda item: item[1], reverse=True)
        
        desc = "🏆 **Resultados Finales:**\n\n"
        
        # Emojis para el podio
        medals = ["🥇", "🥈", "🥉"]
        podium_count = 0

        for j_id, score in sorted_results:
            user = discord.utils.get(self.players, id=j_id)
            
            # Caso: El jugador NO hizo Bust (puntos > 0)
            if score > 0:
                if podium_count < 3:
                    # Asignamos medalla al 1ero, 2do y 3ero
                    desc += f"{medals[podium_count]} **{user.name}**: {score} pts\n"
                    podium_count += 1
                else:
                    # Supervivientes fuera del top 3
                    desc += f"{emotes.pp} **{user.name}**: {score} pts\n"
            
            # Caso: El jugador hizo BUST (puntos == 0)
            else:
                desc += f"{emotes.pp} **{user.name}**: BUST (0 pts)\n"

        survivors = [s for s in sorted_results if s[1] > 0]
        if survivors:
            winner = discord.utils.get(self.players, id=survivors[0][0])
            desc += f"\n\n\n{emotes.happy} ¡**{winner.name}** ha ganado! {emotes.happy}"
        else:
            desc += f"\n\n\n🤡 Todos hicieron bust... nadie gana {emotes.pn}"

        embed = discord.Embed(
            title=f"🏁 Fin del Juego {emotes.kase}", 
            description=desc, 
            color=0xF2C1D1
        )


        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Flip", style=discord.ButtonStyle.primary, emoji="🎲")
    async def flip(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.get_current_player()
        if interaction.user != player:
            return await interaction.response.send_message(f"No es tu turno, espera un pokito mierda {emotes.angi}", ephemeral=True)

        card = random.choice(self.deck)
        hand = self.boards[player.id]

        if card in hand: # BUST
            self.final_scores[player.id] = 0
            await interaction.channel.send(f"💥 ¡BUST! {player.mention} sacó un {card} repetido y perdió sus puntos. {emotes.jojojo}{emotes.jojojo}{emotes.jojojo}")
            await self.stay_turn(interaction)
        else:
            hand.append(card)
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Stay", style=discord.ButtonStyle.success, emoji="✅")
    async def stay(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.get_current_player()
        if interaction.user != player:
            return await interaction.response.send_message(f"No es tu turno, espera un pokito mierda {emotes.angi}", ephemeral=True)

        self.final_scores[player.id] = sum(self.boards[player.id])
        await self.stay_turn(interaction)

class Flip7Lobby(discord.ui.View):
    def __init__(self, creador):
        super().__init__(timeout=60)
        self.creador = creador
        self.players = [creador]

    @discord.ui.button(label="Unirse", style=discord.ButtonStyle.secondary)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            return await interaction.response.send_message(f"Ya estás en la lista, ¡espera a que empiece! {emotes.angii}", ephemeral=True)
        
        self.players.append(interaction.user)
        await interaction.response.edit_message(content=f"📝 **Jugadores anotados:** {', '.join([j.name for j in self.players])}")

    @discord.ui.button(label="Iniciar Juego", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.creador:
            return await interaction.response.send_message(f"Solo quien inició el lobby puede empezar el juego {emotes.angii}", ephemeral=True)
        
        game_view = MultiFlip7View(self.players)
        await interaction.response.edit_message(content=None, embed=game_view.create_embed(), view=game_view)