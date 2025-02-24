import os

import nextcord
import psycopg2
import requests
from dotenv import load_dotenv
from nextcord.ext import commands

load_dotenv("../.env")
DATABASE_URL = os.getenv("POSTGRES_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()


def get_pokemon_data(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    response = requests.get(url)

    if response.status != 200:
        return None

    data = response.json()
    return {
        "name": data["name"].capitalize(),
        "hp": data["stats"][0]["base_stat"],
        "attack": data["stats"][1]["base_stat"],
        "defense": data["stats"][2]["base_stat"],
        "speed": data["stats"][5]["base_stat"],
        "sprite": data["sprites"]["front_default"]
    }


class BattleButtons(nextcord.ui.View):
    def __init__(self, battle_manager):
        super().__init__(timeout=60)
        self.battle_manager = battle_manager

    @nextcord.ui.button(label="Attack", style=nextcord.ButtonStyle.danger)
    async def attack(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self.battle_manager.handle_attack(interaction)

    @nextcord.ui.button(label="Dodge", style=nextcord.ButtonStyle.primary)
    async def dodge(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self.battle_manager.handle_dodge(interaction)

    @nextcord.ui.button(label="Run", style=nextcord.ButtonStyle.secondary)
    async def run(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self.battle_manager.handle_run(interaction)


async def get_pokemon_stats(user_id):
    cur.execute("""
        SELECT pokemon_name, level, hp, attack, defense, speed, sprite_url
        FROM pokemons WHERE user_id = %s
    """, (user_id,))
    return cur.fetchone()


def calculate_damage(attacker_stats, defender_stats, is_dodge):
    base_damage = (attacker_stats[3] * 0.5) - (defender_stats[4] * 0.2)
    if is_dodge:
        base_damage *= 0.5
    return max(int(base_damage), 1)


class BattleManager:
    def __init__(self, ctx, player1, player2):
        self.ctx = ctx
        self.player1 = player1
        self.player2 = player2
        self.current_turn = player1
        self.battle_active = True
        self.dodge_cooldown = {}

    async def handle_attack(self, interaction):
        if not self.battle_active or interaction.user.id != self.current_turn.id:
            return

        attacker_stats = await get_pokemon_stats(self.current_turn.id)
        defender = self.player2 if self.current_turn == self.player1 else self.player1
        defender_stats = await get_pokemon_stats(defender.id)

        is_dodge = defender.id in self.dodge_cooldown and self.dodge_cooldown[defender.id]
        damage = calculate_damage(attacker_stats, defender_stats, is_dodge)

        # Update defender's HP in database
        new_hp = defender_stats[2] - damage
        cur.execute("""
            UPDATE pokemons SET hp = %s WHERE user_id = %s
        """, (new_hp, defender.id))
        conn.commit()

        # Create battle update embed
        embed = nextcord.Embed(
            title="Battle Update!",
            description=f"{self.current_turn.mention}'s {attacker_stats[0]} attacked {defender.mention}'s {defender_stats[0]}!",
            color=0xFF0000
        )
        embed.add_field(name="Damage Dealt", value=str(damage))
        embed.add_field(name=f"{defender_stats[0]}'s HP", value=f"{new_hp}/{defender_stats[2]}")

        if new_hp <= 0:
            self.battle_active = False
            embed.add_field(name="Battle Result", value=f"{self.current_turn.mention} wins!", inline=False)
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            self.current_turn = defender
            self.dodge_cooldown[defender.id] = False
            await interaction.response.edit_message(embed=embed, view=BattleButtons(self))

    async def handle_dodge(self, interaction):
        if not self.battle_active or interaction.user.id != self.current_turn.id:
            return

        if self.current_turn.id in self.dodge_cooldown and self.dodge_cooldown[self.current_turn.id]:
            await interaction.response.send_message("You can't dodge twice in a row!", ephemeral=True)
            return

        self.dodge_cooldown[self.current_turn.id] = True
        pokemon_stats = await get_pokemon_stats(self.current_turn.id)

        embed = nextcord.Embed(
            title="Dodge!",
            description=f"{self.current_turn.mention}'s {pokemon_stats[0]} prepares to dodge the next attack!",
            color=0x00FF00
        )

        self.current_turn = self.player2 if self.current_turn == self.player1 else self.player1
        await interaction.response.edit_message(embed=embed, view=BattleButtons(self))

    async def handle_run(self, interaction):
        if not self.battle_active or interaction.user.id != self.current_turn.id:
            return

        self.battle_active = False
        embed = nextcord.Embed(
            title="Battle Ended",
            description=f"{self.current_turn.mention} has fled from the battle!",
            color=0x808080
        )
        await interaction.response.edit_message(embed=embed, view=None)


class PokemonBattle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = {}

    @commands.command(name="choose_pokemon", help="Choose your Pokemon!")
    async def choose_pokemon(self, ctx, pokemon_name: str):
        user_id = ctx.author.id
        pokemon = get_pokemon_data(pokemon_name)

        if not pokemon:
            await ctx.send(f"☹️ {ctx.author.mention} **Invalid Pokemon name! Try again.**", ephemeral=True)
            return

        cur.execute("""
                SELECT * FROM pokemons WHERE user_id = %s
            """, (user_id,))
        existing_pokemon = cur.fetchone()

        if existing_pokemon:
            await ctx.send(
                f"🤦🏻 {ctx.author.mention} **You already have a Pokemon!** Use `!release_pokemon` to choose a new one.")
            return

        cur.execute("""
                INSERT INTO pokemons (user_id, pokemon_name, level, hp, attack, defense, speed, sprite_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, pokemon["name"], 1, pokemon["hp"], pokemon["attack"], pokemon["defense"], pokemon["speed"],
                  pokemon["sprite"]))
        conn.commit()

        embed = nextcord.Embed(
            title="Pokemon Chosen!",
            description=f"{ctx.author.mention} You selected **{pokemon['name']}**!",
            color=0x00FF00
        )
        embed.set_thumbnail(url=pokemon["sprite"])

        await ctx.send(embed=embed)

    @commands.command(name="battle", help="Challenge another user to a Pokemon battle!")
    async def battle(self, ctx, opponent: nextcord.Member):
        if ctx.author.id == opponent.id:
            await ctx.send("You can't battle yourself!")
            return

        if ctx.author.id in self.active_battles or opponent.id in self.active_battles:
            await ctx.send("One of the players is already in a battle!")
            return

        # Check if both players have Pokémon
        cur.execute("SELECT * FROM pokemons WHERE user_id IN (%s, %s)", (ctx.author.id, opponent.id))
        pokemon = cur.fetchall()
        if len(pokemon) != 2:
            await ctx.send("Both players must have a Pokemon to battle!")
            return

        self.active_battles[ctx.author.id] = True
        self.active_battles[opponent.id] = True

        # Create battle embed
        embed = nextcord.Embed(
            title="Pokemon Battle!",
            description=f"{ctx.author.mention} vs {opponent.mention}",
            color=0xFF00FF
        )

        battle_manager = BattleManager(ctx, ctx.author, opponent)
        view = BattleButtons(battle_manager)

        await ctx.send(embed=embed, view=view)

    @commands.command(name="release_pokemon", help="Release your current Pokemon")
    async def release_pokemon(self, ctx):
        cur.execute("DELETE FROM pokemons WHERE user_id = %s", (ctx.author.id,))
        conn.commit()
        await ctx.send(f"✅ {ctx.author.mention} Your Pokemon has been released!")


def setup(bot):
    bot.add_cog(PokemonBattle(bot))
