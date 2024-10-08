import nextcord
from nextcord.ext import commands
import requests
from dotenv import load_dotenv
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import premium_check

load_dotenv()

HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API")


class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Question and answer with Huggingface Mistral-7B-Instruct-v0.2 API
    @nextcord.slash_command(name='question', description="A.I answers your question!")
    @premium_check()
    async def answer_question(self, ctx: nextcord.Interaction, *, question):
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
