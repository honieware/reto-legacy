# Import global variables and databases.
from definitions import srv, best, customprefix, chan, botname, support

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
from sharedFunctions import sendErrorEmbed, getCurrentPrefix, formatMessage, getLocalKarma, createAutovoteEmbed

# ----------------------------------------------------------------------------------------------

class Configuration(commands.Cog):
	"""
	Things that have to do with setting up and personalizing the bot.
	"""
	def __init__(self, client):
		self.client = client
	
	# ---------------------
	#	  SET UP BOT
	# ---------------------
	
	@commands.command(name="setup", pass_context=True, description="Sets up the bot, creating the necessary roles, channels and emojis for it to function. REQUIRED ROLES: Manage messages")
	@commands.has_permissions(manage_guild=True)
	async def setup(self, ctx):
		"""Sets up the bot automagically. REQUIRED ROLES: Manage messages"""
		loadingEmoji = self.client.get_emoji(660250625107296256)
		loadingText = await ctx.send(str(loadingEmoji) + " Getting " + botname + " ready to go...")
		error = False
		creationLog = ""
		prefix = await getCurrentPrefix(ctx)

		# Register server in database!
		# This should be unnecessary unless it's a VERY specific, debug-y case.
		srv.upsert({'serverid': ctx.guild.id, 'heart': 'plus', 'crush': 'minus', 'star': '10', 'global': True}, Query().serverid == ctx.guild.id)
		
		# If the role "Curator" doesn't exist, the bot creates it.
		try:
			rolesearch = discord.utils.get(ctx.guild.roles, name="Curator")
			if rolesearch == None:
				await ctx.guild.create_role(name="Curator")
				creationLog += "\n- The Curator role (users with this role can use the Star emoji) was created."
		except Exception as e:
			print(e)
			error = True
			errorLog = "Something happened while creating the role *Curator*. Maybe the bot doesn't have sufficient permissions?"
		
		# If the channel "#best-of" doesn't exist, the bot creates it.
		try:
			server = str(ctx.message.guild.id)
			bestsearch = best.get(Query().serverid == server)
			if bestsearch:
				existingBestOfChannel = discord.utils.get(ctx.message.guild.channels, id=bestsearch["channelid"])
			if not bestsearch or not existingBestOfChannel:
				bestOfChannel = await ctx.guild.create_text_channel('best-of')
				best.upsert({'serverid': server, 'channelid': bestOfChannel.id, 'notification': "message"}, Query().serverid == server)
				creationLog += "\n- The Best Of channel, where Starred comments lie, was created."
		except Exception as e:
			print(e)
			error = True
			errorLog = "There was an error while trying to create the Best Of channel. May have to do with permissions?"

		# If the user who executed the command doesn't have assigned the role "Curator", the bot assigns it.
		try:
			if discord.utils.get(ctx.message.author.roles, name="Curator") is None:
				role = discord.utils.get(ctx.guild.roles, name="Curator")
				await ctx.message.author.add_roles(role)
				creationLog += "\n- You were given the role Curator."
		except Exception as e:
			print(e)
			error = True
			errorLog = "While creating the role Curator, an error occurred. May have to do something with permissions."

		# If the emoji "10" doesn't exist, the bot creates it.
		try:
			rolesearch = discord.utils.get(ctx.guild.roles, name="Curator")
			emojisearch = discord.utils.get(ctx.guild.emojis, name="10")
			if emojisearch == None:
				with open("images/star.png", "rb") as image:
					await ctx.guild.create_custom_emoji(name="10", image=image.read(), roles=[rolesearch])
					creationLog += "\n- The emoji Star (+10) was created. Only Curators can use it to add content to the Best Of channel!"
		except Exception as e:
			print(e)
			error = True
			errorLog = "Trying to create the role-exclusive emoji Star (10) sent out an error. Maybe there's not enough space for new emoji, or the bot doesn't have permissions."

		# If the emoji "plus" doesn't exist, the bot creates it.
		try:
			plussearch = discord.utils.get(ctx.guild.emojis, name="plus")
			if plussearch == None:
				with open("images/plus.png", "rb") as image:
					await ctx.guild.create_custom_emoji(name="plus", image=image.read())
					creationLog += "\n The emoji Heart (+1) was created."
		except Exception as e:
			print(e)
			error = True
			errorLog = "Trying to create the emoji Heart (plus) sent out an error. Maybe there's not enough space for new emoji, or the bot doesn't have permissions."
		
		# If the emoji "minus" doesn't exist, the bot creates it.
		try:
			minussearch = discord.utils.get(ctx.guild.emojis, name="minus")
			if minussearch == None:
				with open("images/minus.png", "rb") as image:
					await ctx.guild.create_custom_emoji(name="minus", image=image.read())
					creationLog += "\n- The emoji Crush (-1) was created."
		except Exception as e:
			print(e)
			error = True
			errorLog = "Trying to create the emoji Crush (minus) sent out an error. Maybe there's not enough space for new emoji, or the bot doesn't have permissions."
		
		await loadingText.delete()
		emoji = discord.utils.get(ctx.message.guild.emojis, name="10")
		
		if error == False and creationLog != "":
			await ctx.send("**" + botname + "** is now set up and ready to go!\n\n*What changed?*")
			creationLog += "\n"
			if creationLog != "":
				await ctx.send(creationLog)
			await ctx.send("*What now?*\n- Giving someone the role *Curator* on Server Settings will let them use the " + str(emoji) + " emoji to star posts. A Discord restart (CTRL+R) may be needed to see the emoji.\n- Edit the look of the default emojis using the command " + prefix + "emoji to make " + botname + " your own!\n- Rename the #best-of channel to a name you like the most on Server Settings.\n- Use the command " + prefix + "notification if your server is big, and you'd rather change the confirm message (e.g. Congrats! +10 points to the user) to a reaction.")
			if support != "":
				await ctx.send("- If any issues arise, make sure to check in on " + botname + "'s official support server, over at **" + support + "**. :heart:")
			else:
				await ctx.send("- Thank you very much for installing **" + botname + "**! :heart:")
		elif error == True:
			await sendErrorEmbed(ctx, "Something happened and the setup couldn't be completed. (" + errorLog + ")\n- Check that there is space to create three new emojis and that the bot has sufficient permissions.\n- If you're certain everything was taken care of, try running the setup command again.")
		else:
			await ctx.send("**" + botname + "** was already set up - nothing has changed!\n\n*Want some pointers?*\n- Giving someone the role *Curator* on Server Settings will let them use the " + str(emoji) + " emoji to star posts. A Discord restart (CTRL+R) may be needed to see the emoji.\n- Edit the look of the default emojis using the command " + prefix + "emoji to make " + botname + " your own!\n- Rename the #best-of channel to a name you like the most on Server Settings.\n- Use the command " + prefix + "notification if your server is big, and you'd rather change the confirm message (e.g. Congrats! +10 points to the user) to a reaction.")
			if support != "":
				await ctx.send("- If any issues arise, make sure to check in on " + botname + "'s official support server, over at **" + support + "**. :heart:")
			else:
				await ctx.send("- Thank you very much for installing **" + botname + "**! :heart:")
			
			
	# -------------------------
	#		MANAGE EMOJIS
	# -------------------------
				
	@commands.command(aliases=['reto', 'config', 'cfg', 'emojis', 'settings'], description='Used by server admins to manage their emojis. ?emoji edit to change the look of a heart/crush/10 points, ?emoji default to restore all emojis. REQUIRED ROLES: Manage messages')
	@commands.has_permissions(manage_guild=True)
	async def emoji(self, ctx, *args):
		"""Used to manage bot emojis. REQUIRED ROLES: Manage messages"""
		script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
		rel_path = "../images/testimage.png"
		path = os.path.join(script_dir, rel_path)
		prefix = await getCurrentPrefix(ctx)
		if not args:
			await ctx.send("Please provide an argument!\n**" + prefix + "emoji edit** *name_of_emoji* - Lets you edit any of the three default emojis (10/plus/minus). Image required.\n**" + prefix + "emoji default** - Restores the custom emoji (10/plus/minus) to their original state.")
		elif args[0] == "edit":
			if len(args) != 2:
				await sendErrorEmbed(ctx, "No emoji name was provided. Valid emoji names: 10/plus/minus")
			elif args[1] == "10":
					if not ctx.message.attachments:
						await sendErrorEmbed(ctx, "Couldn't find an image! Upload an image or an URL along with your command.")
					else:
						async with aiohttp.ClientSession() as session:
							url = ctx.message.attachments[0].url
							print (url)
							async with session.get(url) as resp:
								if resp.status == 200:
									f = await aiofiles.open(path, mode='wb')
									await f.write(await resp.read())
									await f.close()
									rolesearch = discord.utils.get(ctx.guild.roles, name="Curator")
									with open("images/testimage.png", "rb") as image:
										if not (os.stat('images/testimage.png').st_size > 256000):
											emojisearch = discord.utils.get(ctx.guild.emojis, name="10")
											await emojisearch.delete()
											await ctx.guild.create_custom_emoji(name="10", image=image.read())
											await ctx.send("The emoji **:10:** has been modified.")
										else:
											await sendErrorEmbed(ctx, "Your image is too big! Discord emojis have to be 256kb in size or smaller.")
										
			elif args[1] == "plus":
					if not ctx.message.attachments:
						await sendErrorEmbed(ctx, "Couldn't find an image! Upload an image or an URL along with your command.")
					else:
						async with aiohttp.ClientSession() as session:
							url = ctx.message.attachments[0].url
							print (url)
							async with session.get(url) as resp:
								if resp.status == 200:
									f = await aiofiles.open(path, mode='wb')
									await f.write(await resp.read())
									await f.close()
									rolesearch = discord.utils.get(ctx.guild.roles, name="Curator")
									with open("images/testimage.png", "rb") as image:
										if not (os.stat('images/testimage.png').st_size > 256000):
											emojisearch = discord.utils.get(ctx.guild.emojis, name="plus")
											await emojisearch.delete()
											await ctx.guild.create_custom_emoji(name="plus", image=image.read())
											await ctx.send("The emoji **:plus:** has been modified.")
										else:
											await sendErrorEmbed(ctx, "Your image is too big! Discord emojis have to be 256kb in size or smaller.")
										
			elif args[1] == "minus":
					if not ctx.message.attachments:
						await sendErrorEmbed(ctx, "Couldn't find an image! Upload an image or an URL along with your command.")
					else:
						async with aiohttp.ClientSession() as session:
							url = ctx.message.attachments[0].url
							print (url)
							async with session.get(url) as resp:
								if resp.status == 200:
									f = await aiofiles.open(path, mode='wb')
									await f.write(await resp.read())
									await f.close()
									rolesearch = discord.utils.get(ctx.guild.roles, name="Curator")
									with open("images/testimage.png", "rb") as image:
										if not (os.stat('images/testimage.png').st_size > 256000):
											emojisearch = discord.utils.get(ctx.guild.emojis, name="minus")
											await emojisearch.delete()
											await ctx.guild.create_custom_emoji(name="minus", image=image.read())
											await ctx.send("The emoji **:minus:** has been modified.")
										else:
											await sendErrorEmbed(ctx, "Your image is too big! Discord emojis have to be 256kb in size or smaller.")
										
			else:
				await sendErrorEmbed(ctx, "Invalid emoji name. Valid names: 10/plus/minus")
		elif args[0] == "default":
			try:
				# Restore :10:
				rolesearch = discord.utils.get(ctx.guild.roles, name="Curator")
				emojisearch = discord.utils.get(ctx.guild.emojis, name="10")
				if emojisearch == None:
					with open("images/star.png", "rb") as image:
						await ctx.guild.create_custom_emoji(name="10", image=image.read(), roles=[rolesearch])
				else:
					await emojisearch.delete()
					with open("images/star.png", "rb") as image:
						await ctx.guild.create_custom_emoji(name="10", image=image.read(), roles=[rolesearch])
				# Restore :plus:
				emojisearch = discord.utils.get(ctx.guild.emojis, name="plus")
				if emojisearch == None:
					with open("images/plus.png", "rb") as image:
						await ctx.guild.create_custom_emoji(name="plus", image=image.read())
				else:
					await emojisearch.delete()
					with open("images/plus.png", "rb") as image:
						await ctx.guild.create_custom_emoji(name="plus", image=image.read())
				# Restore :minus:
				emojisearch = discord.utils.get(ctx.guild.emojis, name="minus")
				if emojisearch == None:
					with open("images/minus.png", "rb") as image:
						await ctx.guild.create_custom_emoji(name="minus", image=image.read())
				else:
					await emojisearch.delete()
					with open("images/minus.png", "rb") as image:
						await ctx.guild.create_custom_emoji(name="minus", image=image.read())
				await ctx.send("All emojis have been restored!")
			except:
				await sendErrorEmbed(ctx, "An error has occurred while restoring the emojis. Check the bot's permissions and that there's space for three more emojis and try again!")
		else:
			await ctx.send("Invalid argument!\n**" + prefix + "emoji edit** *name_of_emoji* - Lets you edit any of the three default emojis (10/plus/minus). Image required.\n**" + prefix + "emoji default** - Restores the custom emoji (10/plus/minus) to their original state.")

	# -------------------------
	#	SET UP NAME MODIFYING
	# -------------------------
				
	@commands.command(description="Let's get you set up and ready to change #best-of's name with this command!")
	@commands.has_permissions(manage_guild=True)
	async def name(self,ctx,*args):
		"""Get the ability to change #best-of's name!"""
		y2k = await ctx.send(":arrows_counterclockwise: Looking up if you're set up already...")
		best.clear_cache()
		server = str(ctx.message.guild.id)
		channel = best.search(Query().serverid == server)
		if (channel):
			await ctx.send(":white_check_mark: **You're already set up!**")
			await ctx.send("If you want to change the name of the #best-of channel, you can edit it on the Discord settings as usual!")
			await y2k.delete()
		else:
			channelid = discord.utils.get(self.client.get_all_channels(), name='best-of')
			best.upsert({'serverid': server, 'channelid': channelid.id, 'notification': "message"}, Query().serverid == server)
			await ctx.send(":raised_hands: **You weren't set up**, so I did it for you.")
			await ctx.send("If you want to change the name of the #best-of channel, you can edit it on the Discord settings as usual!")
			await y2k.delete()

	# -------------------------
	#	  CHANGE BOT PREFIX
	# -------------------------
				
	@commands.command(description="Change the bot's prefix to whichever you want. You can also use ?prefix default to get everything back to normal.")
	@commands.has_permissions(manage_guild=True)
	async def prefix(self,ctx,*args):
		"""Change the bot's prefix to whichever you want."""

		prefix = await getCurrentPrefix(ctx)
		if args:
			if args[0] == "default":
				pre = customprefix.get(Query().server == ctx.message.guild.id)
				customprefix.remove(doc_ids=[int(pre.doc_id)])
				await ctx.send("Your prefix is back to normal! You can now use `?` on " + botname + "'s commands.")
			else:
				customprefix.upsert({'server': ctx.message.guild.id, 'prefix': args[0]}, Query().server == ctx.message.guild.id)
				await ctx.send("Your prefix is now `" + args[0] + "`! You can now use it as a prefix to " + botname + "'s commands.")
		else:		 
			await ctx.send("Set up your prefix by writing in `" + prefix + "prefix *symbol*`. If you've messed up, you can restore it to default by writing `" + prefix + "prefix default`.\n_(Bot prompts will accomodate to this new prefix, except for the command descriptions on " + prefix + "help.)._")

	# -------------------------
	#	 CHANGE LOCAL KARMA
	# -------------------------

	@commands.command(description="Change the name and emoji of your Server's Karma with ?localkarma \"*name*\" *emoji*, or go back to safety with ?localkarma default.")
	@commands.has_permissions(manage_guild=True)
	async def localkarma(self,ctx,*args):
		"""Edit the name and emoji of your Local Karma!"""

		prefix = await getCurrentPrefix(ctx)
		if args:
			if args[0] == "default":
				srv.upsert({'server': ctx.message.guild.id, 'karmaname': False, 'karmaemoji': False}, Query().server == ctx.message.guild.id)
				await ctx.send("Your Local Karma has been restored to its default state.")
			else:
				if len(args) == 2:
					srv.upsert({'server': ctx.message.guild.id, 'karmaname': args[0], 'karmaemoji': args[1]}, Query().server == ctx.message.guild.id)
					await ctx.send("Your Local Karma has been updated!\n**Name:** " + args[0] + "\n**Emoji:** " + args[1])
				else:
					await sendErrorEmbed(ctx, "You forgot to set an emoji as the second argument!")
		else:
			karmaName = await getLocalKarma("name", ctx.message)
			karmaEmoji = await getLocalKarma("emoji", ctx.message)
			await ctx.send("Set up your Local Karma by writing in `" + prefix + "localkarma *name* *emoji*`. If you've messed up, you can restore it to default by writing `" + prefix + "localkarma default`.\n_(Your current Karma settings are " + karmaEmoji + " **" + karmaName + "**)._")

	# -------------------------
	#	 ENABLE AUTO-VOTES
	# -------------------------
				
	@commands.command(aliases=['autovotes', 'autoreact', 'autoreacts', 'autoreactions'], description="Enable/disable the bot reacting to every message in a certain channel! This is useful for image channels, where you'd want to have every post already reacted to with a Heart and a Crush to encourage voting. (You can also enable this server-wide, with ?autovote server.)")
	@commands.has_permissions(manage_guild=True)
	async def autovote(self,ctx,*args):
		"""Enable/disable the bot reacting to every message in a channel!"""
		
		channelId = str(ctx.message.channel.id)
		
		# Check if the channel exists.
		possibleConfigs = [
			{
				"emoji": "📜",
				"name": "Text",
				"description": "Regular, text-only messages.",
				"database": "text"
			},
			{
				"emoji": "🖼️",
				"name": "Images",
				"description": "Images attached to regular messages.",
				"database": "images"
			},
			{
				"emoji": "🎥",
				"name": "Videos",
				"description": "Anything with them moving pictures!",
				"database": "videos"
			},
			{
				"emoji": "🗄️",
				"name": "Files",
				"description": "Attachments - .txt, .zip, etcetera.",
				"database": "files"
			},
			{
				"emoji": "📎",
				"name": "Embeds",
				"description": "Links, formatted bot messages...",
				"database": "embeds"
			}
		]

		channelConfig = chan.get(Query()['server'] == ctx.message.guild.id)
		autovoteEmbed = await createAutovoteEmbed(channelId, possibleConfigs, channelConfig)
		sentEmbed = await ctx.send(embed=autovoteEmbed)
		
		emojiArray = []
		for config in possibleConfigs:
			emojiArray.append(config["emoji"])
			await sentEmbed.add_reaction(emoji=config["emoji"])
		
		def check(reaction, user):
			return user == ctx.message.author and str(reaction.emoji) in emojiArray and reaction.message.channel == ctx.message.channel
		
		try:
			reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
		except asyncio.TimeoutError:
			await sentEmbed.clear_reactions()
		else:
			while True:
				try:
					for config in possibleConfigs:
						if config["emoji"] == reaction.emoji:
							if (channelConfig and channelId + "-" + config["database"] in channelConfig and channelConfig[channelId + "-" + config["database"]] == True):
								chan.update({channelId + "-" + config["database"]: False}, where('server') == ctx.message.guild.id)
							else:
								exists = chan.count(Query().server == ctx.message.guild.id)
								# If the channel doesn't exist.
								if (exists == 0):
									chan.insert({'server': ctx.message.guild.id})
								chan.update({channelId + "-" + config["database"]: True}, where('server') == ctx.message.guild.id)
					
					# Update the old embed
					channelConfig = chan.get(Query()['server'] == ctx.message.guild.id)
					autovoteEmbed = await createAutovoteEmbed(channelId, possibleConfigs, channelConfig)
					await sentEmbed.edit(embed=autovoteEmbed)

					# Remove emoji
					await reaction.remove(ctx.message.author)

					reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
				except asyncio.TimeoutError:
					await sentEmbed.clear_reactions()
					break

	# -------------------------
	#	CHANGE NOTIFICATIONS
	# -------------------------
				
	@commands.command(aliases=['notif', 'notifications'], description="Change the confirm notification settings (e.g. Congrats! X person gave you a star and now you're in the Best Of channel.) from Reactions to Messages. (?notification message/?notification reaction)")
	@commands.has_permissions(manage_guild=True)
	async def notification(self,ctx,*args):
		"""Change confirm notif. to messages or reactions."""

		prefix = await getCurrentPrefix(ctx)
		loadingEmoji = self.client.get_emoji(660250625107296256)
		okayEmoji = self.client.get_emoji(660217963911184384)
		server = str(ctx.message.guild.id)
		best.clear_cache()
		server = str(ctx.message.guild.id)
		channel = best.search(Query().serverid == server)
		if not channel:
			channelid = discord.utils.get(self.client.get_all_channels(), name='best-of')
			best.upsert({'serverid': server, 'channelid': channelid.id, 'notification': "message"}, Query().serverid == server)
		notifmode = best.search(Query().serverid == server)
		notifmode = notifmode[0]['notification']
		notifstr = str(notifmode)
		print(best.search(Query().serverid == server))
		if not args:
			await ctx.send("You're currently using **" + notifstr.capitalize() + "** Mode.\n💠 *" + prefix + "notification message* tells " + botname + " to send a message when someone Stars/Hearts/Crushes a comment. Great for small servers, and shows the Karma that the user currently has.\n💠 *" + prefix + "notification reaction* sends a reaction when someone Stars/Hearts/Crushes a comment. Great if you don't want to have excess notifications on Mobile, but it doesn't show the Karma the user has.\n💠 *" + prefix + "notification disabled* deactivates notifications on this server - no messages or reactions when someone Stars/Hearts/Crushes a comment. This isn't recommended unless it's being used in a very heavy server, as it leaves zero feedback that their vote has been counted.")
		elif args[0] == "reaction" or args[0] == "reactions":
			best.update({"notification": "reaction"}, where('serverid') == server)
			await ctx.send("*Got it!* The server will send confirmations as a reaction.\nNext time someone reacts to a comment, said message will be reacted with " + str(okayEmoji) + " for a couple of seconds.")
		elif args[0] == "message" or args[0] == "messages":
			best.update({"notification": "message"}, where('serverid') == server)
			await ctx.send("*Got it!* The server will send confirmations as messages.\nNext time someone reacts to a comment, they'll be sent a message as confirmation (which will delete itself after a couple of seconds).")
		elif args[0] == "disabled":
			best.update({"notification": "disabled"}, where('serverid') == server)
			await ctx.send("*Got it!* The server will not send confirmations.\nNext time someone reacts to a comment, it will be counted, but there'll be no confirmation of it.")
		else:
			await sendErrorEmbed(ctx, "That's not a valid option!")
		# best.clear_cache()
		print(best.search(Query().serverid == server))
		
	# -------------------------
	#	REATTACH BEST-OF
	# -------------------------
				
	@commands.command(description="If the #best-of channel stops working properly, you can reattach it with this command! Enter the channel as an argument.")
	@commands.has_permissions(manage_guild=True)
	async def reattach(self, ctx, channel: discord.TextChannel):
		"""Make a pre-existing channel into the Best Of!"""
		server = str(ctx.message.guild.id)
		best.upsert({'channelid': channel.id, 'serverid': server}, Query().serverid == server)
		await ctx.send("**Gotcha!** The new Best Of channel is now " + channel.mention + ".")

	# -------------------------
	#	CHANGE NOTIFICATION MESSAGES
	# -------------------------
				
	@commands.command(aliases=['nm'], description="Create your own custom notification messages! This requires `?notification` to be in Message Mode. Read more about the syntax using `?nm`.")
	@commands.has_permissions(manage_guild=True)
	async def notificationmessages(self, ctx, *args):
		"""Create your own custom notification messages."""
		errormessage = """
		\n**Argument 1:** Message type
		`[plus/minus/10/10repeat/default]`
		`10repeat` represents the message that appears when a message is starred multiple times.
		`default` will reset all of your set messages!
		\n**Argument 2:** Message
		`"string"`
		(Inbetween quotes.)
		\n**Message modifiers** (usable in Argument 2)
		`{u}`: Username
		`{um}`: Username (mentions/pings the user)
		`{c}`: Channel name
		`{cm}`: Channel name (links to the channel)
		`{b}`: Best Of name
		`{bm}`: Best Of name (links to the channel)
		`{m}`: Message
		`{s}`: Server name
		`{p}`: Points added or subtracted
		`{k}`: Total karma count (local)
		`{gk}`: Total karma count (global)
		`{kn}`: Local karma name
		`{ke}`: Local karma emoji
		`{e}`: Default karma emoji
		`{pe}`: Plus emoji
		`{me}`: Minus emoji
		`\\n`: Newline (pressing RETURN/ENTER)
		"""
		types = ["plus", "minus", "10", "10repeat"]
		server = str(ctx.message.guild.id)
		notifmode = best.get(Query().serverid == server)
		if "notification" in notifmode:
			notifmode = notifmode['notification']
		else:
			notifmode = "message"
		prefix = await getCurrentPrefix(ctx)

		if (notifmode != "message"):
			await sendErrorEmbed(ctx, "To set a custom notification message, the server should use Message Mode on notification settings!\nYou can change this with `" + prefix + "notification message`.")
		else:
			if not args:
				await sendErrorEmbed(ctx, "Enter the type of message you'd like to change!" + errormessage)
			elif any(item.lower() == args[0].lower() for item in types):
				if len(args) == 1:
					await sendErrorEmbed(ctx, "Hey, now - you have to enter the message you'd like to set, too!" + errormessage)
				elif len(args) == 3:
					await sendErrorEmbed(ctx, "The message should be inbetween quotes!" + errormessage)
				else:
					messageType = args[0]
					best.upsert({'serverid': server, messageType + "Message": args[1]}, Query().serverid == server)
					parsed = await formatMessage(args[1], ctx.message)
					await ctx.send("**You got it!** The new message for the `" + args[0] + "` trigger is " + parsed)
			elif args[0] == "default":
				bestof = best.get(Query().serverid == server)
				for t in types:
					if t + "Message" in bestof.keys():
						best.update(delete(t + "Message"), Query().serverid == server)
				await ctx.send("**You got it!** All messages are back to the default.")
			else:
				await sendErrorEmbed(ctx, "You haven't entered a valid message type!" + errormessage)

	
def setup(client):
	client.add_cog(Configuration(client))