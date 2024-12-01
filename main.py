import discord
from discord import app_commands
from discord.ext import commands
import json
import os

my_secret = "MTMwNzcwNjMwNDY0MjY4MjkwMQ.GDX_Gn.bF6WhMawaeW9mrJRZjziOBMSQ0vBxwP5AJdx4c"
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

data_file = "stands_data.json"

if not os.path.exists(data_file):
    with open(data_file, "w") as file:
        json.dump({"stands": {}}, file)

def load_data():
    with open(data_file, "r") as file:
        return json.load(file)

def save_data(data):
    with open(data_file, "w") as file:
        json.dump(data, file, indent=4)

class MyBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bot.event
    async def on_ready():
        await bot.tree.sync()
        print(f"{bot.user} is now running!")

    @app_commands.command(name="mystand", description="Show your stand")
    async def mystand(self, interaction: discord.Interaction):
        await self.display_stand(interaction, interaction.user)

    @app_commands.command(name="stand", description="View another user's stand")
    async def stand(self, interaction: discord.Interaction, member: discord.Member):
        await self.display_stand(interaction, member)

    async def display_stand(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(thinking=True)
        data = load_data()
        user_id = str(member.id)
        stand = data["stands"].get(user_id, {})
        status = stand.get("status", "Default")

        if not stand:
            embed = discord.Embed(
                title="My Stand",
                description="This is my stand! There's nothing here yet, but it will be coming soon!",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title=stand.get("title", "My Stand"),
                description=stand.get("description", "No description yet."),
                color=discord.Color.from_str(stand.get("embedcolor", "#0000FF"))
            )
            
            if "gamepasses" in stand and stand["gamepasses"]:
                view = discord.ui.View()
                for gpass in stand["gamepasses"]:
                    button = discord.ui.Button(label=f"{gpass['price']}", emoji="<:robux:1281936443417034783>", url=gpass["url"], style=discord.ButtonStyle.link)
                    view.add_item(button)
                embed.set_footer(text=f"{member.display_name}'s stand | Status: {status}", icon_url=member.avatar.url if member.avatar else None)
                await interaction.followup.send(embed=embed, view=view)
                return

        embed.set_footer(text=f"{member.display_name}'s stand | Status: {status}", icon_url=member.avatar.url if member.avatar else None)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="edit_title", description="Edit your stand's title")
    async def edit_title(self, interaction: discord.Interaction, title: str):
        data = load_data()
        user_id = str(interaction.user.id)
        stand = data["stands"].get(user_id, {})
        status = stand.get("status", "Default")

        title_limit = 30 if status == "Default" else 60
        if len(title) > title_limit:
            await interaction.response.send_message(f"Title exceeds the limit of {title_limit} characters for {status} status.", ephemeral=True)
            return

        if user_id not in data["stands"]:
            data["stands"][user_id] = {}
        data["stands"][user_id]["title"] = title
        save_data(data)
        await interaction.response.send_message("Your stand's title has been updated.", ephemeral=True)

    @app_commands.command(name="edit_description", description="Edit your stand's description")
    async def edit_description(self, interaction: discord.Interaction, description: str):
        data = load_data()
        user_id = str(interaction.user.id)
        stand = data["stands"].get(user_id, {})
        status = stand.get("status", "Default")

        description_limit = 100 if status == "Default" else 200
        if len(description) > description_limit:
            await interaction.response.send_message(f"Description exceeds the limit of {description_limit} characters for {status} status.", ephemeral=True)
            return

        if user_id not in data["stands"]:
            data["stands"][user_id] = {}
        data["stands"][user_id]["description"] = description
        save_data(data)
        await interaction.response.send_message("Your stand's description has been updated.", ephemeral=True)

    @app_commands.command(name="edit_color", description="Edit your stand's embed color using a HEX code")
    async def edit_color(self, interaction: discord.Interaction, color: str):
        data = load_data()
        user_id = str(interaction.user.id)

        try:
            color_code = discord.Color.from_str(color)
        except ValueError:
            await interaction.response.send_message("Invalid color format! Please use a HEX color code like #FF5733.", ephemeral=True)
            return

        if user_id not in data["stands"]:
            data["stands"][user_id] = {}
        data["stands"][user_id]["embedcolor"] = color
        save_data(data)
        await interaction.response.send_message("Your stand's color has been updated.", ephemeral=True)

    @app_commands.command(name="addgpass", description="Add a game pass button to your stand")
    async def addgpass(self, interaction: discord.Interaction, price: int, url: str):
        data = load_data()
        user_id = str(interaction.user.id)
        stand = data["stands"].get(user_id, {})
        status = stand.get("status", "Default")

        gpass_limit = 5 if status == "Default" else 12
        if "gamepasses" not in stand:
            stand["gamepasses"] = []
        elif len(stand["gamepasses"]) >= gpass_limit:
            await interaction.response.send_message(f"Game passes exceed the limit of {gpass_limit} for {status} status.", ephemeral=True)
            return

        if any(gpass["price"] == price for gpass in stand["gamepasses"]):
            await interaction.response.send_message("A game pass with this price already exists.", ephemeral=True)
            return

        stand["gamepasses"].append({"price": price, "url": url})
        data["stands"][user_id] = stand
        save_data(data)
        await interaction.response.send_message("Game pass added to your stand.", ephemeral=True)

    @app_commands.command(name="removegpass", description="Remove a game pass button from your stand by price")
    async def removegpass(self, interaction: discord.Interaction, price: int):
        data = load_data()
        user_id = str(interaction.user.id)
        stand = data["stands"].get(user_id)

        if not stand or "gamepasses" not in stand:
            await interaction.response.send_message("You have no game passes to remove.", ephemeral=True)
            return

        new_gamepasses = [gpass for gpass in stand["gamepasses"] if gpass["price"] != price]
        if len(new_gamepasses) == len(stand["gamepasses"]):
            await interaction.response.send_message("No game pass with this price found.", ephemeral=True)
            return

        stand["gamepasses"] = new_gamepasses
        save_data(data)
        await interaction.response.send_message("Game pass removed from your stand.", ephemeral=True)

    @app_commands.command(name="info", description="Get information about the bot and its commands")
    async def info(self, interaction: discord.Interaction):
        description = (
            "Welcome to **PleaseDonateBot**! This bot allows you to set up your personal stand with game passes "
            "to help others find your items easily. \n\n"
            "**Commands:**\n"
            "- `/mystand` - Show your stand\n"
            "- `/stand {member}` - View another userâ€™s stand\n"
            "- `/edit_title {title}` - Edit your stand's title\n"
            "- `/edit_description {description}` - Edit your stand's description\n"
            "- `/edit_color {color}` - Change your stand's color\n"
            "- `/addgpass {price} {url}` - Add a game pass to your stand\n"
            "- `/removegpass {price}` - Remove a game pass from your stand\n"
            "- `/removegpass {price}` - Remove a game pass from your stand\n"

        )
        embed = discord.Embed(title="PleaseDonateBot Information", description=description, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

class MyBot(commands.Cog):

    @app_commands.command(name="notify_shutdown", description="Notify all servers about the bot's shutdown.")
    async def notify_shutdown(self, interaction: discord.Interaction):
        message = (
            "Hello everyone,\n\n"
            "We apologize for sending this message in this channel. "
            "This is to notify you that the bot will soon be disabled. "
            "Thank you for your understanding and support.\n\n"
            "Best regards, the Bot Team."
        )
        embed = discord.Embed(
            title="Bot Shutdown Notification",
            description=message,
            color=discord.Color.red()
        )

        failed_guilds = []
        for guild in self.bot.guilds:
            channel = next(
                (channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages),
                None
            )
            if channel:
                try:
                    await channel.send(embed=embed)
                except Exception:
                    failed_guilds.append(guild.name)

        if failed_guilds:
            failed_list = "\n".join(failed_guilds)
            await interaction.response.send_message(
                f"Notification sent, but failed for the following servers:\n{failed_list}", ephemeral=True
            )
        else:
            await interaction.response.send_message("Notification sent to all servers.", ephemeral=True)

async def main():
    async with bot:
        await bot.add_cog(MyBot(bot))
        await bot.start(my_secret)

import asyncio
asyncio.run(main())
