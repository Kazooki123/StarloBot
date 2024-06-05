import nextcord
from nextcord.ext import commands
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import premium_check

load_dotenv('../.env')

GEMINI_API = os.getenv('GEMINI_TOKEN')

genai.configure(api_key=GEMINI_API)

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 400,
}

model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

# RAP BATTLE COMMAND (For fun using A.I)
def generate_rap_line(character, previous_lines):
    prompt = f"{character} is a rapper in a rap battle. "
    for line in previous_lines:
        prompt += f"{line}\n"
    prompt += f"{character} responds:" 
    
    response = model.generate_content(prompt)
    
    text = response.candidates[0].content.parts[0].content
    
    return text.strip()

HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API")

class Art(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @nextcord.slash_command(name='ai_art', description="Gives out an A.I generated image base in your prompt!")
    @premium_check()
    async def generate_image(self, ctx: nextcord.Interaction, *, prompt):
        api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"}
        # payload = {
        #     "inputs": prompt,
        #     "options": {
        #         "wait_for_model": True
        #     }
        # }
        def query(payload):
            response = requests.post(api_url, headers=headers, json=payload)
	                             
            return response.content
    
        try:
        
            bytes = query(
                {
                    "inputs": prompt
                }
            )
            import io
            from PIL import Image
            image = Image.open(io.BytesIO(bytes))
            with io.BytesIO() as image_binary:
                image.save(image_binary, 'JPEG')
                image_binary.seek(0)
                await ctx.send(file=nextcord.File(fp=image_binary, filename='generated_image.jpg'))


        except requests.exceptions.RequestException as e:
            print(f"API Request Error: {e}")
            await ctx.send("Error occurred while making the API request.")

        except json.JSONDecodeError as e:
            print(f"JSON Decoding Error: {e}")
            await ctx.send("Error occurred while decoding the API response.")
            
    @nextcord.slash_command(description="Plays a rap battle based on characters!")
    async def rapbattle(self, ctx: nextcord.Interaction, character1: str, vs: str, character2: str):
        if vs.lower() != "vs".lower():
            await ctx.send("Usage: !rapbattle {character} V.S {character}")
            return
    
        character1_lines = []
        character2_lines = []
    
        rounds = 3
    
        for i in range(rounds):
            line1 = generate_rap_line(character1, character1_lines + character2_lines)
            character1_lines.append(line1)
        
            line2 = generate_rap_line(character2, character1_lines + character2_lines)
            character2_lines.append(line2)
        
        embed = nextcord.Embed(title="Rap Battle", color=nextcord.Color.gold())
        embed.add_field(name=f"{character1}:", value="\n".join(character1_lines), inline=False)
        embed.add_field(name=f"{character2}:", value="\n".join(character2_lines), inline=False)
    
        await ctx.send(embed=embed)
            
def setup(bot):
    bot.add_cog(Art(bot))