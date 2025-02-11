import nextcord
from nextcord.ext import commands
import requests
from dotenv import load_dotenv
import json
import os

load_dotenv('../.env')

HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API")

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def is_premium(user_id):
    async with bot.pg_pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT premium_user FROM user_data
            WHERE user_id = $1;
            """, user_id
        )
        return record and record['premium_user']
        
def premium_check():
    async def predicate(ctx):
        if await is_premium(ctx.author.id):
            return True
        else:
            await ctx.send('Looks like you haven\'t been premium yet, please type !premium, Thank you.')
            return False

    return commands.check(predicate)

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Question and answer with Huggingface Mistral-7B-Instruct-v0.2 API
    @commands.command(name='question')
    @premium_check()
    async def answer_question(self, ctx, *, question):
        api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}

        def query(payload):
            response = requests.post(api_url, headers=headers, json=payload)

            return response.content

        try:
            response = query(
                {
                    "inputs": question
                }
            )
            response = response.decode('utf-8')
            answer = json.loads(response)
            answer = answer[0]['generated_text']

            answer_embed = nextcord.Embed(title="AI Answer", color=nextcord.Color.blue())
            answer_embed.add_field(name="Question", value=question, inline=False)
            answer_embed.add_field(name="Answer By AI", value=answer)
            await ctx.send(embed=answer_embed)

            response_json = json.loads(response)

            if response_json.get("error"):
                await ctx.send(f"Error generating answer: {response_json['error']}")
            else:
                answer = response_json[0]['generated_text']
                await ctx.send(answer)

        except requests.exceptions.RequestException as e:
            print(f"API Request Error: {e}")
            await ctx.send("Error occurred while making the API request.")

        except ValueError as e:
            print(f"JSON Decoding Error: {e}")
            await ctx.send("Error occurred while decoding the API response.")


def setup(bot):
    bot.add_cog(Question(bot))
