# Import global variables and databases.
from definitions import debug, db, post, priv, best, dm, chan, customprefix

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
from sharedFunctions import printLeaderboard, createLeaderboardEmbed, getProfile, sendErrorEmbed

# ----------------------------------------------------------------------------------------------

class Reaction(commands.Cog):
	"""
	Code for the bot's Reaction feature - assigning posts and all.
	"""
	def __init__(self, client):
		self.client = client
	
	# Looking for React/Unreact code?
	# Starting from 1.6, you can find this at sharedFunctions.py and reto.py!
	# The change to raw reaction checks means it needs to not be in its own cog.

	# -------------------------------
	#		   USER REACTS
	# -------------------------------
		
	@commands.Cog.listener()
	async def on_reaction_add(self, reaction, user):
		value = user.id
		User  = Query()
		if ((user.id != reaction.message.author.id) or (debug == True)) and not user.bot:
			if isinstance(reaction.emoji, str):

				# -------------------------
				#  REACTION = :WASTEBASKET:
				#       (leaderboards)
				# -------------------------	
				if reaction.emoji == '🗑️':
					await deleteMessages(reaction)

				# -------------------------
				#  REACTION = :ARROW_RIGHT:
				#       (leaderboards)
				# -------------------------	
				if reaction.emoji == '➡️':
					result = dm.get(Query()['id'] == reaction.message.id)
					page = result.get('page') + 1
					currentguild = str(reaction.message.guild.id)
					isGlobal = result.get('global')
					if (isGlobal == True):
						result = post.all()
					else:
						result = post.search(Query()['servers'] == currentguild)
					leaderboard = {} # Prepares an empty dictionary.
					j = 0
					for x in result: # For each entry in the database:
						leaderboard[j] = [int(x.get("points")), str(x.get("content")), str(x.get("username")), str(x.get("embed")), str(x.get("servers")), str(x.get("stars")), str(x.get("nsfw")), str(x.get("richembed"))] # ...save the user's ID and its amount of points in a new Python database.
						j = j+1
					
					leaderboard = sorted(leaderboard.items(), key = lambda x : x[1][0], reverse=True)

					await printLeaderboard(page, leaderboard, self, reaction.message.guild, reaction.message, reaction.message.channel, False, isGlobal)

					await deleteMessages(reaction)

				# -------------------------
				#  REACTION = :ARROW_LEFT:
				#       (leaderboards)
				# -------------------------	
				if reaction.emoji == '⬅️':

					result = dm.get(Query()['id'] == reaction.message.id)
					page = result.get('page') - 1
					currentguild = str(reaction.message.guild.id)
					isGlobal = result.get('global')
					if (isGlobal == True):
						result = post.all()
					else:
						result = post.search(Query()['servers'] == currentguild)
					leaderboard = {} # Prepares an empty dictionary.
					j = 0
					for x in result: # For each entry in the database:
						leaderboard[j] = [int(x.get("points")), str(x.get("content")), str(x.get("username")), str(x.get("embed")), str(x.get("servers")), str(x.get("stars")), str(x.get("nsfw")), str(x.get("richembed"))] # ...save the user's ID and its amount of points in a new Python database.
						j = j+1
					
					leaderboard = sorted(leaderboard.items(), key = lambda x : x[1][0], reverse=True)

					await printLeaderboard(page, leaderboard, self, reaction.message.guild, reaction.message, reaction.message.channel, False, isGlobal)

					await deleteMessages(reaction)

				# -------------------------
				#     REACTION = :BOMB:
				#     (Delete User Data)
				# -------------------------	
				if reaction.emoji == "💣":
					if isinstance(reaction.message.channel, discord.channel.DMChannel):
						if (reaction.message.embeds[0].title == "Are you SURE?!"):
							checkM = loadingEmoji = self.client.get_emoji(660250625107296256)
							react = await reaction.message.add_reaction(checkM)
							priv.remove(where('username') == user.id)
							priv.clear_cache()
							post.remove(where('username') == str(user.id))
							post.clear_cache()
							db.remove(where('username')   == str(user.id))
							db.clear_cache()

							botid = self.client.user
							await reaction.message.remove_reaction(checkM, botid)
							await reaction.message.channel.send("**Done.** Your Privacy Settings, all of your Comments and your personal data (such as servers and Karma) has been deleted.\nDo note that, by interacting with Reto functions, you may be re-introduced into the database.\n*Thank you for using Reto!*")

	# -------------------------------
	#         AUTOVOTE LOGIC
	# -------------------------------
	@commands.Cog.listener()
	async def on_message(ctx, message):
		if not message.author.bot and not isinstance(message.channel, discord.channel.DMChannel):
			pre = customprefix.search(Query().server == message.guild.id)
			if pre and not message.content.startswith(pre[0]['prefix']) or not pre and not message.content.startswith('?') : # shouldn't invoke commands

				messageType = "text"
				# Get first attachment
				if(len(message.attachments) > 0):
					attachment = message.attachments[0].url
					# Determine type
					for e in ['jpg','jpeg','png','webp','gif']:
						if attachment[-len(e)-1:]==f'.{e}':
							messageType = "images"
					for e in ['mp4', 'mov']:
						if attachment[-len(e)-1:]==f'.{e}':
							messageType = "videos"
					if messageType == "text":
						messageType = "files"
				# Embeds take priority
				if (message.embeds):
					messageType = "embeds"

				channelConfig = chan.get(Query()['server'] == message.guild.id)
				if (channelConfig):
					if str(message.channel.id) + "-" + messageType in channelConfig and channelConfig[str(message.channel.id) + "-" + messageType] == True:
						plus = discord.utils.get(message.guild.emojis, name="plus")
						minus = discord.utils.get(message.guild.emojis, name="minus")
						await message.add_reaction(plus)
						await message.add_reaction(minus)



async def deleteMessages(reaction):
	channel = reaction.message.channel
	result = dm.get(Query()['id'] == reaction.message.id)
	messageIds = result.get('messages')
	for x in messageIds:
		msg = await channel.fetch_message(x)
		await msg.delete()

def setup(client):
	client.add_cog(Reaction(client))
