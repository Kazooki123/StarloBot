import nextcord
from nextcord.ext import commands
import json
import random
import aiofiles
import os
from typing import Dict, Any

VALID_CONTINENTS = ["Europe", "Asia", "Africa", "Oceania", "Antarctica", "Americas"]

HAPPINESS_EMOJIS = {
    "very_happy": "😄",  # > 150 happiness
    "happy": "🙂",      # 100-150 happiness
    "neutral": "😐",    # 50-100 happiness
    "sad": "😟",        # 0-50 happiness
    "angry": "😠"       # < 0 happiness
}

STARTING_RESOURCES = {
    "population": 50000,
    "gold": 1000,
    "food": 500,
    "tools": 50,
    "soldiers": 100,
    "morale": 300,
    "happiness": 100,
    "land": 200
}

REVOLUTION_THRESHOLD = 0 

BUILDINGS = {
    "farm": {"gold": 300, "tools": 10},
    "barracks": {"gold": 500, "tools": 20},
    "house": {"gold": 200, "tools": 5},
    "municipality": {"gold": 100, "tools": 5},
    "castle": {"gold": 1000, "tools": 50},
    "schools": {"gold": 200, "tools": 10}
}

class Empire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.empires: Dict[str, Any] = {}
        self.data_file = os.path.join('..', 'json', 'empires.json')
        self.events_file = os.path.join('..', 'json', 'empire_events.json')
        self._ensure_data_directory()
        self.load_empires()
        self.load_events()
        
    def _ensure_data_directory(self) -> None:
        """Ensure the data directory exists"""
        os.makedirs('json', exist_ok=True)

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
            if os.path.exists(self.events_file):
                with open(self.data_file, 'r') as f:
                    self.empires = json.load(f)
        except Exception as e:
            print(f"Error loading empires: {e}")
            self.empires = {}
                
    def load_events(self) -> None:
        """Load Empire events from JSON file"""
        try:
            with open(self.data_file, "r") as f:
                self.empires = json.load(f)
        except Exception as e:
            print(f"Error loading Empire events: {e}")

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

    def create_embed(self, title: str, description: str, color: nextcord.Color) -> nextcord.Embed:
        """Create a standardized embed"""
        return nextcord.Embed(title=title, description=description, color=color)
    
    def get_happiness_emoji(self, happiness: int) -> str:
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

    async def check_revolution(self, ctx, user_id: str) -> bool:
        """Check if a revolution should occur and handle it"""
        empire = self.empires[user_id]
        happiness = empire["resources"]["happiness"]
        
        if happiness <= REVOLUTION_THRESHOLD:
            revolution_embed = nextcord.Embed(
                title="⚠️ Revolution Imminent!",
                description=f"Your people are revolting! ({happiness} happiness)\n"
                           "What will you do?\n"
                           "React with:\n"
                           "🛡️ - Defend your empire (-500 gold, -50 soldiers)\n"
                           "👑 - Surrender and start anew",
                color=nextcord.Color.red()
            )
            message = await ctx.send(embed=revolution_embed)
            await message.add_reaction("🛡️")
            await message.add_reaction("👑")
            
            def check(reaction, user):
                return user.id == ctx.author.id and str(reaction.emoji) in ["🛡️", "👑"]
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "🛡️":
                    if empire["resources"]["gold"] >= 500 and empire["resources"]["soldiers"] >= 50:
                        empire["resources"]["gold"] -= 500
                        empire["resources"]["soldiers"] -= 50
                        empire["resources"]["happiness"] += 50
                        self.save_empires()
                        await ctx.send("👑 You successfully defended against the revolution, but at a great cost!")
                        return False
                    else:
                        await ctx.send("❌ You don't have enough resources to defend!")
                        return True
                else:
                    return True
                    
            except TimeoutError:
                await ctx.send("⏰ Time's up! The revolution succeeds!")
                return True
                
        return False

    @commands.command(name="setempire", help="Set your own empire and have fun!")
    async def setempire(self, ctx, empire_name: str, continent: str):
        user_id = str(ctx.author.id)
        if user_id in self.empires:
            await ctx.send("⚠️ **You already have an empire!** Use `!statempire` to **check its status.**")
            return
        
        if continent.capitalize() not in VALID_CONTINENTS:
            await ctx.send(f"❌ **Invalid Continent!** Choose from: {', '.join(VALID_CONTINENTS)}.")
            return
        
        self.empires[user_id] = {
            "name": empire_name,
            "continent": continent.capitalize(),
            "resources": STARTING_RESOURCES.copy(),
            "farming": False
        }
        
        await self.save_empires()
        
        embed = self.create_embed(
            f"🏰 **Empire Created:** {empire_name}",
            f"🌎 **Located in {continent.capitalize()}**\n"
            f"💰 Gold: {STARTING_RESOURCES['gold']}\n"
            f"🥪 Food: {STARTING_RESOURCES['food']}\n"
            f"🤰🏼 Population: {STARTING_RESOURCES['population']}\n"
            f"⚔️ Soldiers: {STARTING_RESOURCES['soldiers']}",
            nextcord.Color.green()
        )
        await ctx.send(embed=embed)
        
    @commands.command(name="statempire", help="Shows the stats of your empire!")
    async def statempire(self, ctx):
        """Check your empire's stats with happiness indicator"""
        user_id = str(ctx.author.id)
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        empire = self.empires[user_id]
        resources = empire["resources"]
        happiness = resources["happiness"]
        happiness_emoji = self.get_happiness_emoji(happiness)
        
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
        await ctx.send(embed=embed)
        
    @commands.command(name="empirehelp", help="Show sub-commands for the Empire command!")
    async def empirehelp(self, ctx):
        embed = nextcord.Embed(
            title="🏰 Empire Commands",
            description="**List of available sub-commands for the Empire!🛠️**",
            color=nextcord.Color.gold()
        )
        
        embed.add_field(name="!rename_empire", value="✍🏼 **Rename your Empire.** Usage: `!rename_empire <name>`", inline=True)
        embed.add_field(name="!farm", value="🌾 **Farm food to feed people and workers in your Empire!**", inline=True)
        embed.add_field(name="!harvest", value="🧑🏻‍🌾 **Harvest your crops and food!**", inline=True)
        embed.add_field(name="!trade", value="💹 **Trade your gold, food and tools to someones else Empire!** Usage: `!trade <resources> <amount> @user`", inline=True)
        embed.add_field(name="!build", value="🛠️ **Build more structures into your Empire!** Usage: `!build <structure>`", inline=True)
        embed.add_field(name="!expand", value="🗺️ **Expand your empire and grow more acres!**", inline=True)
        embed.add_field(name="!tax", value="💳 **Tax your people and get gold.** Usage: `!tax 5`", inline=True)
        embed.add_field(name="!attack", value="⚔️ **Attack another users Empire!**. Usage: `!attack @user`", inline=True)
        embed.add_field(name="!event", value="👀 **Trigger a Random Event in your Empire!**", inline=True)
        embed.add_field(name="!disband", value="💔 **Collapse and Disband your own Empire...**", inline=True)
        embed.add_field(name="!inviteempire", value="📩 **Invite a user to your empire!** Usage: `!inviteempire @user`", inline=True)
        embed.add_field(name="!joinempire", value="🎯 **Join and accept someones empire invite!** Usage: `!joinempire <name>`", inline=True)
        
        await ctx.send(embed=embed)
        
    @commands.command(name="rename_empire", help="Rename your empire!")
    async def rename(self, ctx, name: str):
        """
        Rename your empire!
        """
        user_id = str(ctx.author.id)
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        self.empires[user_id]["name"] = name
        await self.save_empires()
        
        await ctx.send(f"🏰 **{ctx.author.mention} Has Renamed their Empire to:** {name}")
        
    @commands.command(name="farm", help="Farm foods and crops for your empire!")
    async def farm(self, ctx):
        """
        Start farming to produce food!
        """
        user_id = str(ctx.author.id)
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        if self.empires[user_id]["farming"]:
            await ctx.send("🌱 **Your fields are already growing crops!** Wait until the **harvest.**")
            return
        
        self.empires[user_id]["farming"] = True
        await self.save_empires()
        await ctx.send("🌾 **You started farming!** Use `!harvest` after some time.")
        
    @commands.command(name="harvest", help="Harvest your food and crops for your villagers!")
    async def harvest(self, ctx):
        """
        Harvest crops if farming is active.
        """
        user_id = str(ctx.author.id)
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        if not self.empires[user_id]["farming"]:
            await ctx.send("🌱 **Your farms are empty!** Use `!farm` first.")
            return
        
        food_gained = random.randint(100, 300)
        self.empires[user_id]["resources"]["food"] += food_gained
        self.empires[user_id]["farming"] = False
        await self.save_empires()
        
        await ctx.send(f"🌾 You harvested **{food_gained} food!** Your **storage** is now `{self.empires[user_id]['resources']['food']}`.")
        
    @commands.command(name="build", help="Build houses, buildings, and maybe more!")
    async def build(self, ctx, structure: str):
        """
        Construct buildings like farms, barracks, or houses.
        """
        user_id = str(ctx.author.id)
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        structure = structure.lower()
        if structure not in BUILDINGS:
            await ctx.send(f"🏗️ **Invalid building!** Choose from: {','.join(BUILDINGS.key())}.")
            return
        
        cost = BUILDINGS[structure]
        resources = self.empires[user_id]["resources"]
        
        if resources["gold"] < cost["gold"] or resources["tools"] < cost["tools"]:
            await ctx.send("❌ **Not enough resources to build this structure!**")
            return
        
        resources["gold"] -= cost["gold"]
        resources["tools"] -= cost["tools"]
        await self.save_empires()
        
        await ctx.send(f"🏗️ {ctx.author.mention} You built a **{structure}!** Resources updated.")
        
    @commands.command(name="trade", help="Trade to another users empire!")
    async def trade(self, ctx, resources: str, amount: int, user: nextcord.Member):
        """
        Trade users with resources (only gold, food & tools)
        """
        user_id = str(ctx.author.id)
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        resources = self.empires[user_id]["resources"]
        
        
    
    @commands.command(name="expand", help="Expand your empire!")
    async def expand(self, ctx):
        """
        Expand empire land by spending gold.
        """
        user_id = str(ctx.author.id)
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        cost = 500
        resources = self.empires[user_id]["resources"]
        
        if resources["gold"] < cost:
            await ctx.send(f"❌ **{ctx.author.mention} You don't have enough gold to expand!**")
            return
        
        resources["gold"] -= cost
        resources["land"] += 50
        await self.save_empires()
        
        await ctx.send(f"🌄 **{ctx.author.mention} has expanded their land!** Its land is now `{resources['land']} acres`.")
        
    @commands.command(name="recruit", help="Recruit soldiers for your empire!")
    async def recruit(self, ctx, amount: int):
        """
        Recruit soldiers using gold.
        """
        user_id = str(ctx.author.id)
        
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        cost_per_soldier = 100
        total_cost = amount * cost_per_soldier
        resources = self.empires[user_id]["resources"]
        
        if resources["gold"] < total_cost:
            await ctx.send(f"❌ **{ctx.author.mention} You don't have enough gold to recruit!**")
            return
        
        resources["gold"] -= total_cost
        resources["soldiers"] += amount
        await self.save_empires()
        
        await ctx.send(f"🛡️ **{ctx.author.mention} recruited {amount} soldiers!** His army now has: `{resources['soldiers']}` soldiers.")
        
    @commands.command(name="tax", help="Tax the people of your empire!")
    async def tax(self, ctx, amount: int):
        """Modified tax command to affect happiness"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        if amount < 1 or amount > 100:
            await ctx.send(f"❌ **{ctx.author.mention} Tax rate must be between 1% and 100%!**")
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
        if await self.check_revolution(ctx, user_id):
            del self.empires[user_id]
            self.save_empires()
            await ctx.send("👋 Your empire has fallen to revolution! Use `!setempire` to start anew.")
            return
            
        await ctx.send(f"💰 **{ctx.author.mention} collected {gold_gained} gold in taxes!**\n"
                      f"Happiness decreased by {happiness_loss} points.")
        
    @commands.command(name="disband", help="Disband your empire!")
    async def disband(self, ctx):
        """
        Disband your empire!
        """
        user_id = str(ctx.author.id)
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        self.empires[user_id]["resources"]["soldiers"] = 0
        await self.save_empires()
        
        await ctx.send(f"👋 **{ctx.author.mention} has disbanded his empire!** His army now has: `{self.empires[user_id]['resources']['soldiers']}` soldiers.")
    
    @commands.command(name="event", help="Trigger a random event in your empire!")
    async def event(self, ctx):
        user_id = str(ctx.author.id)
        if user_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return

        event = random.choice(self.events_file)
        self.update_resources(user_id, event["changes"])
        await self.save_empires()
        
        await ctx.send(f"📜 **Empire Event:** {event['message']}")
        
    @commands.command(name="attack", help="Attack another users empire!")
    async def attack(self, ctx, target: nextcord.Member):
        """
        Attack another empire and steal gold!
        """
        attacker_id = str(ctx.author.id)
        target_id = str(target.id)
        
        if attacker_id not in self.empires or target_id not in self.empires:
            await ctx.send("⚠️ **Both players MUST have an empire to fight!** Use `!setempire` first.")
            return
        
        attacker_soldiers = self.empires[attacker_id]["resources"]["soldiers"]
        target_soldiers = self.empires[target_id]["resources"]["soldiers"]
        
        if attacker_soldiers <= 0:
            await ctx.send("❌ You have no soldiers to attack!")
            return
        
        if target_soldiers <= 0:
            await ctx.send(f"🥂 **{target.mention} had no defense!** You stole 200 gold!")
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
            
            await ctx.send(f"⚔️ **Battle Result:** {ctx.author.mention} won and stole {stolen_gold} **gold** from {target.mention}!🤺")
        else:
            await ctx.send(f"⚔️ **Battle Result:** {target.mention} defended **successfully!** No gold was stolen.")
            
    @commands.command(name="inviteempire", help="Invite users to your empire!")
    async def inviteempire(self, ctx, user: nextcord.Member):
        """
        Invite another player to your empire!
        """
        owner_id = str(ctx.author.id)
        target_id = str(user.id)
        
        if owner_id not in self.empires:
            await ctx.send("❌ **You don't have an empire!** Use `!setempire <name> <continent>` to create one!")
            return
        
        if target_id in self.empires:
            await ctx.send("⚠️ **That player already has their own empire!**")
            return
        
        empire_name = self.empires[owner_id]["name"]
        await ctx.send(f"📜 {user.mention}, you have been invited to join **{empire_name}**! Use `!joinempire {empire_name}` to accept!")
        
    @commands.command(name="joinempire", help="Join a users empire!")
    async def joinempire(self, ctx, empire_name: str):
        """
        Join an existing empire!
        """
        user_id = str(ctx.author.id)
        
        if user_id in self.empires:
            await ctx.send("❌ **You already have an empire!** Use `!statempire` to check it.")
            return
        
        for owner_id, empire in self.empires.items():
            if empire["name"].lower() == empire_name.lower():
                self.empires[user_id] = empire
                self.save_empires()
                await ctx.send(f"🥂 {ctx.author.mention} has joined **{empire_name}**!")
                return
            
        await ctx.send("⚠️ That **Empire** does not exist!")
        
def setup(bot):
    bot.add_cog(Empire(bot))