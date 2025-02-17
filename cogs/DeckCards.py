import random

import nextcord
from nextcord.ext import commands

## -- DECK CARDS GAME (HIGH CARD) -- ##

suits = ['♠️', '♥️', '♦️', '♣️']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
initial_deck = [f'{rank}{suit}' for suit in suits for rank in ranks]

rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13,
               'A': 11}

deck = initial_deck.copy()
games = {}


def calculate_hand_value(hand):
    value = sum(rank_values[card[:-2]] for card in hand)
    num_aces = sum(1 for card in hand if card.startswith('A'))
    while value > 21 and num_aces:
        value -= 10
        num_aces -= 1
    return value


async def check_game_status(ctx):
    game_id = ctx.channel.id
    if game_id not in games:
        return

    all_stand = all(player["stand"] for player in games[game_id]["players"].values())
    if all_stand:
        await dealer_turn(ctx)


async def dealer_turn(ctx):
    embed = nextcord.Embed(title="🎴 Dealers Turn!", color=nextcord.Color.yellow())

    game_id = ctx.channel.id
    dealer = games[game_id]["dealer"]
    deck = games[game_id]["deck"]

    while calculate_hand_value(dealer["hand"]) < 17:
        dealer["hand"].append(deck.pop())

    dealer_value = calculate_hand_value(dealer["hand"])
    dealer_hand_str = ' '.join(dealer["hand"])
    embed.add_field(name="🤩 Dealer", value=f"💵 **Dealer's hand: {dealer_hand_str} (Value: {dealer_value})**",
                    inline=False)
    await ctx.send(embed=embed)

    await determine_winners(ctx)


async def determine_winners(ctx):
    game_id = ctx.channel.id
    dealer_value = calculate_hand_value(games[game_id]["dealer"]["hand"])

    for player, data in games[game_id]["players"].items():
        embed = nextcord.Embed(title="🏆 Game Result", color=nextcord.Color.green())
        player_value = calculate_hand_value(data["hand"])

        if player_value > 21:
            embed.add_field(name="Busts!❌", value=f"🥲 **{player.display_name} busts and loses!**", inline=False)
        elif dealer_value > 21 or player_value > dealer_value:
            embed.add_field(name=f"🤩 {player.display_name} Wins!",
                            value=f"**{player.display_name} wins with {player_value} against dealer's {dealer_value}!**",
                            inline=False)
        elif player_value < dealer_value:
            embed.add_field(name="🤩 Dealer Wins",
                            value=f"**{player.display_name} loses with {player_value} against dealer's {dealer_value}.**",
                            inline=False)
        else:
            embed.add_field(name="🤔 Ties!",
                            value=f"**{player.display_name} ties with dealer at {player_value}.**",
                            inline=False)
        await ctx.send(embed=embed)

    del games[game_id]


