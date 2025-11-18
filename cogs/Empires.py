import asyncio
import json
import os
import random
from typing import Dict, Any
import aiofiles
import nextcord
from nextcord.ext import commands

VALID_CONTINENTS = ["Europe", "Asia", "Africa", "Oceania", "Antarctica", "Americas"]

HAPPINESS_EMOJIS = {
    "very_happy": "😄",  # > 150 happiness
    "happy": "🙂",  # 100-150 happiness
    "neutral": "😐",  # 50-100 happiness
    "sad": "😟",  # 0-50 happiness
    "angry": "😠"  # < 0 happiness
}

STARTING_RESOURCES = {
    "population": 50000,
    "gold": 1000,
    "food": 10000,
    "tools": 50,
    "soldiers": 100,
    "morale": 300,
    "happiness": 100,
    "land": 200
}

REVOLUTION_THRESHOLD = 0

BUILDINGS = {
    "farm": {"gold": 200, "tools": 10},
    "barrack": {"gold": 100, "tools": 20},
    "house": {"gold": 100, "tools": 5},
    "municipality": {"gold": 100, "tools": 5},
    "castle": {"gold": 1000, "tools": 50},
    "school": {"gold": 200, "tools": 10}
}


def _ensure_data_directory() -> None:
    """Ensure the data directory exists"""
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'json'), exist_ok=True)


def create_embed(title: str, description: str, color: nextcord.Color) -> nextcord.Embed:
    """Create a standardized embed"""
    return nextcord.Embed(title=title, description=description, color=color)


def get_happiness_emoji(happiness: int) -> str:
    """Return appropriate emoji based on happiness level"""
    if happiness > 150:
        return HAPPINESS_EMOJIS["very_happy"]
    elif happiness > 100:
        return HAPPINESS_EMOJIS["happy"]
    elif happiness > 50:
        return HAPPINESS_EMOJIS["neutral"]
    elif happiness > 0:
        return HAPPINESS_EMOJIS["sad"]
    else:
        return HAPPINESS_EMOJIS["angry"]


