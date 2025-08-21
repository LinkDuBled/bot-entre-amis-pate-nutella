import threading
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from flask import Flask

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

# --- Flask app juste pour Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Discord is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))  # Render donne le port via variable d'env
    app.run(host="0.0.0.0", port=port)

# --- Discord bot ---

secret_role="weeb"

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user.name}")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to testbot server {member.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "the game" in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention} you piece of shit !")
    await bot.process_commands(message)

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}")

@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} You are now assigned to {secret_role}")
    else:
        await ctx.send("The role doesn't exist")

@bot.command()
async def remove(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} has had the {secret_role} removed")
    else:
        await ctx.send("The role doesn't exist")

@bot.command()
@commands.has_role(secret_role)
async def secret(ctx):
    await ctx.send("Welcome to the club !")

@secret.error
async def secret_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("you can't do that !")

@bot.command()
async def dm(ctx, *, msg):
    await ctx.author.send(f"You said {msg}")

@bot.command()
async def reply(ctx):
    await ctx.reply("Tis is a reply to your message")

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="Polling", description=question)
    poll_massage = await ctx.send(embed=embed)
    await poll_massage.add_reaction("👍")
    await poll_massage.add_reaction("👎")

if __name__ == "__main__":
    # Lancer Flask dans un thread séparé
    threading.Thread(target=run_flask).start()
    # Lancer le bot Discord
    bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