class DeckCards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='playcards')
    async def playcards(self, ctx, player1: nextcord.Member = None, player2: nextcord.Member = None):
        embed = nextcord.Embed(title="🃏 High Card Game", color=nextcord.Color.yellow())
        if player1 is None or player2 is None:
            embed.add_field(name="🚨 Warning", value="🎯 **Please mention two players to start the game.**", inline=False)
            await ctx.send(embed=embed)
            return

        global deck

        if len(deck) < 2:
            embed.add_field(name="🚨 Warning",
                            value="🥲 **Not enough cards in the deck to continue!** Please reset the game.",
                            inline=False)
            await ctx.send(embed=embed)
            return

        random.shuffle(deck)
        player1_card = deck.pop()
        player2_card = deck.pop()

        player1_value = rank_values[player1_card[:-2]]
        player2_value = rank_values[player2_card[:-2]]

        embed = nextcord.Embed(title="High Card Result:", color=nextcord.Color.green())
        if player1_value > player2_value:
            embed.add_field(name=f"♠️ {player1.display_name} **Wins!**",
                            value=f"🤑 {player1.display_name} **wins with {player1_card} against {player2_card}!**")
        elif player1_value < player2_value:
            embed.add_field(name=f"♣️ {player2.display_name} **Wins!**",
                            value=f"🤑 {player2.display_name} **wins with {player2_card} against {player1_card}!**")
        else:
            embed.add_field(name="🥱 Tie!", value=f"👀 **It's a tie with {player1_card} and {player2_card}!**")

        await ctx.send(embed=embed)

    @commands.command(name="resetdeck")
    async def resetdeck(self, ctx):
        embed = nextcord.Embed(title="Reset", color=nextcord.Color.red())
        global deck
        deck = initial_deck.copy()
        embed.add_field(name="🎴 Deck Reset!", value="🔂 **The deck has been reset!**")
        await ctx.send(embed=embed)

    @commands.command(name="blackjack")
    async def startblackjack(self, ctx, *players: nextcord.Member):
        embed = nextcord.Embed(title="Blackjack", color=nextcord.Color.red())

        if not players:
            embed.add_field(name="🚨 Warning!", value="🎯 **Please mention at least one player to start Blackjack.**",
                            inline=False)
            await ctx.send(embed=embed)
            return

        global deck
        if len(deck) < 2 * (len(players) + 1):
            embed.add_field(name="🚨 Warning!",
                            value="🥱 **Not enough cards in the deck to continue!** Please reset the game.",
                            inline=False)
            await ctx.send(embed=embed)
            return

        random.shuffle(deck)

        game_id = ctx.channel.id
        games[game_id] = {
            "players": {player: {"hand": [], "stand": False} for player in players},
            "dealer": {"hand": []},
            "deck": deck.copy()
        }

        # Deal initial cards
        for _ in range(2):
            for player in players:
                games[game_id]["players"][player]["hand"].append(games[game_id]["deck"].pop())
            games[game_id]["dealer"]["hand"].append(games[game_id]["deck"].pop())

        # Show dealer's hand
        dealer_hand = games[game_id]["dealer"]["hand"]
        dealer_hand_str = f"{dealer_hand[0]} ??"
        embed.add_field(name="🎴 Dealer's Hand", value=f"👀 **Dealer's hand: {dealer_hand_str}**", inline=False)
        await ctx.send(embed=embed)

        # Show players' hands
        for player in players:
            player_embed = nextcord.Embed(title=f"{player.display_name}'s Hand", color=nextcord.Color.blue())
            hand = games[game_id]["players"][player]["hand"]
            hand_str = ' '.join(hand)
            player_embed.add_field(name="🃏 Cards",
                                   value=f"🤑 **{hand_str} (Value: {calculate_hand_value(hand)})**",
                                   inline=False)
            await ctx.send(embed=player_embed)

        instructions = nextcord.Embed(title="Your Turn!", color=nextcord.Color.green())
        instructions.add_field(name="💰 Hit or Stand?",
                               value="🤩 **Use !hit to draw another card or !stand to keep your hand.**", inline=False)
        await ctx.send(embed=instructions)

    @commands.command(name="hit")
    async def hit(self, ctx):
        embed = nextcord.Embed(title="Hit", color=nextcord.Color.red())

        game_id = ctx.channel.id
        if game_id not in games:
            embed.add_field(name="🚨 Warning!",
                            value="❌ **No active Blackjack game in this channel. Start one with !blackjack.**",
                            inline=False)
            await ctx.send(embed=embed)
            return

        player = ctx.author
        if player not in games[game_id]["players"]:
            embed.add_field(name="🚨 Warning!", value="🥲 **You are not a part of this Blackjack game!**", inline=False)
            await ctx.send(embed=embed)
            return

        if games[game_id]["players"][player]["stand"]:
            embed.add_field(name="🚨 Warning!", value="😉 **You have already chosen to stand!**", inline=False)
            await ctx.send(embed=embed)
            return

        games[game_id]["players"][player]["hand"].append(games[game_id]["deck"].pop())
        hand = games[game_id]["players"][player]["hand"]
        hand_value = calculate_hand_value(hand)

        embed = nextcord.Embed(title=f"**{player.display_name}'s Turn**", color=nextcord.Color.blue())
        hand_str = ' '.join(hand)
        embed.add_field(name="🃏 Your Hand",
                        value=f"💵 **{hand_str} (Value: {hand_value})**",
                        inline=False)
        await ctx.send(embed=embed)

        if hand_value > 21:
            bust_embed = nextcord.Embed(title="Bust! 💥", color=nextcord.Color.red())
            bust_embed.add_field(name="Game Over!",
                                 value=f"💥 **{player.display_name} busts with {hand_value}**!",
                                 inline=False)
            await ctx.send(embed=bust_embed)
            games[game_id]["players"][player]["stand"] = True

        await check_game_status(ctx)

    @commands.command(name="stand")
    async def stand(self, ctx):
        embed = nextcord.Embed(title="🦢 Stand", color=nextcord.Color.blue())

        game_id = ctx.channel.id
        if game_id not in games:
            embed.add_field(name="🚨 Warning!",
                            value="❌ **No active Blackjack game in this channel. Start one with !blackjack.**",
                            inline=False)
            await ctx.send(embed=embed)
            return

        player = ctx.author
        if player not in games[game_id]["players"]:
            embed.add_field(name="🚨 Warning!", value="**❌You are not a part of this Blackjack game!**", inline=False)
            await ctx.send(embed=embed)
            return

        games[game_id]["players"][player]["stand"] = True
        embed.add_field(name="Stand", value=f"👀 **{player.display_name} stands with their current hand!**",
                        inline=False)
        await ctx.send(embed=embed)

        await check_game_status(ctx)


def setup(bot):
    bot.add_cog(DeckCards(bot))
