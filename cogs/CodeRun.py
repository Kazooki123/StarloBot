import nextcord
from nextcord.ext import commands
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv('../.env')

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")


class CodeRun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.language_ids = {
            'python': 71,
            'javascript': 93,
            'typescript': 74,
            'java': 62,
            'lua': 64,
            'c': 50,
            'cpp': 54,
            'c++': 54,
            'assembly': 45,
            'ruby': 72,
            'rust': 73,
            'elixir': 57,
            'go': 60,
        }
        self.headers = {
            'content-type': 'application/json',
            'X-RapidAPI-Key': RAPIDAPI_KEY,
            'X-RapidAPI-Host': 'judge0-ce.p.rapidapi.com'
        }
        self.base_url = 'https://judge0-ce.p.rapidapi.com'

    @nextcord.slash_command(name="code", description="Interprets and displays the output code that you have given.")
    async def code_run(self, interaction, language: str = None):
        """
        Runs code in the specified programming language
        Usage: !code [language]
        """
        if language is None:
            supported_langs = ", ".join(f"`{lang}`" for lang in self.language_ids.keys())
            await interaction.response.send_message(f"❌ {interaction.author.mention} **Please specify a language.** Supported languages: {supported_langs}")
            return

        language = language.lower()
        if language not in self.language_ids:
            supported_langs = ", ".join(f"`{lang}`" for lang in self.language_ids.keys())
            await interaction.response.send_message(f"❌ {interaction.author.mention} **Unsupported language.** Supported languages: {supported_langs}")
            return

        prompt_message = await interaction.response.send_message(f"**Please type the {language} code here**")

        def check(message):
            return message.author == interaction.author and message.channel == interaction.channel

        try:
            code_message = await self.bot.wait_for('message', check=check, timeout=300)
            code = code_message.content.strip()

            if code.startswith('```') and code.endswith('```'):
                code = '\n'.join(code.split('\n')[1:-1])
            elif code.startswith('`') and code.endswith('`'):
                code = code[1:-1]

            status_message = await interaction.response.send_message("👾 **Compiling and running...**")

            result = await self.execute_code(language, code)

            embed = nextcord.Embed(
                title=f"{language.capitalize()} Code Execution",
                color=nextcord.Color.blue()
            )

            if len(code) > 1024:
                embed.add_field(name="Code", value=f"```{language}\n{code[:1021]}...```", inline=False)
            else:
                embed.add_field(name="Code", value=f"```{language}\n{code}```", inline=False)

            if result['stdout']:
                stdout = result['stdout']
                if len(stdout) > 1024:
                    stdout = stdout[:1021] + "..."
                embed.add_field(name="Output", value=f"```\n{stdout}```", inline=False)

            if result['stderr']:
                stderr = result['stderr']
                if len(stderr) > 1024:
                    stderr = stderr[:1021] + "..."
                embed.add_field(name="Error", value=f"```\n{stderr}```", inline=False)
                embed.color = nextcord.Color.red()

            if result['compile_output']:
                compile_output = result['compile_output']
                if len(compile_output) > 1024:
                    compile_output = compile_output[:1021] + "..."
                embed.add_field(name="Compilation Error", value=f"```\n{compile_output}```", inline=False)
                embed.color = nextcord.Color.red()

            if result['time'] and result['memory']:
                embed.add_field(
                    name="Stats",
                    value=f"**Execution Time:** {result['time']}s | Memory: {result['memory']} KB",
                    inline=False
                )

            await status_message.edit(content=None, embed=embed)

        except asyncio.TimeoutError:
            await prompt_message.edit(content="Code input timed out. Please try again.")
        except Exception as e:
            await interaction.response.send_message(f"❌ **An error occurred**: {str(e)}")

    async def execute_code(self, language, code):
        payload = {
            'language_id': self.language_ids[language],
            'source_code': code,
            'stdin': '',
            'cpu_time_limit': 5
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Submit the code
                async with session.post(
                        f'{self.base_url}/submissions',
                        headers=self.headers,
                        json=payload
                ) as response:
                    if response.status != 201:
                        return {
                            'stdout': '',
                            'stderr': f'API Error: {response.status}',
                            'compile_output': '',
                            'time': None,
                            'memory': None
                        }

                    response_data = await response.json()
                    token = response_data['token']

                for _ in range(10):
                    await asyncio.sleep(1)

                    async with session.get(
                            f'{self.base_url}/submissions/{token}',
                            headers=self.headers
                    ) as response:
                        if response.status != 200:
                            continue

                        result = await response.json()
                        if result['status']['id'] not in [1, 2]:
                            return {
                                'stdout': result.get('stdout', ''),
                                'stderr': result.get('stderr', ''),
                                'compile_output': result.get('compile_output', ''),
                                'time': result.get('time', None),
                                'memory': result.get('memory', None)
                            }

                return {
                    'stdout': '',
                    'stderr': 'Execution timed out or is still running.',
                    'compile_output': '',
                    'time': None,
                    'memory': None
                }
        except Exception as e:
            return {
                'stdout': '',
                'stderr': f'Error: {str(e)}',
                'compile_output': '',
                'time': None,
                'memory': None
            }


def setup(bot):
    if not os.getenv('RAPIDAPI_KEY'):
        print("⚠️ Warning: RAPIDAPI_KEY not found in environment variables. CodeRun cog will not function properly.")

    bot.add_cog(CodeRun(bot))
