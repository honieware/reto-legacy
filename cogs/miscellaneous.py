# Import global variables and databases.
from definitions import srv, priv

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
		embed=discord.Embed(title="Changelog", description="Reto 1.6 - 2021/2/12\n[Check out the full, more readable changelog on Github!](https://github.com/honiemun/reto-legacy/releases)", color=0x74f8dd)
		embed.set_thumbnail(url="https://i.ibb.co/ySfQhDG/reto.png")
		embed.add_field(name="Your data is secure", value="This update brings with it one of the most overdue features, and a central focus of it: your data with Reto has graduated from JSON school to RETO uni, and is now fully encrypted! Not even the developers can snoop around and check on your comments, profile info, and the like.", inline=False)
		embed.add_field(name="Your data is ephimerous", value="Following the new Discord bot guidelines, all of your comment data will be stored for 30 days tops - and at that point, it will be unceremoniously deleted from our databases. As a side-effect, Global Post Leaderboards will be a bit spicier... and a bit more competitive!", inline=False)
		embed.add_field(name="Your data is yours", value=prefix + "privacy has gotten a full-on makeover, now featuring a swiss-army knife of tools to make sure you're aware, and can limit, what info Reto knows about you! In addition to the former Privacy Mode (Reto won't store your personal comments), you can now disable server-wide logging (server's comments won't appear on Global Leaderboards), enable Permanent Storage (circumvents the new 30-day storage), and delete your entire Reto data to start anew (or quit).", inline=False)
		embed.add_field(name="Un-react to Un-heart", value="For the first time in forever, Reactions have gotten a bit more love. Have you ever hearted a post, then immediately regretted it? Now you can take it all back by... just removing the reaction, and putting an appropriate Minus emoji on its place. This also works for Stars, but starring something, then un-Starring it, then Starring it again *will* put it twice on the Best Of channel again.", inline=False)
		embed.add_field(name="Souped-up Best Of Messages", value="Ever wanted to star a post including an embed (like a tweet, or YouTube video), but the final embed on the channel came out blank? Say no more - now we save that embed, re-format it a bit, and display some of its info on both the Best Of channel and post leaderboards.", inline=False)
		embed.add_field(name="Reaction Cooldown, Begone", value="Wanted to react to a post after a good while, but the bot wouldn't even flinch because the message was \"too old\"? Well, we migrated to a new system that now allows you to react to posts made waaaaay back! Try it out - star a comment from 2019, see what happens!", inline=False)
		embed.add_field(name="Autovotes!", value="When Reto started, it boasted itself as \"Reddit's Karma system, for Discord.\" This was a weird comparison, seeing how Reddit would have each comment marked with upvotes and downvotes, while you had to manually add them in on Reto. Well, enabling " + prefix + "autovote server or channel wide, now you can emulate that! This dandy little feature will make Reto auto-react to every message sent with a Plus and a Minus, to encourage voting. Perfect for meme channels.", inline=False)
		embed.add_field(name="Updated Reaction Emoji", value="Originally, the Star and Heart emojis would look SUSPICIOUSLY similar to the ⭐ and ❤️ default emotes, with just different shades to differentiate them. This means a _high_ amount of people would add the standard heart emoji to a post expecting to react to it, and nothing would happen. Now the emoji look like this: " + str(defaultStar) + " | " + str(defaultPlus) + " | " + str(defaultMinus) + ", to differentiate them better! If you already have a server using the old emoji and want these ones, run " + prefix + "emoji default!", inline=False)
		embed.add_field(name="And more stuff under the hood...", value="That's not all, of course! We've also spruced things up on the backend, cleaned things that were irrelevant years ago, and made QOL changes (for example, bot errors look way nicer, and if you have a custom " + prefix + "prefix, now the messages Reto sends will show it instead of the default \"?\").", inline=False)
		embed.add_field(name="A note for Bot Owners", value="The migration to an encrypted filesystem is MANUAL. If you update to 1.6 or higher, you might get a warning message asking you to run a piece of code to encrypt your database - make sure to do so if you'd like to update!", inline=True)
		await ctx.send(embed=embed)

	@commands.command(description='Sends an invite link for the bot to invite it to other servers.')
	async def invite(self, ctx):
		"""Invite the bot to your server!"""
		await ctx.send("Here's an invitation link for the bot: https://discordapp.com/api/oauth2/authorize?client_id=" + str(self.client.user.id) + "&permissions=1342449744&scope=bot")

	@commands.command(description='This command just throws a generic error from the error handler.')
	async def error(self, ctx):
		"""Throws... an error. For testing purposes."""
		await sendErrorEmbed(ctx.message.channel,"I'm not sure why you're here, truth to be told! Nothing has necessarily gone wrong, you just decided to throw an error, for some reason. Er, good job?")

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
				textSwitch = "(Enabled - disable it with " + prefix + "privacy mode off)"
			else:
				emojiSwitch = "\\❌"
				textSwitch = "(Disabled - enable it with " + prefix + "privacy mode on)"
			embed.add_field(name=emojiSwitch + " Privacy Mode", value="Let Reto know you don't want your (reacted to) comments logged. When enabled, this will make it so you don't show up on Post Leaderboards and Global Post Leaderboards. " + textSwitch, inline=False)
			
			if privSettings and "storage" in privSettings and privSettings['storage'] == True:
				emojiSwitch = "\\✔️"
				textSwitch = "(Enabled - disable it with " + prefix + "privacy storage off)"
			else:
				emojiSwitch = "\\❌"
				textSwitch = "(Disabled - enable it with " + prefix + "privacy storage on)"
			embed.add_field(name=emojiSwitch + " Permanent Storage", value="Reto deletes your comment information 30 days after it's first saved, per Discord policies. If you'd like to have your comments be stored indefinitely, enable this option. " + textSwitch, inline=False)

			if not isinstance(ctx.message.channel, discord.channel.DMChannel):
				srvSettings = srv.search(Query().serverid == ctx.message.guild.id)[0]
				if "global" in srvSettings and srvSettings['global'] == True or not "global" in srvSettings:
					emojiSwitch = "\\✔️"
					textSwitch = "(Enabled - Curators can disable it with " + prefix + "privacy server off)"
				else:
					emojiSwitch = "\\❌"
					textSwitch = "(Disabled - Curators can enable it with " + prefix + "privacy server on)"
				embed.add_field(name=emojiSwitch + " Server Logging", value="Setting this as disabled means the server won't show up on Global Post Leaderboards, perfect for private or confidential conversations. " + textSwitch, inline=False)
			embed.add_field(name="\\💣 Destroy your user data", value="Ready to leave Reto, and want to leave your previous conversations, points and the like behind? Do note that this action is destructive, and will only affect you and not that of the server at large. If so, use " + prefix + "privacy data delete.", inline=True)
			await ctx.send(embed=embed)
		elif args[0] == "mode":
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