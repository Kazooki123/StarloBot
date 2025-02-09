import nextcord
from nextcord.ext import commands
import json
import random
import asyncio
from datetime import datetime, timedelta

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_jobs()
        self.user_cooldowns = {}

    def load_jobs(self):
        with open('cogs/jobs.json', 'r') as f:
            self.jobs_data = json.load(f)

    @nextcord.slash_command(
        name="jobs",
        description="View available jobs!",
        guild_ids=[1237746712291049483]
    )
    async def jobs(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="🏢 Available Jobs",
            description="Choose a job to apply for!",
            color=nextcord.Color.blue()
        )
        
        for job, details in self.jobs_data["jobs"].items():
            embed.add_field(
                name=f"💼 {job}",
                value=f"```\nSalary: {details['salary']}🪙/hr\n{details['description']}\n\nPerks: {', '.join(details['perks'])}```",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(
        name="apply",
        description="Apply for a job",
        guild_ids=[1237746712291049483]
    )
    async def apply(self, interaction: nextcord.Interaction, job: str):
        if job not in self.jobs_data["jobs"]:
            await interaction.response.send_message("That job doesn't exist! Use /jobs to see available positions.")
            return

        # Check cooldown
        user_id = str(interaction.user.id)
        if user_id in self.user_cooldowns:
            if datetime.now() < self.user_cooldowns[user_id]:
                wait_time = (self.user_cooldowns[user_id] - datetime.now()).seconds
                await interaction.response.send_message(f"You must wait {wait_time} seconds before applying again!")
                return

        job_data = self.jobs_data["jobs"][job]
        
        # Start interview
        await interaction.response.send_message(f"📝 Starting interview for {job} position...")
        
        questions = job_data["interview_questions"]
        score = 0
        
        for question in questions:
            question_embed = nextcord.Embed(
                title="Interview Question",
                description=question,
                color=nextcord.Color.gold()
            )
            await interaction.followup.send(embed=question_embed)

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                answer = await self.bot.wait_for('message', timeout=30.0, check=check)
                # Score based on answer length and complexity
                if len(answer.content) > 20:
                    score += 1

            except asyncio.TimeoutError:
                await interaction.followup.send("Interview timed out! Try again later.")
                return

        # Results
        if score >= len(questions) // 2:
            success_embed = nextcord.Embed(
                title="🎉 Congratulations!",
                description=f"You've been hired as a {job}!\nSalary: {job_data['salary']}🪙/hr\nUse /work to start earning!",
                color=nextcord.Color.green()
            )
            
            await self.update_user_job(interaction.user.id, job)
            
            # Set cooldown
            self.user_cooldowns[user_id] = datetime.now() + timedelta(hours=24)
            
            await interaction.followup.send(embed=success_embed)
        else:
            fail_embed = nextcord.Embed(
                title="❌ Unfortunately...",
                description="We'll keep your application on file. Try again in 24 hours!",
                color=nextcord.Color.red()
            )
            await interaction.followup.send(embed=fail_embed)

    @nextcord.slash_command(
        name="work",
        description="Work at your job to earn coins!",
        guild_ids=[1237746712291049483]
    )
    async def work(self, interaction: nextcord.Interaction):
        job = await self.get_user_job(interaction.user.id)
        
        if job in self.jobs_data["jobs"]:
            earnings = random.randint(
                self.jobs_data["jobs"][job]["salary"] - 100,
                self.jobs_data["jobs"][job]["salary"] + 100
            )
            
            work_messages = [
                f"You wrote some clean code and earned {earnings}🪙!",
                f"You fixed a critical bug and earned {earnings}🪙!",
                f"You completed a project ahead of schedule and earned {earnings}🪙!"
            ]
            
            embed = nextcord.Embed(
                title="💼 Work Complete!",
                description=random.choice(work_messages),
                color=nextcord.Color.green()
            )
            
            await self.update_user_balance(interaction.user.id, earnings)
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("You need to get a job first! Use /apply to apply for one.")

def setup(bot):
    bot.add_cog(Currency(bot))