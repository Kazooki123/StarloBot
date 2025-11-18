import os

import nextcord
import psycopg2
from dotenv import load_dotenv
from nextcord.ext import commands

load_dotenv("../.env")

DATABASE_URL = os.getenv("POSTGRES_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()


def company_exist(user_id):
    cur.execute("SELECT 1 FROM companies WHERE user_id = %s", (user_id,))
    return cur.fetchone() is not None


class CompanyTycoon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="startcompany", description="Start your company now!")
    async def start_company(self, interaction: nextcord.Interaction, company_name: str, industry: str):
        user_id = interaction.author.id

        if company_exist(user_id):
            await interaction.response.send_message(f"❌ {interaction.author.mention} **You already own a company!**")
            return
        
        valid_industries = ["Technology", "Finance", "Retail", "Healthcare", "Manufacturing", "Entertainment"]
        
        if industry not in valid_industries:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **That's an Invalid Industry!** Choose from: `{','.join(valid_industries)}`")
            return
        
        cur.execute(
            "INSERT INTO companies (user_id, company_name, industry) VALUES (%s, %s, %s)",
            (user_id, company_name, industry)
        )
        conn.commit()
        
        await interaction.response.send_message(f"✅ {interaction.author.mention} **You have successfully started your company!**")
        await interaction.response.send_message(f"📝 Company Name: {company_name}")
        await interaction.response.send_message(f"🏭 Industry: {industry}")
        
    @nextcord.slash_command(name="companyinfo", description="Check your company info and more!")
    async def company_info(self, interaction: nextcord.Interaction):
        user_id = interaction.author.id
        
        cur.execute(
            "SELECT company_name, industry, funds, employees, reputation FROM companies WHERE user_id = %s",
            (user_id,)
        )
        company = cur.fetchone()
        
        if not company:
            await interaction.response.send_message(f"❌ {interaction.author.mention} **You don't own a company!**")
            return
        
        company_name, industry, funds, employees, reputation = company
        embed = nextcord.Embed(
            title=f"🏢 {company_name} - {industry} Industry",
            color=nextcord.Color.blue()
        )
        embed.add_field(name="💰 Funds", value=f"${funds}", inline=True)
        embed.add_field(name="👥 Employees", value=str(employees), inline=True)
        embed.add_field(name="🌟 Reputation", value=str(reputation), inline=True)
        await interaction.response.send_message(embed=embed)
        
    @nextcord.slash_command(name="hire", description="Hire more people!")
    async def hire(self, interaction):
        """
        
        """


def setup(bot):
    bot.add_cog(CompanyTycoon(bot))