class Empire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.empires: Dict[str, Any] = {}
        self.data_file = os.path.join(os.path.dirname(__file__), '..', 'json', 'empires.json')
        self.events_file = os.path.join(os.path.dirname(__file__), '..', 'json', 'empire_event.json')
        _ensure_data_directory()
        self.load_empires()
        self.load_events()

    async def save_empires(self) -> None:
        """Save empires data to JSON file asynchronously"""
        try:
            async with aiofiles.open(self.data_file, 'w') as f:
                await f.write(json.dumps(self.empires, indent=4))
        except Exception as e:
            print(f"Error saving empires: {e}")

    def load_empires(self) -> None:
        """Load empire data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.empires = json.load(f)
            else:
                print("Empires file not found, creating empty dictionary")
                self.empires = {}
        except Exception as e:
            print(f"Error loading empires: {e}")
            self.empires = {}

    def load_events(self) -> None:
        """Load Empire events from JSON file"""
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r') as f:
                    self.events = json.load(f)
            else:
                print("Events file not found")
                self.events = {"events": []}
        except Exception as e:
            print(f"Error loading Empire events: {e}")
            self.events = {"events": []}

    async def save_empires(self) -> None:
        """Save empires data to JSON file asynchronously"""
        try:
            async with aiofiles.open(self.data_file, 'w') as f:
                await f.write(json.dumps(self.empires, indent=4))
        except Exception as e:
            print(f"Error saving empires: {e}")

    def update_resources(self, user_id: str, changes: Dict[str, int]) -> None:
        """Safely update empire resources"""
        for resource, amount in changes.items():
            if resource in self.empires[user_id]["resources"]:
                self.empires[user_id]["resources"][resource] += amount
                self.empires[user_id]["resources"][resource] = max(0, self.empires[user_id]["resources"][resource])

    async def check_revolution(self, interaction, user_id: str) -> bool:
        """Check if a revolution should occur and handle it"""
        empire = self.empires[user_id]
        happiness = empire["resources"]["happiness"]

        if happiness <= REVOLUTION_THRESHOLD:
            revolution_embed = nextcord.Embed(
                title="⚠️ Revolution Imminent!",
                description=f'Your people are revolting! ({happiness} happiness)\n'
                            'What will you do?\n'
                            'React with:\n'
                            '🛡️ - Defend your empire (-500 gold, -50 soldiers)\n'
                            '👑 - Surrender and start anew',
                color=nextcord.Color.red()
            )
            message = await interaction.response.send_message(embed=revolution_embed)
            await message.add_reaction("🛡️")
            await message.add_reaction("👑")

            def check(reaction, user):
                return user.id == interaction.author.id and str(reaction.emoji) in ["🛡️", "👑"]

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

                if str(reaction.emoji) == "🛡️":
                    if empire["resources"]["gold"] >= 500 and empire["resources"]["soldiers"] >= 50:
                        empire["resources"]["gold"] -= 500
                        empire["resources"]["soldiers"] -= 50
                        empire["resources"]["happiness"] += 50
                        await self.save_empires()
                        await interaction.response.send_message("👑 You successfully defended against the revolution, but at a great cost!")
                        return False
                    else:
                        await interaction.response.send_message("❌ You don't have enough resources to defend!")
                        return True
                else:
                    return True

            except TimeoutError:
                await interaction.response.send_message("⏰ Time's up! The revolution succeeds!")
                return True

        return False

    @nextcord.slash_command(name="setempire", description="Set your own empire and have fun!")
    async def setempire(self, interaction, empire_name: str, continent: str):
        user_id = str(interaction.author.id)
        if user_id in self.empires:
            await interaction.response.send_message("⚠️ **You already have an empire!** Use `!statempire` to **check its status.**")
            return

        if continent.capitalize() not in VALID_CONTINENTS:
            await interaction.response.send_message(f"❌ **Invalid Continent!** Choose from: {', '.join(VALID_CONTINENTS)}.")
            return

        self.empires[user_id] = {
            "name": empire_name,
            "continent": continent.capitalize(),
            "resources": STARTING_RESOURCES.copy(),
            "farming": False
        }

        await self.save_empires()

        embed = create_embed(
            f"🏰 **Empire Created:** {empire_name}",
            f"🌎 **Located in {continent.capitalize()}**\n"
            f"💰 Gold: {STARTING_RESOURCES['gold']}\n"
            f"🥪 Food: {STARTING_RESOURCES['food']}\n"
            f"🤰🏼 Population: {STARTING_RESOURCES['population']}\n"
            f"⚔️ Soldiers: {STARTING_RESOURCES['soldiers']}",
            nextcord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(2)
        await interaction.response.send_message(
            f"👀 {interaction.author.mention} **Do you know you can type:** `!empirehelp` for more Empire related commands?")

    @nextcord.slash_command(name="statempire", description="Shows the stats of your empire!")
    async def stat_empire(self, interaction):
        """Check your empire's stats with happiness indicator"""
        user_id = str(interaction.author.id)
        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        empire = self.empires[user_id]
        resources = empire["resources"]
        happiness = resources["happiness"]
        happiness_emoji = get_happiness_emoji(happiness)

        embed = nextcord.Embed(
            title=f"🏰 {empire['name']} (🌎 {empire['continent']})",
            description=f"💰 Gold: {resources['gold']}\n"
                        f"🥪 Food: {resources['food']}\n"
                        f"🤰🏼 Population: {resources['population']}\n"
                        f"🛠️ Tools: {resources['tools']}\n"
                        f"⚔️ Soldiers: {resources['soldiers']}\n"
                        f"🪽 Morale: {resources['morale']}\n"
                        f"People's Happiness: {happiness} {happiness_emoji}",
            color=nextcord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="empirehelp", description="Show sub-commands for the Empire command!")
    async def empire_help(self, interaction):
        embed = nextcord.Embed(
            title="🏰 Empire Commands",
            description="**List of available sub-commands for the Empire!🛠️**",
            color=nextcord.Color.gold()
        )

        embed.add_field(name="!rename_empire", value="✍🏼 **Rename your Empire.** Usage: `!rename_empire <name>`",
                        inline=True)
        embed.add_field(name="!farm", value="🌾 **Farm food to feed people and workers in your Empire!**", inline=True)
        embed.add_field(name="!harvest", value="🧑🏻‍🌾 **Harvest your crops and food!**", inline=True)
        embed.add_field(name="!trade",
                        value="💹 **Trade your gold, food and tools to someones else Empire!** Usage: `!trade <resources> <amount> @user`",
                        inline=True)
        embed.add_field(name="!build",
                        value="🛠️ **Build more structures into your Empire!** Usage: `!build <structure>`", inline=True)
        embed.add_field(name="!expand", value="🗺️ **Expand your empire and grow more acres!**", inline=True)
        embed.add_field(name="!tax", value="💳 **Tax your people and get gold.** Usage: `!tax 5`", inline=True)
        embed.add_field(name="!attack", value="⚔️ **Attack another users Empire!**. Usage: `!attack @user`",
                        inline=True)
        embed.add_field(name="!event", value="👀 **Trigger a Random Event in your Empire!**", inline=True)
        embed.add_field(name="!disband", value="💔 **Collapse and Disband your own Empire...**", inline=True)
        embed.add_field(name="!minegold", value="🪙 **Mine more gold for your Empire!**", inline=True)
        embed.add_field(name="!treaty", value="🕊️ **Sign a peace treaty to your opponent.** Usage: `!treaty @user`",
                        inline=True)
        embed.add_field(name="!alliance",
                        value="🤝 **Form an alliance between your Empire and someone else!** Usage: `!alliance @user`",
                        inline=True)
        embed.add_field(name="!inviteempire", value="📩 **Invite a user to your empire!** Usage: `!inviteempire @user`",
                        inline=True)
        embed.add_field(name="!joinempire",
                        value="🎯 **Join and accept someones empire invite!** Usage: `!joinempire <name>`", inline=True)

        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="rename_empire", description="Rename your empire!")
    async def rename(self, interaction: nextcord.Interaction, name: str):
        """
        Rename your empire!
        """
        user_id = str(interaction.author.id)
        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        self.empires[user_id]["name"] = name
        await self.save_empires()

        await interaction.response.send_message(f"🏰 **{interaction.author.mention} Has Renamed their Empire to:** {name}")

    @nextcord.slash_command(name="farm", description="Farm foods and crops for your empire!")
    async def farm(self, interaction: nextcord.Interaction):
        """
        Start farming to produce food!
        """
        user_id = str(interaction.author.id)
        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        if self.empires[user_id]["farming"]:
            await interaction.response.send_message("🌱 **Your fields are already growing crops!** Wait until the **harvest.**")
            return

        self.empires[user_id]["farming"] = True
        await self.save_empires()
        await interaction.response.send_message(f"🌾 **{interaction.author.mention} You started farming!** Use `!harvest` after some time.")

    @nextcord.slash_command(name="harvest", description="Harvest your food and crops for your villagers!")
    async def harvest(self, interaction):
        """
        Harvest crops if farming is active.
        """
        user_id = str(interaction.author.id)
        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        if not self.empires[user_id]["farming"]:
            await interaction.response.send_message("🌱 **Your farms are empty!** Use `!farm` first.")
            return

        food_gained = random.randint(100, 300)
        self.empires[user_id]["resources"]["food"] += food_gained
        self.empires[user_id]["farming"] = False
        await self.save_empires()

        await interaction.response.send_message(
            f"🌾 You harvested **{food_gained} food!** Your **storage** is now `{self.empires[user_id]['resources']['food']}`.")

    @nextcord.slash_command(name="build", description="Build houses, buildings, and maybe more!")
    async def build(self, interaction, structure: str):
        """
        Construct buildings like farms, barracks, or houses.
        """
        user_id = str(interaction.author.id)
        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        structure = structure.lower()
        if structure not in BUILDINGS:
            await interaction.response.send_message(f"🏗️ **Invalid building!** Choose from: {','.join(BUILDINGS.key())}.")
            return

        cost = BUILDINGS[structure]
        resources = self.empires[user_id]["resources"]

        if resources["gold"] < cost["gold"] or resources["tools"] < cost["tools"]:
            await interaction.response.send_message("❌ **Not enough resources to build this structure!**")
            return

        resources["gold"] -= cost["gold"]
        resources["tools"] -= cost["tools"]
        await self.save_empires()

        await interaction.response.send_message(f"🏗️ {interaction.author.mention} You built a **{structure}!** Resources updated.")

    @nextcord.slash_command(name="trade", description="Trade to another users empire!")
    async def trade(self, interaction, resource: str, amount: int, member: nextcord.Member):
        """
        Trade users with resources (only gold, food & tools)
        """
        sender_id = str(interaction.author.id)
        receiver_id = str(member.id)
        resources = self.empires[sender_id]["resources"]
        if sender_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        if receiver_id not in self.empires:
            await interaction.response.send_message("❌ **The recipient doesn't have an Empire!**")
            return

        if resource not in resources["gold", "food", "tools"]:
            await interaction.response.send_message(f"❌ **{interaction.author.mention} You have invalid resource!** Available: **gold, food, tools**")
            return

        if amount <= 0:
            await interaction.response.send_message(f"⚠️ **{interaction.author.mention} Your amount must be greater than zero!**")
            return

        if sender_id["resources"].get(resource, 0) < amount:
            await interaction.response.send_message(f"❌ **{interaction.author.mention} You don't have enough {resource} to trade!**")
            return

        self.empires[sender_id]["resources"][resource] -= amount
        self.empires[receiver_id]["resources"][resource] = self.empires[receiver_id]["resources"].get(resource,
                                                                                                      0) + amount
        await self.save_empires()

        await interaction.response.send_message(f"✅ **Trade Successful!** {interaction.author.name} sent {amount} {resource} to {member.name}!")

    @nextcord.slash_command(name="minegold", description="Mine gold to gather more resources!")
    async def minegold(self, interaction):
        """
        Mine for a chance of gold!
        """
        user_id = interaction.author.id
        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        gold_mined = 20

        user_id["resources"]["gold"] = user_id["resources"].get("gold", 0) + gold_mined
        await self.save_empires()

        await interaction.response.send_message(f"⛏️ **{interaction.author.mention} mined {gold_mined} gold!**")

    @nextcord.slash_command(name="treaty", description="Sign a peace treaty between two warring empires!")
    async def treaty(self, interaction, member: nextcord.Member):
        """
        Sign a peace treaty to stop a war.
        Usage: !treaty @user
        """
        sender_id = str(interaction.author.id)
        receiver_id = str(member.id)

        if sender_id not in self.empires or receiver_id not in self.empires:
            await interaction.response.send_message(f"⚠️ **Both** {sender_id} **and** {receiver_id} **MUST have empires to sign a treaty!**")
            return

        if receiver_id in self.empires[sender_id].get("enemies", []):
            self.empires[sender_id]["enemies"].remove(receiver_id)
            self.empires[receiver_id]["enemies"].remove(sender_id)
            await self.save_empires()
            await interaction.response.send_message(f"🕊️ **Peace Treaty signed between {interaction.author.name} and {member.name}**")
        else:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **You are not at war with {member.name} Empire!**")

    @nextcord.slash_command(name="alliance", description="Form a alliance towards a users Empire!")
    async def alliance(self, interaction, member: nextcord.Member):
        """
        Form an alliance with another empire!
        """
        sender_id = str(interaction.author.id)
        receiver_id = str(member.id)

        if sender_id not in self.empires or receiver_id not in self.empires:
            await interaction.response.send_message(f"⚠️ **Both** {sender_id} **and** {receiver_id} **MUST have empires to form an alliance!**")
            return

        if receiver_id in self.empires[sender_id].get("allies", []):
            await interaction.response.send_message("❌ **You are already allied with this empire!**")
            return

        self.empires[sender_id].setdefault("allies", []).append(receiver_id)
        self.empires[receiver_id].setdefault("allies", []).append(sender_id)
        await self.save_empires()

        await interaction.response.send_message(f"✅ **{interaction.author.mention} and {member.name} have formed an alliance!**")

    @nextcord.slash_command(name="empiremarket", description="Market of your empire!")
    async def empire_market(self, interaction):
        """
        Manage markets into your own Empire!
        """

    @nextcord.slash_command(name="expand", description="Expand your empire!")
    async def expand(self, interaction):
        """
        Expand empire land by spending gold.
        """
        user_id = str(interaction.author.id)
        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        cost = 500
        resources = self.empires[user_id]["resources"]

        if resources["gold"] < cost:
            await interaction.response.send_message(f"❌ **{interaction.author.mention} You don't have enough gold to expand!**")
            return

        resources["gold"] -= cost
        resources["land"] += 50
        await self.save_empires()

        await interaction.response.send_message(
            f"🌄 **{interaction.author.mention} has expanded their land!** Its land is now `{resources['land']} acres`.")

    @nextcord.slash_command(name="recruit", description="Recruit soldiers for your empire!")
    async def recruit(self, interaction, amount: int):
        """
        Recruit soldiers using gold.
        """
        user_id = str(interaction.author.id)

        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        cost_per_soldier = 100
        total_cost = amount * cost_per_soldier
        resources = self.empires[user_id]["resources"]

        if resources["gold"] < total_cost:
            await interaction.response.send_message(f"❌ **{interaction.author.mention} You don't have enough gold to recruit!**")
            return

        resources["gold"] -= total_cost
        resources["soldiers"] += amount
        await self.save_empires()

        await interaction.response.send_message(
            f"🛡️ **{interaction.author.mention} recruited {amount} soldiers!** His army now has: `{resources['soldiers']}` soldiers.")

    @nextcord.slash_command(name="tax", description="Tax the people of your empire!")
    async def tax(self, interaction, amount: int):
        """Modified tax command to affect happiness"""
        user_id = str(interaction.author.id)

        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        if amount < 1 or amount > 100:
            await interaction.response.send_message(f"❌ **{interaction.author.mention} Tax rate must be between 1% and 100%!**")
            return

        resources = self.empires[user_id]["resources"]
        gold_gained = (resources["gold"] * amount) // 100
        happiness_loss = amount // 2  # Higher tax = lower happiness

        changes = {
            "gold": gold_gained,
            "happiness": -happiness_loss,
            "morale": -happiness_loss
        }

        self.update_resources(user_id, changes)
        await self.save_empires()

        # Check for revolution after taxing
        if await self.check_revolution(interaction, user_id):
            del self.empires[user_id]
            await self.save_empires()
            await interaction.response.send_message("👋 Your empire has fallen to revolution! Use `!setempire` to start anew.")
            return

        await interaction.response.send_message(f"💰 **{interaction.author.mention} collected {gold_gained} gold in taxes!**\n"
                       f"Happiness decreased by {happiness_loss} points.")

    @nextcord.slash_command(name="disband", description="Disband your empire!")
    async def disband(self, interaction):
        """
        Disband your empire!
        """
        user_id = str(interaction.author.id)
        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        self.empires[user_id]["resources"]["soldiers"] = 0
        await self.save_empires()

        await interaction.response.send_message(
            f"👋 **{interaction.author.mention} has disbanded his empire!** His army now has: `{self.empires[user_id]['resources']['soldiers']}` soldiers.")

    @nextcord.slash_command(name="event", description="Trigger a random event in your empire!")
    async def event(self, interaction):
        user_id = str(interaction.author.id)
        if user_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        event = random.choice(self.events["events"])
        changes = event.get("changes") or event.get("change", {})

        # Update resources with the changes
        self.update_resources(user_id, changes)
        await self.save_empires()

        await interaction.response.send_message(f"📜 **Empire Event:** {event['message']}")

    @nextcord.slash_command(name="attack", description="Attack another users empire!")
    async def attack(self, interaction, target: nextcord.Member):
        """
        Attack another empire and steal gold!
        """
        attacker_id = str(interaction.author.id)
        target_id = str(target.id)

        if attacker_id not in self.empires or target_id not in self.empires:
            await interaction.response.send_message("⚠️ **Both players MUST have an empire to fight!** Use `!setempire` first.")
            return

        attacker_soldiers = self.empires[attacker_id]["resources"]["soldiers"]
        target_soldiers = self.empires[target_id]["resources"]["soldiers"]

        if attacker_soldiers <= 0:
            await interaction.response.send_message("❌ You have no soldiers to attack!")
            return

        if target_soldiers <= 0:
            await interaction.response.send_message(f"🥂 **{target.mention} had no defense!** You stole 200 gold!")
            self.empires[attacker_id]["resources"]["gold"] += 200
            await self.save_empires()
            return

        attack_power = random.randint(0, attacker_soldiers)
        defense_power = random.randint(0, target_soldiers)

        if attack_power > defense_power:
            stolen_gold = random.randint(100, 300)
            self.empires[attacker_id]["resources"]["gold"] += stolen_gold
            self.empires[target_id]["resources"]["gold"] -= stolen_gold
            await self.save_empires()

            await interaction.response.send_message(
                f"⚔️ **Battle Result:** {interaction.author.mention} won and stole {stolen_gold} **gold** from {target.mention}!🤺")
        else:
            await interaction.response.send_message(f"⚔️ **Battle Result:** {target.mention} defended **successfully!** No gold was stolen.")

    @nextcord.slash_command(name="inviteempire", description="Invite users to your empire!")
    async def invite_empire(self, interaction, user: nextcord.Member):
        """
        Invite another player to your empire!
        """
        owner_id = str(interaction.author.id)
        target_id = str(user.id)

        if owner_id not in self.empires:
            await interaction.response.send_message("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        if target_id in self.empires:
            await interaction.response.send_message("⚠️ **That player already has their own empire!**")
            return

        empire_name = self.empires[owner_id]["name"]
        await interaction.response.send_message(
            f"📜 {user.mention}, you have been invited to join **{empire_name}**! Use `!joinempire {empire_name}` to accept!")

    @nextcord.slash_command(name="joinempire", description="Join a users empire!")
    async def join_empire(self, interaction, empire_name: str):
        """
        Join an existing empire!
        """
        user_id = str(interaction.author.id)

        if user_id in self.empires:
            await interaction.response.send_message("❌ **You already have an empire!** Use `!statempire` to check it.")
            return

        for owner_id, empire in self.empires.items():
            if empire["name"].lower() == empire_name.lower():
                self.empires[user_id] = empire
                await self.save_empires()
                await interaction.response.send_message(f"🥂 {interaction.author.mention} has joined **{empire_name}**!")
                return

        await interaction.response.send_message("⚠️ That **Empire** does not exist!")


def setup(bot):
    bot.add_cog(Empire(bot))
