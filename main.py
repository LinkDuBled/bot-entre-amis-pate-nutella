import threading
import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from flask import Flask
import unidecode
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.all()

bot = commands.Bot(command_prefix='/', intents=intents)

# --- Flask app juste pour Render ---
app = Flask(__name__)


@app.route('/')
def home():
    return "Bot Discord is running!"


def run_flask():
    port = int(os.environ.get("PORT", 5000))  # Render donne le port via variable d'env
    app.run(host="0.0.0.0", port=port)


# --- Discord bot ---

secret_role = "weeb"

async def moderate_the_game_message(message: discord.Message) -> bool:
    """
    Retourne True si le message a été modéré (supprimé + notification),
    False sinon.
    """
    # Évite de te modérer toi-même
    if message.author == message.guild.me or message.author == message.channel.guild.me if hasattr(message.channel, "guild") else False:
        return False

    content_norm = re.sub(r'[^a-zA-Z]', '', unidecode.unidecode((message.content or "").replace(" ", "").lower().replace("@", "a")))
    if "thegame" in content_norm:
        # Tente de supprimer le message et notifie dans le salon
        try:
            await message.delete()
        except discord.Forbidden:
            # Pas la permission de supprimer; on peut quand même notifier si tu veux
            pass
        await message.channel.send(f"{message.author.mention} you piece of shit !")
        return True
    return False



@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user.name}")
    try:
        # Sync global (peut prendre du temps à apparaître)
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées (globales): {len(synced)}")

        # Option test: sync immédiat sur un serveur (remplace <GUILD_ID>)
        # guild = discord.Object(id=<GUILD_ID>)
        # synced_guild = await bot.tree.sync(guild=guild)
        # print(f"Commandes slash synchronisées (guild): {len(synced_guild)}")
    except Exception as e:
        print(f"Erreur lors de la sync : {e}")


@bot.event
async def on_member_join(member : discord.Member):
    guild_name = member.guild.name

    await member.send(f"Welcome to {guild_name}, {member.name} !")


@bot.event
async def on_message(message):
    await moderate_the_game_message(message)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    await moderate_the_game_message(after)
    await bot.process_commands(after)


@bot.tree.command(name="hello", description="Says hello to the user")
async def hello(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(f"Hello {interaction.user.mention}")


@bot.tree.command(name="assign", description="Assign the secret role")
async def assign(interaction: discord.Interaction) -> None:
    if interaction.guild is None:
        await interaction.response.send_message("Cette commande doit être utilisée dans un serveur.", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name=secret_role)
    if role:
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"{interaction.user.mention} You are now assigned to {secret_role}")
    else:
        await interaction.response.send_message("The role doesn't exist", ephemeral=True)


@bot.tree.command(name="remove", description="Remove the secret role")
async def remove(interaction: discord.Interaction) -> None:
    if interaction.guild is None:
        await interaction.response.send_message("Cette commande doit être utilisée dans un serveur.", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name=secret_role)
    if role:
        await interaction.user.remove_roles(role)
        await interaction.response.send_message(f"{interaction.user.mention} has had the {secret_role} removed")
    else:
        await interaction.response.send_message("The role doesn't exist", ephemeral=True)


@bot.tree.command(name="secret", description="Only for the secret role")
@app_commands.guild_only()
@app_commands.checks.has_role(secret_role)  # Astuce: préfère l’ID du rôle pour éviter les soucis de casse/doublons
async def secret(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Welcome to the club !", ephemeral=True)

@secret.error
async def secret_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("Tu n’as pas le rôle requis.", ephemeral=True)
    else:
        await interaction.response.send_message("Une erreur est survenue.", ephemeral=True)


@bot.tree.command(name="dm", description="Send a DM to yourself")
async def dm(interaction: discord.Interaction, msg: str = "Hello !") -> None:
    try:
        await interaction.user.send(f"You said {msg}")
        await interaction.response.send_message("DM envoyé.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Impossible d’envoyer un DM (paramètres de confidentialité).", ephemeral=True)


@bot.tree.command(name="poll", description="Create a poll")
async def poll(interaction: discord.Interaction, question: str) -> None:
    embed = discord.Embed(title="Polling", description=question)
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    await message.add_reaction("👍")
    await message.add_reaction("👎")


if __name__ == "__main__":
    # Lancer Flask dans un thread séparé
    threading.Thread(target=run_flask).start()
    # Lancer le bot Discord
    bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)