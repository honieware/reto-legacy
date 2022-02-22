# Import global variables and databases.
from definitions import srv, priv, support, botname

# Imports, database definitions and all that kerfuffle.

import discord
from discord.ext import commands, tasks
import asyncio
import pyfiglet
from tinydb import TinyDB, Query, where
from tinydb.operations import add, subtract, delete
import aiohttp        
import aiofiles
import os.path
import os
import json
import random
from datetime import datetime, date
import logging

# sharedFunctions
from sharedFunctions import printLeaderboard, createLeaderboardEmbed, getProfile, sendErrorEmbed, getCurrentPrefix, exportData

# ----------------------------------------------------------------------------------------------

class Miscellaneous(commands.Cog):
	"""
	Bonus stuff that has to do with the bot's updates, invites, privacy settings, and other extras.
	"""
	def __init__(self, client):
		self.client = client
	
	#------------------------
	# MISCELLANEOUS COMMANDS
	#------------------------
	@commands.command(description="Simple testing command to check the bot's latency.")
	async def ping(self, ctx):
		"""Nothing but a simple latency tester."""
		latency = str(int(round(self.client.latency,3)*1000))
		await ctx.send("🏓 **Pong!** Looks like the latency is about " + latency + "ms.")

	@commands.command(aliases=['update', 'changelog', 'log', 'news'], description="Check the new features on the bot since last update!")
	async def updates(self, ctx):
		"""Check Reto's new features!"""

		prefix = await getCurrentPrefix(ctx)
		defaultPlus  = self.client.get_emoji(809578589439393822)
		defaultMinus = self.client.get_emoji(809578623732023337)
		defaultStar  = self.client.get_emoji(809578548418969620)
		embed=discord.Embed(title="Changelog", description="Reto 1.7 LTS (The Last Hurrah Update) - 2022-2-21\n[Check out the full changelog on Github!](https://github.com/honiemun/reto-legacy/releases)", color=0x74f8dd)
		embed.set_thumbnail(url="https://i.ibb.co/ySfQhDG/reto.png")
		embed.add_field(name="What's new in v1.7", value="** **", inline=False)
		embed.add_field(name="☯️ Local Karma", value="At long last, you can both collect Karma specific to the server you're in, *and* globally throughout all servers! Local Karma works with everything: `?profile` now shows two different counters, one server-specific and one global, `?lb` now ranks users against their local karma points, and various other parts of Reto have been tweaked to accomodate!\n** **", inline=False)
		embed.add_field(name="📘 Customizable Local Karma Names", value="Don't want your shiny new Server specific Karma total to have a generic name like _My Server Karma_? Using `?localkarma`, you can set not only what it'll be called, but an emoji to represent your new currency, too!\n** **", inline=False)
		embed.add_field(name="🤖 Granular Autovote", value="Now you can enable `?autovote` specifically for images, text messages, videos, files, embeds... the works! No more having every single little message auto-voted - fine-tune it to your hearts' content.\n** **", inline=False)
		embed.add_field(name="🌟 Beautified Best-Of Messages", value="There's a couple improvements on the Best Of messages: each now includes a link to jump to the original message, and if Reto can't show a file (such as videos, audio files, multiple images...) it'll let you know on the message's footer! Also, Best Of messages support Replies now - so you'll never lose the context on who's replying to who!\n** **", inline=False)
		embed.add_field(name="👤 Reworked Profiles", value="With the change to Local Karma, the `?profile` command has been updated a tad as well! The stats look cleaner, the Badges have their own section, and the Embed changes colour depending on what your profile picture's colour is.\n** **", inline=False)
		embed.add_field(name="Also including changes from v1.6a & v1.6b:", value="- Create custom Notification Messages with `?nm` and change what Reto says after a Reaction! (You can also add Modifiers to it, or restore it to default with ?nm default).\n- Bot doesn't detect the Best Of channel? Use `?reattach #channel` to get it running!\n- Get a copy of your personal data with `?privacy data export`!\n- Errors and exceptions get more detailed, as Reto sends a stacktrace whenever it finds some nasty block o' code.\n- If there are multiple people Starring a message, Reto will send a new message for that!\n** **", inline=False)
		embed.add_field(name="And Bot Owner updates:", value="- Made the console way prettier to look at, with a simplified look, update notices and coloured alerts!\n- Config files got easier to set up, with a Creation Wizard before launching Reto if it can't find your configs.\n- Use `?rosebud` (or `?motherlode`, or `?editkarma` if you're not a Sims fan) to change an user's global karma total! Keep in mind that they'll have a Mark of Shame to go alongside it, though.\n- More code clean-up, as always!\n** **", inline=False)
		embed.add_field(name="🎉 The Last Hurrah", value="This will be the last major update to Reto v1.x (now Reto Legacy). [There's now a new repo](https://github.com/honiemun/reto-legacy) where the project will live, and come March 1st, 2022 it will enter Long Term Support mode, meaning only bug fixes will be implemented until March 2023.\n\nReto isn't going anywhere, though! Reto v2 (codenamed Retool) is in the works, built from the ground up and using modern Discord technology such as Slash Commands and Button Components. The bot will migrate to v2 once it's completed - and if you're self-hosting, hopefully you'll consider hopping versions as well!\n** **", inline=False)
		await ctx.send(embed=embed)

	@commands.command(description='Sends an invite link for the bot to invite it to other servers.')
	async def invite(self, ctx):
		"""Invite the bot to your server!"""
		await ctx.send("Here's an invitation link for the bot: https://discordapp.com/api/oauth2/authorize?client_id=" + str(self.client.user.id) + "&permissions=1342449744&scope=bot")

	@commands.command(description='This command just throws a generic error from the error handler.')
	async def error(self, ctx):
		"""Throws... an error. For testing purposes."""
		await sendErrorEmbed(ctx.message.channel,"I'm not sure why you're here, truth to be told! Nothing has necessarily gone wrong, you just decided to throw an error, for some reason. Er, good job?")

	@commands.command(description='Get a link to Discord\'s support server!')
	async def support(self, ctx):
		"""Sends a link to the Discord's support server!"""
		embed=discord.Embed(title="Need a hand?", description="[Join the Discord support server](" + support + ") to ask for help, report bugs, request features and get news and updates on " + botname + "!", color=0x8bd878)
		await ctx.send(embed=embed)

	@commands.command(aliases=['data'], description="Manage the data Reto holds about you - limit what it can do with it, erase it entirely, and more!")
	async def privacy(self,ctx,*args):
		"""Info and settings on what Reto knows about you."""

		prefix = await getCurrentPrefix(ctx)
		if not args:
			embed=discord.Embed(title="Privacy Settings", description="Manage how Reto accesses your data.")
			privSettings = priv.search(Query().username == ctx.message.author.id)
			if privSettings:
				privSettings = privSettings[0]
			if privSettings and "mode" in privSettings and privSettings['mode'] == True:
				emojiSwitch = "\\✔️"
				textSwitch = "(Enabled - disable it with `" + prefix + "privacy mode off`)"
			else:
				emojiSwitch = "\\❌"
				textSwitch = "(Disabled - enable it with `" + prefix + "privacy mode on`)"
			embed.add_field(name=emojiSwitch + " Privacy Mode", value="Let Reto know you don't want your (reacted to) comments logged. When enabled, this will make it so you don't show up on Post Leaderboards and Global Post Leaderboards. " + textSwitch, inline=False)
			
			if privSettings and "storage" in privSettings and privSettings['storage'] == True:
				emojiSwitch = "\\✔️"
				textSwitch = "(Enabled - disable it with `" + prefix + "privacy storage off`)"
			else:
				emojiSwitch = "\\❌"
				textSwitch = "(Disabled - enable it with `" + prefix + "privacy storage on`)"
			embed.add_field(name=emojiSwitch + " Permanent Storage", value="Reto deletes your comment information 30 days after it's first saved, per Discord policies. If you'd like to have your comments be stored indefinitely, enable this option. " + textSwitch, inline=False)

			if not isinstance(ctx.message.channel, discord.channel.DMChannel):
				srvSettings = srv.get(Query().serverid == ctx.message.guild.id)
				if srvSettings and ("global" in srvSettings and srvSettings['global'] == True or not "global" in srvSettings):
					emojiSwitch = "\\✔️"
					textSwitch = "(Enabled - Curators can disable it with `" + prefix + "privacy server off`)"
				else:
					emojiSwitch = "\\❌"
					textSwitch = "(Disabled - Curators can enable it with `" + prefix + "privacy server on`)"
				embed.add_field(name=emojiSwitch + " Server Logging", value="Setting this as disabled means the server won't show up on Global Post Leaderboards, perfect for private or confidential conversations. " + textSwitch, inline=False)
			embed.add_field(name="\\📁 Export your user data", value="Want to get a look of what data Reto knows about you? Want to export your previous user data to a new instance of the bot? Export your personal data with `" + prefix + "privacy data export`!", inline=True)
			embed.add_field(name="\\💣 Destroy your user data", value="Ready to leave Reto, and want to leave your previous conversations, points and the like behind? Do note that this action is destructive, and will only affect you and not that of the server at large. If so, use `" + prefix + "privacy data delete`.", inline=True)

			await ctx.send(embed=embed)
		elif args[0] == "mode":
			if len(args) == 1:
				await sendErrorEmbed(ctx.channel, "Not enough arguments!");
				return
			if args[1] == "on":
				privSettings = priv.search(Query().username == ctx.message.author.id)
				if privSettings:
					privSettings = privSettings[0]
				if not privSettings or "mode" in privSettings and privSettings['mode'] == False or not "mode" in privSettings: # pain
					priv.upsert({'username': ctx.message.author.id, "mode": True}, Query().username == ctx.message.author.id)
					await ctx.send("**Done!** From now on, Reto will not log your posts. This will opt you out from post leaderboards - if you so wish to re-enable this feature, you can use *" + prefix + "privacy mode off* to whitelist yourself.")
				else:
					await ctx.send("**Privacy Mode was already turned on**, so nothing has changed. *Did you mean " + prefix + "privacy mode off?*")
			elif args[1] == "off":
				priv.upsert({'username': ctx.message.author.id, "mode": False}, Query().username == ctx.message.author.id)
				await ctx.send("**Done!** From now on, Reto will start logging your posts, enabling you to use post leaderboards. You can always turn this off with *" + prefix + "privacy mode on.*")
		elif args[0] == "storage":
			if len(args) == 1:
				await sendErrorEmbed(ctx.channel, "Not enough arguments!");
				return
			if args[1] == "on":
				privSettings = priv.search(Query().username == ctx.message.author.id)
				if privSettings:
					privSettings = privSettings[0]
				if not privSettings or "storage" in privSettings and privSettings['storage'] == False or not "storage" in privSettings: # pain
					priv.upsert({'username': ctx.message.author.id, "storage": True}, Query().username == ctx.message.author.id)
					await ctx.send("**Done!** From now on, Reto will not delete your posts after 30 days. That precious place in the leaderboards will stay just where it is. If you change your mind and want to go back to the defaults, you can always do *" + prefix + "privacy storage off* to whitelist yourself.")
				else:
					await ctx.send("**Permanent Storage was already turned on**, so nothing has changed. *Did you mean " + prefix + "privacy storage off?*")
			elif args[1] == "off":
				priv.upsert({"storage": False}, Query().username == ctx.message.author.id)
				await ctx.send("**Done!** From now on, Reto will start deleting your posts after 30 days, as is the default. You can go back to Permanent Storage with *" + prefix + "privacy storage on.*")
		elif args[0] == "server":
			if len(args) == 1:
				await sendErrorEmbed(ctx.channel, "Not enough arguments!");
				return
			if not isinstance(ctx.message.channel, discord.channel.DMChannel):
				if discord.utils.get(ctx.message.author.roles, name="Curator"):
					if args[1] == "on":
						srvSettings = srv.search(Query().serverid == ctx.message.guild.id)[0]
						if not "global" in srvSettings or "global" in srvSettings and srvSettings['global'] == False: # slightly less of a pain
							srv.update({"global": True}, Query().serverid == ctx.message.guild.id)
							await ctx.send("**Done!** Reto will now include the server in Global Post Leaderboards. If you'd prefer to go back into the darkness, feel free to use *" + prefix + "privacy server off*.")
						else:
							await ctx.send("**Server Logging was already turned on**, so nothing has changed. *Did you mean " + prefix + "privacy server off?*")
					elif args[1] == "off":
						srv.update({"global": False}, Query().serverid == ctx.message.guild.id)
						await ctx.send("**Done!** Reto will not include messages sent on this server on the Global Post Leaderboards. Wanna showcase your community's creativity again? Enable it back with *" + prefix + "privacy server on.*")
				else:
					await sendErrorEmbed(ctx,"You have to be a *Curator* to access this command!")
			else:
				await sendErrorEmbed(ctx,"Hey! You can't edit Server Settings when you're not in a server, now!")
		elif args[0] == "data":
			if args[1] == "delete":
				embed=discord.Embed(title="Are you SURE?!", description="This action is permanent and cannot be undone!\nThis is what will be deleted, upon confirming:\n\n• Your karma and other profile information\n• Logs about the servers you're in\n• Every comment stored in the Post Leaderboards\n• Your privacy settings\n\nTo confirm your data's deletion, react below. To cancel, ignore this message.", color=0xfe2c2c)
				await ctx.message.add_reaction(emoji='✉')
				directmessage = await ctx.message.author.send(embed=embed)
				await directmessage.add_reaction(emoji='💣')
			elif args[1] == "export":
				embed=discord.Embed(title="Here's your data!", description="Attached below are the .JSON files Reto stores about you. (Do note this doesn't include server specific files.)", color=0xfee75c)
				await ctx.message.add_reaction(emoji='✉')
				directmessage = await ctx.message.author.send(embed=embed)
				await exportData(str(ctx.message.author.id), ctx)
		else:
			await sendErrorEmbed(ctx,"Invalid argument. Try not adding any to see all the available ones!")
			
def setup(client):
	client.add_cog(Miscellaneous(client))