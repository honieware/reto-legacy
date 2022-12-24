# Import global variables and databases.
from definitions import botname, botowner, activity, post, priv, db, ephemeral, best

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
from datetime import datetime

# sharedFunctions
from sharedFunctions import printLeaderboard, createLeaderboardEmbed, getProfile, sendErrorEmbed, getCurrentPrefix

# ----------------------------------------------------------------------------------------------

class Management(commands.Cog):
	"""
	Commands that have to do with the bot's upkeep. Not relevant to normal users.
	"""

	isDeletingComments = False
	isFirstTime = True

	def __init__(self, client):
		self.client = client
		# Global variable related to periodical comment deletion.
		self.commentDeleter.start()

	def cog_unload(self):
		self.commentDeleter.cancel()
	
	#-------------------------
	#   MANAGEMENT COMMANDS
	#-------------------------
	@commands.command()
	async def activity(self,ctx,*args):
		"""[BOT ADMIN ONLY] Change the bot's activity."""

		prefix = await getCurrentPrefix(ctx)
		isOwner = False
		for x in botowner:
			if (int(ctx.message.author.id) == int(x)):
				isOwner = True

		if isOwner:
			if not args:
				embed = await showActivityList(ctx)
				glb = await ctx.send(embed=embed)
			if args[0] == "create":
				if len(args) == 1:
					await sendErrorEmbed(ctx, "Please introduce the text of the activity to be created.")
				else:
					activity.insert({'activity': args[1]})
					await ctx.send('The activity "' + args[1] + '" has been added to the list!')
			elif args[0] == "delete":
				if len(args) == 1:
					await sendErrorEmbed(ctx, "Please introduce the ID of the activity to be deleted. _You can check it doing " + prefix + "activity_.")
				else:
					# if len of activity equals 1 then dont let it remove
					try:
						toDelete = [int(args[1])]
						activity.remove(doc_ids=toDelete)
					except:
						await sendErrorEmbed(ctx, "The activity with the ID " + args[1] + " couldn't be deleted. (Double check if it exists?)")
					else:
						await ctx.send('The activity with the ID ' + args[1] + ' has been deleted.')
			else:
				embed = await showActivityList(ctx)
				glb = await ctx.send(embed=embed)
		else:
			await sendErrorEmbed(ctx, "Looks like you don't have permission to do this?\n_Are you hosting " + botname + "? If so make sure your User ID is on the **botowner** array on the config.json file!_")
	
	#-------------------------
	#   BROADCAST
	#-------------------------
	@commands.command()
	async def broadcast(self,ctx,*args):
		"""[BOT ADMIN ONLY] Send a message to every server's BEST OF CHANNEL. Only use for special, or breaking updates."""
		if len(args) < 2 or len(args) > 3:
			await sendErrorEmbed(ctx, "Wrong syntax!\n> **First argument:** The title of the broadcasted message.\n> **Second argument:** The broadcasted message's description.\n> **Third argument** (optional): Link to an image, or Null.")
			return

		for server in self.client.guilds:
			bestOf = best.get(Query().serverid == str(server.id))
			if not bestOf:
				continue
			for channel in server.channels:
				if channel.id == bestOf["channelid"]:
					try:
						broadcastEmbed = discord.Embed(title=args[0], description=args[1], color=0x6db3f0)
						if len(args) == 3:
							broadcastEmbed.set_image(url=args[2])
						broadcastEmbed.set_footer(text="Broadcast sent by the Reto developer team.")
						await channel.send(embed=broadcastEmbed)
					except Exception:
						continue
					else:
						break

	#-----------------
	#   EDIT KARMA
	#-----------------
	@commands.command(aliases=['editkarma', 'karmaedit', 'motherlode'])
	async def rosebud(self,ctx,*args):
		"""[BOT ADMIN ONLY] Add or subtract karma from an user."""

		prefix = await getCurrentPrefix(ctx)
		isOwner = False
		for x in botowner:
			if (int(ctx.message.author.id) == int(x)):
				isOwner = True

		if isOwner:
			if not args:
				await sendErrorEmbed(ctx, "Hey! You should probably tag someone first.\nIntended usage: " + prefix + "rosebud `[user]` `[amount of karma]` `[set/add/subtract]`")
				return
			if not ctx.message.mentions:
				await sendErrorEmbed(ctx, "You forgot to add in an user!")
				return
			else:
				user = ctx.message.mentions[0]
				if len(args) < 2:
					await sendErrorEmbed(ctx, "You haven't entered a karma amount!")
					return
				if args[1].isdigit():
					karma = int(args[1])
					value = ""
					if len(args) < 3:
						await sendErrorEmbed(ctx, "You have to enter an argument! `[set/add/subtract]`")
						return	
					# this is a stupid way to write it
					if args[2] == "add":
						value = "add"
					elif args[2] == "subtract":
						value = "subtract"
					elif args[2] == "set":
						value = "set"
					else:
						await sendErrorEmbed(ctx, "That's not a valid argument! `[set/add/subtract]`")
						return
					if args[2] and value:
						# DO THE THING
						exists = db.count(Query().username == str(user.id))
						server = str(ctx.message.guild.id)
						if exists == 0:
							if value == "add" or value == "set":
								db.insert({'username': str(user.id), 'points': karma, 'servers': [server], 'modifiedkarma': True})
							elif value == "subtract":
								db.insert({'username': str(user.id), 'points': -karma, 'servers': [server], 'modifiedkarma': True})
						else:
							if value == "add":
								db.update(add('points',karma), where('username') == str(user.id))
							elif value == "subtract":
								db.update(subtract('points',karma), where('username') == str(user.id))
							elif value == "set":
								db.update({'points': karma}, where('username') == str(user.id))
							db.update({'modifiedkarma': True}, where('username') == str(user.id))
						result = db.get(Query()['username'] == str(user.id))
						
						await ctx.send('Great! ' + user.name + "'s new karma total is " + str(result.get('points')) + ".")
						
				else:
					await sendErrorEmbed(ctx, "That's not a valid amount of karma!")
					return
		else:
			await sendErrorEmbed(ctx, "Looks like you don't have permission to do this?\n_Are you hosting " + botname + "? If so make sure your User ID is on the **botowner** array on the config.json file!_")	

	#-------------------------
	#      POST DELETER
	#-------------------------
	@tasks.loop(hours=12)
	async def commentDeleter(self):
		if self.isFirstTime:
			self.isFirstTime = False
			return
		if not ephemeral:
			return
		if self.isDeletingComments == False and self.isFirstTime == False and ephemeral:
			print("⚠️ Running the COMMENT DELETER...\nThis checks every 12 hours for saved comments that are 30 days old and deletes them from the comments.reto file,\nper Discord's verification rules. Do not stop " + botname + " while this is running!")
			self.isDeletingComments = True # Don't run it twice at the same time!
			i = 0
			totalDeleted = 0
			evalPosts = post.all()
			postLength = len(evalPosts)
			for postelement in evalPosts:
				i = i + 1
				print("Scanning the comments... (" + str(i) + "/" + str(postLength) + ")", end="\r")
				if not "timestamp" in postelement:
					post.update({"timestamp": str(datetime.now())}, where('msgid') == postelement['msgid'])
					postelement['timestamp'] = str(datetime.now())
				parsedTimestamp = datetime.strptime(postelement['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
				delta = datetime.now() - parsedTimestamp

				# permastorage
				privSettings = priv.search(Query().username == int(postelement['username']))
				if privSettings:
					privSettings = privSettings[0]
				if not privSettings or "storage" in privSettings and privSettings['storage'] == False or not "storage" in privSettings:
					if delta.days >= 30:
						totalDeleted = totalDeleted + 1
						post.remove(where('msgid') == postelement['msgid'])
			print("\nAll set! " + str(totalDeleted) + " comments were deleted.\n")
			self.isDeletingComments = False

async def showActivityList(ctx):

	prefix = await getCurrentPrefix(ctx)
	activity.clear_cache()
	result = activity.all()
	s = ""

	try:
		if result:
			for value in result: 
				s += ("ID: " + str(value.doc_id) + " - " + value["activity"] + "\n")
		embed = discord.Embed(title="List of Activities", colour=discord.Colour(0xa353a9), description=s)
		embed.set_footer(text="Add more with " + prefix + "activity create '[text]', or remove one with " + prefix + "activity delete [id].")
		return embed
	except Exception as e:
		await sendErrorEmbed(ctx, "Can't show the activity list! (Too many activities?)")
			
def setup(client):
	client.add_cog(Management(client))