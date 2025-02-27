import asyncio
import json
import os
import random
from datetime import datetime, timedelta

import nextcord
from nextcord.ext import commands


class ApplyJob(commands.Cog):
    def __init__(self, bot):
        self.jobs_data = None
        self.bot = bot
        self.load_jobs()
        self.user_cooldowns = {}

    def load_jobs(self):
        jobs_file_path = os.path.join(os.path.dirname(__file__), "../json/jobs.json")
        with open(jobs_file_path, 'r') as f:
            self.jobs_data = json.load(f)

    @commands.command(name="jobs")
    async def jobs(self, ctx):
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
        
        await ctx.send(embed=embed)

    @commands.command(name="apply")
    async def apply(self, ctx, job: str):
        if job not in self.jobs_data["jobs"]:
            await ctx.send("That job doesn't exist! Use !jobs to see available positions.")
            return

        # Check cooldown
        user_id = str(ctx.user.id)
        if user_id in self.user_cooldowns:
            if datetime.now() < self.user_cooldowns[user_id]:
                wait_time = (self.user_cooldowns[user_id] - datetime.now()).seconds
                await ctx.send(f"You must wait {wait_time} seconds before applying again!")
                return

        job_data = self.jobs_data["jobs"][job]
        
        # Start interview
        await ctx.send(f"📝 Starting interview for {job} position...")
        
        questions = job_data["interview_questions"]
        score = 0
        
        for question in questions:
            question_embed = nextcord.Embed(
                title="Interview Question",
                description=question,
                color=nextcord.Color.gold()
            )
            await ctx.followup.send(embed=question_embed)

            def check(m):
                return m.author == ctx.user and m.channel == ctx.channel

            try:
                answer = await self.bot.wait_for('message', timeout=30.0, check=check)
                # Score based on answer length and complexity
                if len(answer.content) > 20:
                    score += 1

            except asyncio.TimeoutError:
                await ctx.followup.send("Interview timed out! Try again later.")
                return

        # Results
        if score >= len(questions) // 2:
            success_embed = nextcord.Embed(
                title="🎉 Congratulations!",
                description=f"You've been hired as a {job}!\nSalary: {job_data['salary']}🪙/hr\nUse /work to start earning!",
                color=nextcord.Color.green()
            )
            
            await self.update_user_job(ctx.user.id, job)
            
            # Set cooldown
            self.user_cooldowns[user_id] = datetime.now() + timedelta(hours=24)
            
            await ctx.followup.send(embed=success_embed)
        else:
            fail_embed = nextcord.Embed(
                title="❌ Unfortunately...",
                description="We'll keep your application on file. Try again in 24 hours!",
                color=nextcord.Color.red()
            )
            await ctx.followup.send(embed=fail_embed)

    @commands.command(name="work")
    async def work(self, ctx):
        job = await self.get_user_job(ctx.user.id)
        
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
            
            await self.update_user_balance(ctx.user.id, earnings)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("You need to get a job first! Use !apply to apply for one.")


def setup(bot):
    bot.add_cog(ApplyJob(bot))
