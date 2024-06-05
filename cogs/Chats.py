import nextcord
from nextcord.ext import commands
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(
    api_key = os.getenv('GROQ_API_KEY'),
)

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name='chat')
    async def generate_chat(self, ctx: nextcord.Interaction):
        # Pass the user's message content to the chatbot
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": ctx.message.content,
                }
            ],
            model="gemma-7b-it",
            temperature=0.5,
            max_tokens=1024,
            top_p=1,
            stop=None
        )

        # Send the chatbot's response back to the Discord channel
        await ctx.send(chat_completion.choices[0].message.content)
     
        
def setup(bot):
    bot.add_cog(Chat(bot))